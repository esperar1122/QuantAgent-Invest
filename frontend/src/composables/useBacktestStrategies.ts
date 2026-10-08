import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  quantApi,
  type CustomBacktestStrategy,
  type CustomBacktestStrategyCreatePayload,
  type CustomBacktestStrategyUpdatePayload
} from '@/api/quant'

const LOCAL_STORAGE_KEY = 'backtest_custom_strategies_v1'

// 默认 6 套经典回测策略预设种子
export const DEFAULT_BACKTEST_TEMPLATES: CustomBacktestStrategy[] = [
  {
    id: 'preset_btest_portfolio_core',
    name: '👑 核心资产组合 · 多标的回测',
    description: '精选消费、金融、新能源跨行业龙头多标的配置，结合量价与突破多因子协同，分散个股特质风险。',
    icon: '👑',
    tag_type: 'success',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '600519, 000001, 300750, 002594',
      strategy_name: 'custom_rule',
      sizing_model: 'equal_weight',
      initial_capital: 200000,
      strategy_params: {
        condition_mode: 'and',
        ma_mode: 'cross',
        ma_fast: 5,
        ma_slow: 20,
        volume_filter: 'vol_surge',
        vol_ratio: 1.5,
        rsi_filter: 'none',
        rsi_threshold: 30,
        kdj_filter: 'none',
        breakout_filter: 'none',
        breakout_days: 20
      },
      risk_params: {
        stop_loss_pct: 7.0,
        take_profit_pct: 20.0,
        max_holding_days: 20,
        position_ratio: 95
      },
      friction_params: {
        friction_preset: 'a_share',
        slippage_type: 'percent',
        slippage_val: 0.1,
        commission_wan: 2.5,
        min_commission: 5.0,
        stamp_duty_pct: 0.05,
        transfer_fee_wan: 0.1
      }
    }
  },
  {
    id: 'preset_btest_pingan_factor',
    name: '🌟 平安银行 · 自定义多因子',
    description: '针对金融大盘白马定制：均线金叉 + 成交量异动倍增 + 硬止损与动态止盈，兼顾稳健与防守。',
    icon: '🌟',
    tag_type: 'primary',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '000001',
      strategy_name: 'custom_rule',
      sizing_model: 'equal_weight',
      initial_capital: 100000,
      strategy_params: {
        condition_mode: 'and',
        ma_mode: 'cross',
        ma_fast: 5,
        ma_slow: 20,
        volume_filter: 'vol_surge',
        vol_ratio: 1.5,
        rsi_filter: 'none',
        rsi_threshold: 30,
        kdj_filter: 'none',
        breakout_filter: 'none',
        breakout_days: 20
      },
      risk_params: {
        stop_loss_pct: 5.0,
        take_profit_pct: 15.0,
        max_holding_days: 15,
        position_ratio: 95
      },
      friction_params: {
        friction_preset: 'a_share',
        slippage_type: 'percent',
        slippage_val: 0.1,
        commission_wan: 2.5,
        min_commission: 5.0,
        stamp_duty_pct: 0.05,
        transfer_fee_wan: 0.1
      }
    }
  },
  {
    id: 'preset_btest_maotai_dual_ma',
    name: '📈 贵州茅台 · 趋势双均线',
    description: '经典短期MA5与长期MA20金叉死叉，顺应白酒消费白马长期主升浪波段趋势。',
    icon: '📈',
    tag_type: 'primary',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '600519',
      strategy_name: 'dual_ma',
      sizing_model: 'equal_weight',
      initial_capital: 100000,
      strategy_params: {
        fast_period: 5,
        slow_period: 20
      },
      risk_params: {
        stop_loss_pct: 6.0,
        take_profit_pct: 25.0,
        max_holding_days: 30,
        position_ratio: 95
      },
      friction_params: {
        friction_preset: 'a_share',
        slippage_type: 'percent',
        slippage_val: 0.1,
        commission_wan: 2.5,
        min_commission: 5.0,
        stamp_duty_pct: 0.05,
        transfer_fee_wan: 0.1
      }
    }
  },
  {
    id: 'preset_btest_ningde_macd',
    name: '🌊 宁德时代 · MACD动量波段',
    description: '标准DIF与DEA金叉动量捕捉，灵敏捕获高弹性成长赛道龙头的波段起涨点。',
    icon: '🌊',
    tag_type: 'danger',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '300750',
      strategy_name: 'macd',
      sizing_model: 'equal_weight',
      initial_capital: 100000,
      strategy_params: {
        fast: 12,
        slow: 26,
        signal: 9
      },
      risk_params: {
        stop_loss_pct: 8.0,
        take_profit_pct: 18.0,
        max_holding_days: 15,
        position_ratio: 90
      },
      friction_params: {
        friction_preset: 'a_share',
        slippage_type: 'percent',
        slippage_val: 0.1,
        commission_wan: 2.5,
        min_commission: 5.0,
        stamp_duty_pct: 0.05,
        transfer_fee_wan: 0.1
      }
    }
  },
  {
    id: 'preset_btest_etf300_bollinger',
    name: '🎯 沪深300ETF · 布林均值回归',
    description: '指数ETF低摩擦震荡收敛与均值回归，触及下轨超跌反弹建仓，触及上轨遇阻止盈。',
    icon: '🎯',
    tag_type: 'warning',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '510300',
      strategy_name: 'bollinger',
      sizing_model: 'equal_weight',
      initial_capital: 100000,
      strategy_params: {
        window: 20,
        num_std: 2.0
      },
      risk_params: {
        stop_loss_pct: 4.0,
        take_profit_pct: 10.0,
        max_holding_days: 10,
        position_ratio: 95
      },
      friction_params: {
        friction_preset: 'etf',
        slippage_type: 'percent',
        slippage_val: 0.05,
        commission_wan: 1.0,
        min_commission: 5.0,
        stamp_duty_pct: 0.0,
        transfer_fee_wan: 0.1
      }
    }
  },
  {
    id: 'preset_btest_breakout_pioneer',
    name: '⚡ 突破先锋 · 阶段新高主升',
    description: '放量突破20日阶段新高形态，结合短均线多头排列，专攻高爆发力主升浪短线进攻。',
    icon: '⚡',
    tag_type: 'danger',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    is_system: true,
    cannot_delete: false,
    config: {
      symbol: '002594',
      strategy_name: 'custom_rule',
      sizing_model: 'equal_weight',
      initial_capital: 100000,
      strategy_params: {
        condition_mode: 'and',
        ma_mode: 'bull',
        ma_fast: 5,
        ma_slow: 10,
        volume_filter: 'vol_surge',
        vol_ratio: 1.8,
        rsi_filter: 'none',
        rsi_threshold: 30,
        kdj_filter: 'none',
        breakout_filter: 'new_high',
        breakout_days: 20
      },
      risk_params: {
        stop_loss_pct: 5.0,
        take_profit_pct: 20.0,
        max_holding_days: 12,
        position_ratio: 90
      },
      friction_params: {
        friction_preset: 'a_share',
        slippage_type: 'percent',
        slippage_val: 0.1,
        commission_wan: 2.5,
        min_commission: 5.0,
        stamp_duty_pct: 0.05,
        transfer_fee_wan: 0.1
      }
    }
  }
]

