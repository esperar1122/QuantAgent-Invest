import { ApiClient } from './request'

export interface QuoteResponse {
  symbol: string  // 主字段：6位股票代码
  code?: string   // 兼容字段（已废弃）
  full_symbol?: string  // 完整代码（如 000001.SZ）
  name?: string
  market?: string
  price?: number
  change_percent?: number
  amount?: number
  prev_close?: number
  turnover_rate?: number
  amplitude?: number  // 振幅（替代量比）
  trade_date?: string
  updated_at?: string
}

export interface FundamentalsResponse {
  symbol: string  // 主字段：6位股票代码
  code?: string   // 兼容字段（已废弃）
  full_symbol?: string  // 完整代码（如 000001.SZ）
  name?: string
  industry?: string
  market?: string
  sector?: string  // 板块
  pe?: number
  pb?: number
  ps?: number      // 🔥 新增：市销率
  pe_ttm?: number
  pb_mrq?: number
  ps_ttm?: number  // 🔥 新增：市销率（TTM）
  roe?: number
  debt_ratio?: number  // 🔥 新增：负债率
  total_mv?: number
  circ_mv?: number
  turnover_rate?: number
  volume_ratio?: number
  pe_is_realtime?: boolean  // PE是否为实时数据
  pe_source?: string        // PE数据来源
  pe_updated_at?: string    // PE更新时间
  updated_at?: string
}

export interface KlineBar {
  time: string
  open?: number
  high?: number
  low?: number
  close?: number
  volume?: number
  amount?: number
}

export interface KlineResponse {
  symbol: string  // 主字段：6位股票代码
  code?: string   // 兼容字段（已废弃）
  period: 'day'|'week'|'month'|'5m'|'15m'|'30m'|'60m'
  limit: number
  adj: 'none'|'qfq'|'hfq'
  source?: string
  items: KlineBar[]
}

export interface NewsItem {
  title: string
  source: string
  time: string
  url: string
  type: 'news' | 'announcement'
}

export interface NewsResponse {
  symbol: string  // 主字段：6位股票代码
  code?: string   // 兼容字段（已废弃）
  days: number
  limit: number
  include_announcements: boolean
  source?: string
  items: NewsItem[]
}

export const stocksApi = {
  /**
   * 获取股票行情
   * @param symbol 6位股票代码
   */
  async getQuote(symbol: string) {
    return ApiClient.get<QuoteResponse>(`/api/stocks/${symbol}/quote`)
  },

  /**
   * 获取股票基本面数据
   * @param symbol 6位股票代码
   */
  async getFundamentals(symbol: string) {
    return ApiClient.get<FundamentalsResponse>(`/api/stocks/${symbol}/fundamentals`)
  },

  /**
   * 获取K线数据
   * @param symbol 6位股票代码
   * @param period K线周期
   * @param limit 数据条数
   * @param adj 复权方式
   */
  async getKline(symbol: string, period: KlineResponse['period'] = 'day', limit = 120, adj: KlineResponse['adj'] = 'none') {
    return ApiClient.get<KlineResponse>(`/api/stocks/${symbol}/kline`, { period, limit, adj })
  },

  /**
   * 获取股票新闻
   * @param symbol 6位股票代码
   * @param days 天数
   * @param limit 数量限制
   * @param includeAnnouncements 是否包含公告
   */
  async getNews(symbol: string, days = 30, limit = 50, includeAnnouncements = true) {
    return ApiClient.get<NewsResponse>(`/api/stocks/${symbol}/news`, { days, limit, include_announcements: includeAnnouncements })
  },

  /**
   * 获取A股股票池列表及统计指标
   */
  async getPool(params?: StockPoolParams) {
    return ApiClient.get<StockPoolResponse>('/api/stocks/pool', params)
  },

  /**
   * 极速检索股票与指数（支持代码、名称、拼音匹配）
   * @param keyword 关键词
   * @param limit 数量限制
   */
  async search(keyword: string, limit = 15) {
    return ApiClient.get<StockSearchResponse>('/api/stocks/search', { keyword, limit })
  },

  /**
   * 获取股票全套技术指标及量化信号诊断
   * @param symbol 6位股票代码
   * @param period 周期: day/week/month
   * @param limit K线根数
   */
  async getIndicators(symbol: string, period = 'day', limit = 120) {
    return ApiClient.get<TechnicalIndicatorsResponse>(`/api/stocks/${symbol}/indicators`, { period, limit })
  }
}

