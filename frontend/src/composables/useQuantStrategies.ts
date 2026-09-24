import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  stocksApi,
  type CustomQuantStrategy,
  type CustomQuantStrategyCreatePayload,
  type CustomQuantStrategyUpdatePayload,
  type StockPoolParams
} from '@/api/stocks'

const LOCAL_STORAGE_KEY = 'quant_custom_strategies_v1'

// 初始默认自建模板与系统经典策略种子（若本地和后端均为空时提供完整示例）
const DEFAULT_TEMPLATES: CustomQuantStrategy[] = [
  {
    id: 'preset_quant_candidate',
    name: '量化初筛候选池',
    description: '系统全链路基准量化池：合理估值(0<PE<=60)且流动性充沛(成交额>=8000万)，与市场总览同源联动',
    icon: '🎯',
    tag_type: 'primary',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: true,
    params: {
      preset: 'quant_candidate',
      min_pe: 0.01,
      max_pe: 60,
      min_amount: 80000000
    }
  },
  {
    id: 'preset_low_valuation',
    name: '低估值价值',
    description: '严格估值安全边际：市盈率 PE <= 20，市净率 PB <= 2.0',
    icon: '💎',
    tag_type: 'success',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      min_pe: 0.01,
      max_pe: 20,
      min_pb: 0.01,
      max_pb: 2
    }
  },
  {
    id: 'preset_buffett_roe',
    name: '巴菲特高ROE',
    description: '高资本回报率：净资产收益率 ROE >= 15%，市盈率 PE <= 30',
    icon: '👑',
    tag_type: 'warning',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      min_roe: 15,
      min_pe: 0.01,
      max_pe: 30
    }
  },
  {
    id: 'preset_growth',
    name: '业绩高成长',
    description: '高速双增白马：净利润增速 >= 30%，营收增速 >= 20%',
    icon: '🚀',
    tag_type: 'danger',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      min_net_profit_growth: 30,
      min_revenue_growth: 20
    }
  },
  {
    id: 'preset_breakout',
    name: '强势突破',
    description: '量价共振主升浪：日涨幅 >= 3%，换手率 >= 3%，高成交活跃度',
    icon: '⚡',
    tag_type: 'danger',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      min_pct_chg: 3,
      min_turnover_rate: 3,
      volume_level: 'high'
    }
  },
  {
    id: 'preset_active_turnover',
    name: '高换手活跃',
    description: '高流动性博弈：换手率 >= 5%，量比 >= 1.5，上涨趋势',
    icon: '🔥',
    tag_type: 'danger',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      min_turnover_rate: 5,
      min_volume_ratio: 1.5,
      min_pct_chg: 0
    }
  },
  {
    id: 'preset_bluechip',
    name: '稳健蓝筹',
    description: '主板核心资产：主板标的，PE <= 30，股价 >= 10元，正常流动性',
    icon: '🛡️',
    tag_type: 'primary',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      market: '主板',
      min_pe: 0.01,
      max_pe: 30,
      min_close: 10,
      volume_level: 'medium'
    }
  },
  {
    id: 'preset_specialized',
    name: '专精特新',
    description: '成长型专精特新标的：北交所小盘创新企业',
    icon: '🌟',
    tag_type: 'warning',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    params: {
      market: '北交所',
      min_pct_chg: 0,
      market_cap_range: 'small'
    }
  }
]