export function useBacktestStrategies() {
  const customStrategies = ref<CustomBacktestStrategy[]>([])
  const loading = ref(false)

  // 1. 从 LocalStorage 快速读取本地策略
  const loadLocalStrategies = (): CustomBacktestStrategy[] => {
    try {
      const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed
        }
      }
    } catch {
      // 忽略读取错误
    }
    return []
  }

  // 2. 写入 LocalStorage
  const saveLocalStrategies = (list: CustomBacktestStrategy[]) => {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(list))
    } catch (e) {
      console.warn('Failed to save backtest strategies to localStorage', e)
    }
  }

  // 3. 加载策略列表（后端 API 优先，失败降级本地）
  const loadStrategies = async () => {
    loading.value = true
    try {
      const res = await quantApi.getUserStrategies()
      const data = (res as any)?.data || (res as any)
      if (Array.isArray(data) && data.length > 0) {
        customStrategies.value = data
        saveLocalStrategies(data)
        return
      }
      // 后端若为空，检查本地
      const local = loadLocalStrategies()
      if (local.length > 0) {
        customStrategies.value = local
      } else {
        customStrategies.value = [...DEFAULT_BACKTEST_TEMPLATES]
        saveLocalStrategies(customStrategies.value)
      }
    } catch {
      // 后端不可用时平滑降级使用本地存储
      const local = loadLocalStrategies()
      customStrategies.value = local.length > 0 ? local : [...DEFAULT_BACKTEST_TEMPLATES]
    } finally {
      loading.value = false
    }
  }

  // 4. 创建新策略
  const createStrategy = async (payload: CustomBacktestStrategyCreatePayload): Promise<CustomBacktestStrategy> => {
    loading.value = true
    const newId = `btest_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    const nowIso = new Date().toISOString()
    const localStrategy: CustomBacktestStrategy = {
      id: newId,
      name: payload.name.trim(),
      description: payload.description?.trim() || '',
      icon: payload.icon || '🎯',
      tag_type: (payload.tag_type as any) || 'primary',
      config: JSON.parse(JSON.stringify(payload.config)),
      created_at: nowIso,
      updated_at: nowIso,
      is_system: false,
      cannot_delete: false
    }

    try {
      const res = await quantApi.createUserStrategy(payload)
      const serverData = (res as any)?.data || (res as any)
      if (serverData && serverData.id) {
        customStrategies.value.unshift(serverData)
        saveLocalStrategies(customStrategies.value)
        ElMessage.success(`🎉 回测策略【${serverData.name}】已成功持久化保存！`)
        return serverData
      }
    } catch {
      console.warn('Backend API save failed, saved locally')
    }

    // 后端失败时使用本地对象
    customStrategies.value.unshift(localStrategy)
    saveLocalStrategies(customStrategies.value)
    ElMessage.success(`🎉 回测策略【${localStrategy.name}】已在本地持久化保存！`)
    return localStrategy
  }

  // 5. 更新已有策略
  const updateStrategy = async (id: string, payload: CustomBacktestStrategyUpdatePayload): Promise<boolean> => {
    loading.value = true
    const nowIso = new Date().toISOString()
    try {
      await quantApi.updateUserStrategy(id, payload)
    } catch {
      console.warn('Backend update failed, updating locally')
    }

    const idx = customStrategies.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      const current = customStrategies.value[idx]
      customStrategies.value[idx] = {
        ...current,
        name: payload.name !== undefined ? payload.name.trim() : current.name,
        description: payload.description !== undefined ? payload.description.trim() : current.description,
        icon: payload.icon !== undefined ? payload.icon : current.icon,
        tag_type: payload.tag_type !== undefined ? (payload.tag_type as any) : current.tag_type,
        config: payload.config !== undefined ? JSON.parse(JSON.stringify(payload.config)) : current.config,
        updated_at: nowIso
      }
      saveLocalStrategies(customStrategies.value)
      ElMessage.success(`✅ 回测策略【${customStrategies.value[idx].name}】更新成功！`)
      loading.value = false
      return true
    }
    loading.value = false
    return false
  }

  // 6. 删除策略
  const deleteStrategy = async (id: string): Promise<boolean> => {
    const target = customStrategies.value.find(s => s.id === id)
    if (target?.cannot_delete) {
      ElMessage.warning('该系统核心策略不允许删除！')
      return false
    }

    try {
      await quantApi.deleteUserStrategy(id)
    } catch {
      console.warn('Backend delete failed, removing locally')
    }

    customStrategies.value = customStrategies.value.filter(s => s.id !== id)
    saveLocalStrategies(customStrategies.value)
    ElMessage.success('🗑️ 回测策略已成功删除！')
    return true
  }

  // 7. 重置为系统推荐预设
  const resetDefaults = async (): Promise<void> => {
    loading.value = true
    try {
      const res = await quantApi.resetDefaultUserStrategies()
      const data = (res as any)?.data || (res as any)
      if (Array.isArray(data) && data.length > 0) {
        customStrategies.value = data
        saveLocalStrategies(data)
        ElMessage.success('✨ 已成功恢复系统推荐回测策略预设！')
        return
      }
    } catch {
      console.warn('Backend reset failed, restoring local presets')
    }

    // 仅保留自建策略，同时重置所有系统预设
    const userOnly = customStrategies.value.filter(s => !s.is_system)
    customStrategies.value = [...DEFAULT_BACKTEST_TEMPLATES, ...userOnly]
    saveLocalStrategies(customStrategies.value)
    ElMessage.success('✨ 已成功恢复系统推荐回测策略预设！')
    loading.value = false
  }

  // 8. 根据 ID 查找策略
  const getStrategyById = (id: string) => {
    return customStrategies.value.find(s => s.id === id)
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
    resetDefaults,
    getStrategyById
  }
}
