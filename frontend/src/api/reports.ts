import { ApiClient } from './request'

export interface ReportItem {
  id: string
  analysis_id: string
  title: string
  stock_code: string
  stock_name: string
  market_type: string
  model_info?: string
  type: string
  format: string
  status: string
  created_at: string
  analysis_date?: string
  analysts?: string[]
  research_depth?: number
  summary?: string
  file_size?: number
  source?: string
  task_id?: string
  recommendation?: string
  confidence_score?: number
  risk_level?: string
  key_points?: string[]
}

export interface ReportListResponse {
  reports: ReportItem[]
  total: number
  page: number
  page_size: number
}

export interface ReportDetailResponse {
  id: string
  analysis_id: string
  stock_symbol: string
  stock_name: string
  model_info?: string
  analysis_date?: string
  status: string
  created_at: string
  updated_at?: string
  analysts?: string[]
  research_depth?: number
  summary?: string
  reports?: Record<string, any>
  source?: string
  task_id?: string
  recommendation?: string
  confidence_score?: number
  risk_level?: string
  key_points?: string[]
  execution_time?: number
  tokens_used?: number
}

export const reportsApi = {
  /**
   * 获取分析报告列表
   */
  async getReportsList(params?: {
    page?: number
    page_size?: number
    search_keyword?: string
    market_filter?: string
    start_date?: string
    end_date?: string
    stock_code?: string
  }) {
    return ApiClient.get<ReportListResponse>('/api/reports/list', params)
  },

  /**
   * 获取单份报告详细信息
   */
  async getReportDetail(reportId: string) {
    return ApiClient.get<ReportDetailResponse>(`/api/reports/${reportId}/detail`)
  },

  /**
   * 获取特定模块内容 (macro / technical / fundamental / risk 等)
   */
  async getModuleContent(reportId: string, module: string) {
    return ApiClient.get<any>(`/api/reports/${reportId}/content/${module}`)
  }
}
