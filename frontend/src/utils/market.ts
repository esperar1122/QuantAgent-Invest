// 市场参数规范化：统一为 QuantAgent-Invest 支持的 A股/指数
export const normalizeMarketForAnalysis = (market: any): string => {
  const raw = String(market ?? '').trim()
  const upper = raw.toUpperCase()
  if (['指数', 'INDEX'].includes(raw) || upper === 'INDEX') return '指数'
  return 'A股'
}

/**
 * 将交易所代码转换为市场类型
 */
export const exchangeCodeToMarket = (exchangeCode: string): string => {
  const code = String(exchangeCode ?? '').toLowerCase().trim()
  if (['index', 'zs'].includes(code)) return '指数'
  return 'A股'
}

/**
 * 根据股票/指数代码判断类型
 */
export const getMarketByStockCode = (stockCode: string): string => {
  const code = String(stockCode ?? '').trim()
  if (code.startsWith('39') || ['000001', '000300', '000905', '000852', '000688', '000680'].includes(code)) {
    return '指数'
  }
  return 'A股'
}

export default {
  normalizeMarketForAnalysis,
  exchangeCodeToMarket,
  getMarketByStockCode
}

