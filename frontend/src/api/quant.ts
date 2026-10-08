import { ApiClient } from './request'

// ===== 回测相关接口 =====
export interface BacktestStrategyInfo {
  id: string
  name: string
  description: string
  params_schema: Record<string, any>
}

export interface BacktestTradeLog {
  trade_id: string
  date: string
  symbol: string
  action: 'BUY' | 'SELL'
  price: number
  shares: number
  amount: number
  fee: number
  realized_pnl: number
  return_pct: number
  reason?: string
}

export interface BacktestDailyNAV {
  date: string
  cash: number
  holdings_value: number
  total_equity: number
  nav: number
  benchmark_nav?: number
  drawdown_pct: number
}

export interface BacktestMetrics {
  total_return: number
  cagr: number
  annualized_volatility: number
  max_drawdown: number
  max_drawdown_duration_days: number
  sharpe_ratio: number
  sortino_ratio: number
  calmar_ratio: number
  win_rate: number
  profit_factor: number
  total_trades: number
  profitable_trades: number
  losing_trades: number
  benchmark_total_return?: number
  alpha?: number
  beta?: number
}

export interface BacktestFrictionSummary {
  total_commission: number
  total_stamp_duty: number
  total_transfer_fee: number
  total_slippage_cost: number
  total_friction: number
  friction_ratio_pct: number
  commission_desc: string
  stamp_duty_desc: string
  slippage_model_desc: string
}

export interface BacktestRequest {
  symbol: string
  symbols?: string[]
  sizing_model?: string
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital?: number
  commission_rate?: number
  min_commission?: number
  stamp_duty_rate?: number
  transfer_fee_rate?: number
  slippage?: number
  slippage_type?: string
  position_ratio?: number
  strategy_params?: Record<string, any>
  benchmark?: string
}

export interface PortfolioAssetAttribution {
  symbol: string
  trades_count: number
  sell_count: number
  win_count: number
  loss_count: number
  win_rate_pct: number
  realized_pnl: number
  contribution_pct: number
  current_shares: number
  target_weight_pct: number
}

export interface BacktestResponse {
  symbol: string
  is_portfolio?: boolean
  symbols?: string[]
  sizing_model?: string
  asset_attribution?: Record<string, PortfolioAssetAttribution>
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital: number
  final_equity: number
  metrics: BacktestMetrics
  frictions?: BacktestFrictionSummary
  trades: BacktestTradeLog[]
  daily_nav: BacktestDailyNAV[]
  execution_time_seconds?: number
}

// ===== 仓位与组合相关接口 =====
export interface AtrCalculateRequest {
  symbol: string
  current_price: number
  account_equity: number
  risk_tolerance_pct?: number
  atr_multiplier?: number
  atr_period?: number
}

export interface AtrCalculateResponse {
  symbol: string
  current_price: number
  atr_value: number
  suggested_shares: number
  suggested_lots: number
  position_value: number
  capital_ratio_pct: number
  stop_loss_price: number
  max_loss_amount: number
  risk_tolerance_pct: number
}

export interface KellyCalculateRequest {
  win_rate: number
  payoff_ratio: number
  half_kelly?: boolean
}

export interface KellyCalculateResponse {
  win_rate: number
  payoff_ratio: number
  full_kelly_pct: number
  suggested_fraction_pct: number
  is_half_kelly: boolean
  warning?: string
}

// ===== 虚拟模拟盘相关接口 =====
export interface PaperHolding {
  symbol: string
  name: string
  shares: number
  available_shares: number
  cost_price: number
  current_price: number
  market_value: number
  floating_pnl: number
  floating_pnl_pct: number
}

export interface PaperAccount {
  account_id: string
  initial_capital: number
  cash: number
  frozen_cash: number
  holdings_value: number
  total_equity: number
  total_pnl: number
  total_return_pct: number
  today_pnl: number
  holdings: PaperHolding[]
  recent_trades: any[]
}

export interface PaperOrderRequest {
  symbol: string
  action: 'BUY' | 'SELL'
  shares: number
  price?: number
  reason?: string
}

export interface PaperOrderResponse {
  success: boolean
  message: string
  order: any
  account_summary: any
}

export const quantApi = {
  // 回测
  getStrategies() {
    return ApiClient.get<{ strategies: BacktestStrategyInfo[] }>('/api/backtest/strategies')
  },
  runBacktest(params: BacktestRequest) {
    return ApiClient.post<BacktestResponse>('/api/backtest/run', params)
  },

  // 仓位管理
  calculateAtr(params: AtrCalculateRequest) {
    return ApiClient.post<AtrCalculateResponse>('/api/portfolio/calculate-atr', params)
  },
  calculateKelly(params: KellyCalculateRequest) {
    return ApiClient.post<KellyCalculateResponse>('/api/portfolio/calculate-kelly', params)
  },

  // 虚拟模拟盘
  getPaperAccount(skipErrorHandler = false) {
    return ApiClient.get<PaperAccount>('/api/paper-trading/account', undefined, { skipErrorHandler })
  },
  submitPaperOrder(params: PaperOrderRequest) {
    return ApiClient.post<PaperOrderResponse>('/api/paper-trading/order', params)
  },
  testWechat(webhook_url?: string) {
    return ApiClient.post<{ success: boolean; message: string }>('/api/paper-trading/test-wechat', null, {
      params: webhook_url ? { webhook_url } : {}
    })
  },

  // 实时行情快照
  getRealtimeQuotes(symbols: string[]) {
    const syms = symbols.join(',')
    return ApiClient.get<any>(`/api/quotes/live/${syms}`)
  }
}