export interface StockSearchItem {
  code: string
  symbol: string
  name: string
  market: string
  industry?: string
  close?: number
  pct_chg?: number
  amount?: number
  pe?: number
  pb?: number
  total_mv?: number
}

export interface StockSearchResponse {
  items: StockSearchItem[]
  total: number
}

export interface StockPoolItem {
  code: string
  symbol: string
  name: string
  market: string
  industry: string
  source: string
  close?: number | null
  pct_chg?: number | null
  amount?: number | null
  volume?: number | null
  turnover_rate?: number | null
  volume_ratio?: number | null
  pe?: number | null
  pb?: number | null
  ps?: number | null
  circ_mv?: number | null
  total_mv?: number | null
  roe?: number | null
  net_profit_growth?: number | null
  revenue_growth?: number | null
  gross_margin?: number | null
  is_index?: boolean
  trade_date?: string
  updated_at?: string
}

export interface StockPoolStats {
  total_stocks: number
  main_board_count: number
  chinext_count: number
  star_count: number
  bse_count: number
  index_count?: number
}

export interface StockPoolParams {
  keyword?: string
  market?: string
  source?: string
  min_pe?: number | null
  max_pe?: number | null
  min_pb?: number | null
  max_pb?: number | null
  min_ps?: number | null
  max_ps?: number | null
  min_close?: number | null
  max_close?: number | null
  min_pct_chg?: number | null
  max_pct_chg?: number | null
  volume_level?: string
  min_turnover_rate?: number | null
  max_turnover_rate?: number | null
  min_volume_ratio?: number | null
  max_volume_ratio?: number | null
  market_cap_range?: string
  min_market_cap?: number | null
  max_market_cap?: number | null
  min_roe?: number | null
  max_roe?: number | null
  min_net_profit_growth?: number | null
  max_net_profit_growth?: number | null
  min_revenue_growth?: number | null
  max_revenue_growth?: number | null
  min_gross_margin?: number | null
  max_gross_margin?: number | null
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: 'asc' | 'desc'
}

export interface StockPoolResponse {
  total: number
  page: number
  page_size: number
  items: StockPoolItem[]
  stats: StockPoolStats
}

export interface TechnicalIndicatorBar {
  time: string
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  volume?: number | null
  amount?: number | null
  ma5?: number | null
  ma10?: number | null
  ma20?: number | null
  ma60?: number | null
  dif?: number | null
  dea?: number | null
  macd_hist?: number | null
  rsi6?: number | null
  rsi12?: number | null
  rsi24?: number | null
  kdj_k?: number | null
  kdj_d?: number | null
  kdj_j?: number | null
  boll_upper?: number | null
  boll_mid?: number | null
  boll_lower?: number | null
  atr14?: number | null
  obv?: number | null
}

export interface TechnicalSnapshot {
  code: string
  name: string
  market: string
  trade_date: string
  close?: number | null
  overall: {
    rating: string
    score: number
    type: 'bullish' | 'bearish' | 'neutral'
    bullish_count: number
    bearish_count: number
    neutral_count: number
    signals: Array<{ indicator: string; signal: string; type: 'bullish' | 'bearish' | 'neutral' }>
  }
  macd: {
    dif: number
    dea: number
    macd_hist: number
    signal: string
    type: 'bullish' | 'bearish' | 'neutral'
    hist_trend: string
    is_golden_cross: boolean
    is_death_cross: boolean
  }
  rsi: {
    rsi6: number
    rsi12: number
    rsi24: number
    status: string
    type: 'bullish' | 'bearish' | 'neutral'
  }
  kdj: {
    k: number
    d: number
    j: number
    signal: string
    type: 'bullish' | 'bearish' | 'neutral'
    is_golden_cross: boolean
    is_death_cross: boolean
  }
  boll: {
    upper: number
    mid: number
    lower: number
    position_pct: number
    bandwidth: number
    signal: string
    type: 'bullish' | 'bearish' | 'neutral'
  }
  ma: {
    ma5: number
    ma10: number
    ma20: number
    ma60: number
    arrangement: string
    type: 'bullish' | 'bearish' | 'neutral'
  }
  atr?: {
    atr14?: number | null
    volatility_ratio?: number | null
  }
  obv?: {
    obv?: number | null
  }
}

export interface TechnicalIndicatorsResponse {
  code: string
  name: string
  market: string
  period: string
  snapshot: TechnicalSnapshot
  series: TechnicalIndicatorBar[]
}