export function useQuantStrategies() {
  const customStrategies = ref<CustomQuantStrategy[]>([])
  const loading = ref(false)

  // 1. 从 LocalStorage 快速读取本地策略
  const loadLocalStrategies = (): CustomQuantStrategy[] => {
    try {
      const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) {
          return parsed
        }
      }
    } catch {
      // 忽略读取错误
    }
    return []
  }

  // 2. 写入 LocalStorage
  const saveLocalStrategies = (list: CustomQuantStrategy[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(list))
    } catch (e) {
      console.warn('Failed to save strategies to localStorage', e)
    }
  }

  // 3. 加载策略列表（后端 API 优先，失败降级本地）
  const loadStrategies = async () => {
    loading.value = true
    try {
      const res = await stocksApi.getCustomStrategies()
      const data = (res as any)?.data || (res as any)
      if (Array.isArray(data) && data.length > 0) {
        customStrategies.value = data
        saveLocalStrategies(data)
        return
      }
      // 后端为空时，检查本地
      const local = loadLocalStrategies()
      if (local.length > 0) {
        customStrategies.value = local
      } else {
        // 使用默认初始模板
        customStrategies.value = [...DEFAULT_TEMPLATES]
        saveLocalStrategies(customStrategies.value)
      }
    } catch {
      // 后端不可用时平滑降级使用本地存储
      const local = loadLocalStrategies()
      customStrategies.value = local.length > 0 ? local : [...DEFAULT_TEMPLATES]
    } finally {
      loading.value = false
    }
  }

  // 4. 创建新策略
  const createStrategy = async (payload: CustomQuantStrategyCreatePayload): Promise<CustomQuantStrategy> => {
    loading.value = true
    const newId = `strat_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    const nowIso = new Date().toISOString()
    const localStrategy: CustomQuantStrategy = {
      id: newId,
      name: payload.name.trim(),
      description: payload.description?.trim() || '',
      icon: payload.icon || '🎯',
      tag_type: payload.tag_type || 'primary',
      params: { ...payload.params },
      created_at: nowIso,
      updated_at: nowIso,
      is_system: false
    }

    try {
      const res = await stocksApi.createCustomStrategy(payload)
      const data = (res as any)?.data || (res as any)
      if (data && data.id) {
        localStrategy.id = data.id
      }
    } catch (err: any) {
      console.warn('Backend strategy creation failed, using local storage', err)
    } finally {
      loading.value = false
    }

    // 始终更新本地响应式列表与缓存
    customStrategies.value = [localStrategy, ...customStrategies.value]
    saveLocalStrategies(customStrategies.value)
    ElMessage.success(`量化策略【${localStrategy.name}】已成功创建并存入策略库`)
    return localStrategy
  }

  // 5. 修改已有策略
  const updateStrategy = async (id: string, payload: CustomQuantStrategyUpdatePayload): Promise<CustomQuantStrategy> => {
    loading.value = true
    const idx = customStrategies.value.findIndex(s => s.id === id)
    if (idx === -1) {
      loading.value = false
      throw new Error('未找到该策略')
    }

    const updated: CustomQuantStrategy = {
      ...customStrategies.value[idx],
      name: payload.name ? payload.name.trim() : customStrategies.value[idx].name,
      description: payload.description !== undefined ? payload.description.trim() : customStrategies.value[idx].description,
      icon: payload.icon || customStrategies.value[idx].icon,
      tag_type: payload.tag_type || customStrategies.value[idx].tag_type,
      params: payload.params ? { ...payload.params } : customStrategies.value[idx].params,
      updated_at: new Date().toISOString()
    }

    try {
      await stocksApi.updateCustomStrategy(id, payload)
    } catch (err: any) {
      console.warn('Backend strategy update failed, saving locally', err)
    } finally {
      loading.value = false
    }

    customStrategies.value[idx] = updated
    saveLocalStrategies(customStrategies.value)
    ElMessage.success(`量化策略【${updated.name}】指标规则已更新`)
    return updated
  }

  // 6. 删除策略
  const deleteStrategy = async (id: string): Promise<boolean> => {
    loading.value = true
    const target = customStrategies.value.find(s => s.id === id)
    try {
      await stocksApi.deleteCustomStrategy(id)
    } catch (err: any) {
      console.warn('Backend strategy deletion failed, removing locally', err)
    } finally {
      loading.value = false
    }

    customStrategies.value = customStrategies.value.filter(s => s.id !== id)
    saveLocalStrategies(customStrategies.value)
    ElMessage.success(`策略【${target?.name || id}】已从策略库删除`)
    return true
  }

  // 7. 恢复系统推荐预设策略
  const resetToDefaultTemplates = async () => {
    loading.value = true
    try {
      const res = await stocksApi.resetDefaultStrategies()
      const data = (res as any)?.data || (res as any)
      if (Array.isArray(data) && data.length > 0) {
        customStrategies.value = data
        saveLocalStrategies(data)
        ElMessage.success('已恢复系统推荐的 8 套量化基准策略')
        return
      }
      customStrategies.value = [...DEFAULT_TEMPLATES]
      saveLocalStrategies(customStrategies.value)
      ElMessage.success('已恢复系统预设策略')
    } catch (e: any) {
      console.warn('Reset to default strategies failed, using local templates', e)
      customStrategies.value = [...DEFAULT_TEMPLATES]
      saveLocalStrategies(customStrategies.value)
      ElMessage.success('已恢复系统推荐预设策略')
    } finally {
      loading.value = false
    }
  }

  // 8. 格式化策略参数为可视化标签列表
  const formatStrategySummary = (params: Partial<StockPoolParams>): string[] => {
    const summary: string[] = []
    if (params.preset === 'quant_candidate') {
      summary.push('量化初筛候选池')
    }
    if (params.min_pe != null || params.max_pe != null) {
      summary.push(`PE: ${params.min_pe ?? 0} ~ ${params.max_pe ?? '∞'}`)
    }
    if (params.min_pb != null || params.max_pb != null) {
      summary.push(`PB: ${params.min_pb ?? 0} ~ ${params.max_pb ?? '∞'}`)
    }
    if (params.min_ps != null || params.max_ps != null) {
      summary.push(`PS: ${params.min_ps ?? 0} ~ ${params.max_ps ?? '∞'}`)
    }
    if (params.min_amount != null) {
      const amtWan = params.min_amount / 10000
      const amtText = amtWan >= 10000 ? `${(amtWan / 10000).toFixed(1)}亿` : `${amtWan.toFixed(0)}万`
      summary.push(`成交额: ≥${amtText}`)
    }
    if (params.min_close != null || params.max_close != null) {
      summary.push(`股价: ¥${params.min_close ?? 0} ~ ${params.max_close ?? '∞'}`)
    }
    if (params.min_pct_chg != null || params.max_pct_chg != null) {
      summary.push(`涨跌幅: ${params.min_pct_chg ?? '-∞'}% ~ ${params.max_pct_chg ?? '+∞'}%`)
    }
    if (params.min_turnover_rate != null || params.max_turnover_rate != null) {
      summary.push(`换手率: ${params.min_turnover_rate ?? 0}% ~ ${params.max_turnover_rate ?? '∞'}%`)
    }
    if (params.min_volume_ratio != null || params.max_volume_ratio != null) {
      summary.push(`量比: ${params.min_volume_ratio ?? 0} ~ ${params.max_volume_ratio ?? '∞'}`)
    }
    if (params.min_roe != null || params.max_roe != null) {
      summary.push(`ROE: ${params.min_roe ?? 0}% ~ ${params.max_roe ?? '∞'}%`)
    }
    if (params.min_net_profit_growth != null || params.max_net_profit_growth != null) {
      summary.push(`净利增速: ${params.min_net_profit_growth ?? '-∞'}% ~ ${params.max_net_profit_growth ?? '+∞'}%`)
    }
    if (params.min_revenue_growth != null || params.max_revenue_growth != null) {
      summary.push(`营收增速: ${params.min_revenue_growth ?? '-∞'}% ~ ${params.max_revenue_growth ?? '+∞'}%`)
    }
    if (params.min_gross_margin != null || params.max_gross_margin != null) {
      summary.push(`毛利率: ${params.min_gross_margin ?? 0}% ~ ${params.max_gross_margin ?? '∞'}%`)
    }
    if (params.volume_level) {
      const volMap: Record<string, string> = { high: '成交>10亿', medium: '成交3-10亿', low: '成交<3亿' }
      summary.push(volMap[params.volume_level] || params.volume_level)
    }
    if (params.market_cap_range) {
      const capMap: Record<string, string> = { small: '小盘(<100亿)', medium: '中盘(100-500亿)', large: '大盘(>500亿)' }
      summary.push(capMap[params.market_cap_range] || params.market_cap_range)
    }
    if (params.min_market_cap != null || params.max_market_cap != null) {
      summary.push(`市值: ${params.min_market_cap ?? 0}亿 ~ ${params.max_market_cap ?? '∞'}亿`)
    }
    if (params.market && params.market !== '全部') {
      summary.push(`板块: ${params.market}`)
    }
    if (params.source && params.source !== '全部') {
      summary.push(`数据源: ${params.source}`)
    }
    return summary
  }

  onMounted(() => {
    loadStrategies()
  })

  return {
    customStrategies,
    loading,
    loadStrategies,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    resetToDefaultTemplates,
    formatStrategySummary
  }
}
