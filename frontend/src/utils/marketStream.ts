/**
 * 全站实时行情 SSE 流式推送管理器 (Market Quotes SSE Stream Manager)
 * 支持四大核心宽基指数与自选股/个股高频行情秒级推流
 * 具备断线自动指数退避重连、连接保活及组件生命周期自动清理机制
 */

export interface IndexQuoteItem {
  code: string
  full_code?: string
  name: string
  price: number
  prev_close: number
  change: number
  changePercent: number
  change_percent?: number
  volume?: number
  amount?: number
  high?: number
  low?: number
  open?: number
  timestamp?: string
}

export interface IndicesStreamPayload {
  indices: IndexQuoteItem[]
  timestamp?: string
  updated_at?: string
}

export interface QuoteStreamItem {
  code: string
  symbol: string
  name: string
  price: number
  prev_close: number
  open: number
  high: number
  low: number
  change: number
  change_pct: number
  volume_hands: number
  amount_wan: number
  turnover_rate?: number
  pe_ttm?: number
  market_cap_yi?: number
  bid1_price?: number
  bid1_volume?: number
  ask1_price?: number
  ask1_volume?: number
  timestamp?: string
}

export interface StreamController {
  close: () => void
  isConnected: () => boolean
}

/**
 * 建立四大核心指数 (上证/深证/创业板/科创50) 的 SSE 实时行情流
 */
export function createIndicesStream(options: {
  onData: (payload: IndicesStreamPayload) => void
  onConnect?: () => void
  onError?: (err: any) => void
  interval?: number
}): StreamController {
  let eventSource: EventSource | null = null
  let isClosed = false
  let reconnectTimer: any = null
  let retryCount = 0

  const interval = options.interval || 2.5
  const url = `/api/quotes/indices/stream?interval=${interval}`

  function connect() {
    if (isClosed) return

    try {
      eventSource = new EventSource(url)

      eventSource.onopen = () => {
        retryCount = 0
        options.onConnect?.()
      }

      eventSource.addEventListener('indices_update', (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as IndicesStreamPayload
          if (data && Array.isArray(data.indices)) {
            // 防御性校验：校准涨跌幅，杜绝点数混淆
            data.indices.forEach((idx) => {
              if (idx.price && idx.prev_close && idx.prev_close > 0) {
                const diff = +(idx.price - idx.prev_close).toFixed(2)
                const pct = +((diff / idx.prev_close) * 100).toFixed(2)
                // 若出现异常离谱数值（大于 20%），用数学公式强行校准
                if (Math.abs(idx.changePercent) > 20 || (Math.abs(diff) > 0 && idx.changePercent === 0)) {
                  idx.changePercent = pct
                  idx.change_percent = pct
                }
                idx.change = diff
              }
            })
            options.onData(data)
          }
        } catch (e) {
          console.warn('[SSE-Indices] 解析行情数据异常:', e)
        }
      })

      eventSource.onerror = (err) => {
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
        options.onError?.(err)

        if (!isClosed) {
          // 指数退避重连：最快 2 秒，最慢 15 秒
          const delay = Math.min(15000, 2000 * Math.pow(1.5, retryCount))
          retryCount++
          clearTimeout(reconnectTimer)
          reconnectTimer = setTimeout(() => {
            connect()
          }, delay)
        }
      }
    } catch (e) {
      options.onError?.(e)
    }
  }

  connect()

  return {
    close() {
      isClosed = true
      clearTimeout(reconnectTimer)
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    },
    isConnected() {
      return eventSource !== null && eventSource.readyState === EventSource.OPEN
    }
  }
}

/**
 * 建立指定标的池的 SSE 实时行情流
 */
export function createQuotesStream(options: {
  symbols: string[]
  onData: (quotes: Record<string, QuoteStreamItem>) => void
  onConnect?: () => void
  onError?: (err: any) => void
}): StreamController {
  let eventSource: EventSource | null = null
  let isClosed = false
  let reconnectTimer: any = null
  let retryCount = 0

  if (!options.symbols || options.symbols.length === 0) {
    return {
      close: () => {},
      isConnected: () => false
    }
  }

  const symbolsParam = encodeURIComponent(options.symbols.join(','))
  const url = `/api/quotes/stream?symbols=${symbolsParam}`

  function connect() {
    if (isClosed) return

    try {
      eventSource = new EventSource(url)

      eventSource.onopen = () => {
        retryCount = 0
        options.onConnect?.()
      }

      eventSource.addEventListener('quote_update', (event: MessageEvent) => {
        try {
          const quotes = JSON.parse(event.data) as Record<string, QuoteStreamItem>
          if (quotes && typeof quotes === 'object') {
            options.onData(quotes)
          }
        } catch (e) {
          console.warn('[SSE-Quotes] 解析标的行情异常:', e)
        }
      })

      eventSource.onerror = (err) => {
        if (eventSource) {
          eventSource.close()
          eventSource = null
        }
        options.onError?.(err)

        if (!isClosed) {
          const delay = Math.min(15000, 2000 * Math.pow(1.5, retryCount))
          retryCount++
          clearTimeout(reconnectTimer)
          reconnectTimer = setTimeout(() => {
            connect()
          }, delay)
        }
      }
    } catch (e) {
      options.onError?.(e)
    }
  }

  connect()

  return {
    close() {
      isClosed = true
      clearTimeout(reconnectTimer)
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    },
    isConnected() {
      return eventSource !== null && eventSource.readyState === EventSource.OPEN
    }
  }
}
