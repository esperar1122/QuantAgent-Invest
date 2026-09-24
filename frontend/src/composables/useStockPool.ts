import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { stocksApi, type StockPoolItem, type StockPoolStats, type StockPoolParams, type CustomQuantStrategy } from '@/api/stocks'
import { useFavoritesStore } from '@/stores/favorites'
import { useQuantStrategies } from '@/composables/useQuantStrategies'
import { ApiClient } from '@/api/request'

export function useStockPool() {
  const router = useRouter()
  const favoritesStore = useFavoritesStore()
  const quantStrategiesStore = useQuantStrategies()

  // 状态控制
  const loading = ref(false)
  const syncing = ref(false)
  const showAdvancedFilter = ref(false)
  const stockList = ref<StockPoolItem[]>([])
  const selectedStocks = ref<StockPoolItem[]>([])
  const total = ref(0)

  // 顶部统计
  const stats = reactive<StockPoolStats>({
    total_stocks: 5564,
    main_board_count: 3197,
    chinext_count: 1406,
    star_count: 617,
    bse_count: 344,
    index_count: 10
  })

  // 查询参数对象
  const queryParams = reactive<StockPoolParams>({
    preset: undefined,
    keyword: '',
    market: '全部',
    source: '全部',
    min_pe: null,
    max_pe: null,
    min_pb: null,
    max_pb: null,
    min_ps: null,
    max_ps: null,
    min_close: null,
    max_close: null,
    min_pct_chg: null,
    max_pct_chg: null,
    min_turnover_rate: null,
    max_turnover_rate: null,
    min_volume_ratio: null,
    max_volume_ratio: null,
    volume_level: '',
    market_cap_range: '',
    min_market_cap: null,
    max_market_cap: null,
    min_roe: null,
    max_roe: null,
    min_net_profit_growth: null,
    max_net_profit_growth: null,
    min_revenue_growth: null,
    max_revenue_growth: null,
    min_gross_margin: null,
    max_gross_margin: null,
    min_amount: null,
    max_amount: null,
    page: 1,
    page_size: 20,
    sort_field: 'code',
    sort_order: 'asc'
  })

  // 快捷策略预设（从策略库中动态提取预设模板，支持自定义修改与更新）
  const strategyPresets = computed(() => {
    const sys = quantStrategiesStore.customStrategies.value.filter(s => s.is_system || s.id.startsWith('preset_'))
    if (sys.length > 0) {
      return sys.map(s => ({
        id: s.id,
        name: `${s.icon || '🎯'} ${s.name}`,
        type: (s.tag_type || 'primary') as any,
        cannot_delete: s.cannot_delete,
        params: { ...s.params }
      }))
    }
    return [
      {
        id: 'preset_quant_candidate',
        name: '🎯 量化初筛候选池',
        type: 'primary' as const,
        cannot_delete: true,
        params: { preset: 'quant_candidate', min_pe: null, max_pe: null, min_amount: 80000000 }
      },
      {
        id: 'preset_low_valuation',
        name: '💎 低估值价值',
        type: 'success' as const,
        cannot_delete: false,
        params: { min_pe: 0, max_pe: 20, min_pb: 0, max_pb: 2 }
      },
      {
        id: 'preset_buffett_roe',
        name: '👑 巴菲特高ROE',
        type: 'warning' as const,
        cannot_delete: false,
        params: { min_roe: 15, min_pe: 0, max_pe: 30 }
      },
      {
        id: 'preset_growth',
        name: '🚀 业绩高成长',
        type: 'danger' as const,
        cannot_delete: false,
        params: { min_net_profit_growth: 30, min_revenue_growth: 20 }
      },
      {
        id: 'preset_breakout',
        name: '⚡ 强势突破',
        type: 'danger' as const,
        cannot_delete: false,
        params: { min_pct_chg: 3, min_turnover_rate: 3, volume_level: 'high' }
      },
      {
        id: 'preset_active_turnover',
        name: '🔥 高换手活跃',
        type: 'danger' as const,
        cannot_delete: false,
        params: { min_turnover_rate: 5, min_volume_ratio: 1.5, min_pct_chg: 0 }
      },
      {
        id: 'preset_bluechip',
        name: '🛡️ 稳健蓝筹',
        type: 'primary' as const,
        cannot_delete: false,
        params: { market: '主板', min_pe: 0, max_pe: 30, min_close: 10, volume_level: 'medium' }
      },
      {
        id: 'preset_specialized',
        name: '🌟 专精特新',
        type: 'warning' as const,
        cannot_delete: false,
        params: { market: '北交所', min_pct_chg: 0, market_cap_range: 'small' }
      }
    ]
  })

  // 计算当前生效的高级筛选条件数量
  const activeAdvancedCount = computed(() => {
    let cnt = 0
    if (queryParams.preset) cnt++
    if (queryParams.min_pe != null || queryParams.max_pe != null) cnt++
    if (queryParams.min_pb != null || queryParams.max_pb != null) cnt++
    if (queryParams.min_ps != null || queryParams.max_ps != null) cnt++
    if (queryParams.min_close != null || queryParams.max_close != null) cnt++
    if (queryParams.min_pct_chg != null || queryParams.max_pct_chg != null) cnt++
    if (queryParams.min_turnover_rate != null || queryParams.max_turnover_rate != null) cnt++
    if (queryParams.min_volume_ratio != null || queryParams.max_volume_ratio != null) cnt++
    if (queryParams.min_roe != null || queryParams.max_roe != null) cnt++
    if (queryParams.min_net_profit_growth != null || queryParams.max_net_profit_growth != null) cnt++
    if (queryParams.min_revenue_growth != null || queryParams.max_revenue_growth != null) cnt++
    if (queryParams.min_gross_margin != null || queryParams.max_gross_margin != null) cnt++
    if (queryParams.volume_level || queryParams.min_amount != null || queryParams.max_amount != null) cnt++
    if (queryParams.market_cap_range || queryParams.min_market_cap != null || queryParams.max_market_cap != null) cnt++
    return cnt
  })

  const hasActiveAdvancedFilters = computed(() => activeAdvancedCount.value > 0)

  // 生效筛选标签
  const activeFilterTags = computed(() => {
    const tags: Array<{ key: string; label: string; text: string }> = []
    if (queryParams.preset === 'quant_candidate') {
      const candStrat = quantStrategiesStore.customStrategies.value.find(s => s.id === 'preset_quant_candidate')
      const p = candStrat?.params
      const pePart = p?.max_pe ? `0<PE≤${p.max_pe}` : '合理估值'
      const amtWan = p?.min_amount ? p.min_amount / 10000 : 8000
      const amtPart = `成交额≥${amtWan >= 10000 ? (amtWan / 10000) + '亿' : amtWan + '万'}`
      tags.push({ key: 'preset', label: '量化初筛', text: `量化初筛候选池 (${pePart}, ${amtPart})` })
    }
    if (queryParams.keyword && queryParams.keyword.trim()) {
      tags.push({ key: 'keyword', label: '标的', text: queryParams.keyword.trim() })
    }
    if (queryParams.market && queryParams.market !== '全部') {
      tags.push({ key: 'market', label: '板块', text: queryParams.market })
    }
    if (queryParams.source && queryParams.source !== '全部') {
      tags.push({ key: 'source', label: '数据源', text: queryParams.source })
    }
    if (queryParams.min_pe != null || queryParams.max_pe != null) {
      tags.push({ key: 'pe', label: 'PE', text: `${queryParams.min_pe ?? 0} ~ ${queryParams.max_pe ?? '∞'}` })
    }
    if (queryParams.min_pb != null || queryParams.max_pb != null) {
      tags.push({ key: 'pb', label: 'PB', text: `${queryParams.min_pb ?? 0} ~ ${queryParams.max_pb ?? '∞'}` })
    }
    if (queryParams.min_ps != null || queryParams.max_ps != null) {
      tags.push({ key: 'ps', label: 'PS', text: `${queryParams.min_ps ?? 0} ~ ${queryParams.max_ps ?? '∞'}` })
    }
    if (queryParams.min_close != null || queryParams.max_close != null) {
      tags.push({ key: 'close', label: '股价', text: `¥${queryParams.min_close ?? 0} ~ ${queryParams.max_close ?? '∞'}` })
    }
    if (queryParams.min_pct_chg != null || queryParams.max_pct_chg != null) {
      tags.push({ key: 'pct_chg', label: '涨跌幅', text: `${queryParams.min_pct_chg ?? '-∞'}% ~ ${queryParams.max_pct_chg ?? '+∞'}%` })
    }
    if (queryParams.min_turnover_rate != null || queryParams.max_turnover_rate != null) {
      tags.push({ key: 'turnover_rate', label: '换手率', text: `${queryParams.min_turnover_rate ?? 0}% ~ ${queryParams.max_turnover_rate ?? '∞'}%` })
    }
    if (queryParams.min_volume_ratio != null || queryParams.max_volume_ratio != null) {
      tags.push({ key: 'volume_ratio', label: '量比', text: `${queryParams.min_volume_ratio ?? 0} ~ ${queryParams.max_volume_ratio ?? '∞'}` })
    }
    if (queryParams.min_roe != null || queryParams.max_roe != null) {
      tags.push({ key: 'roe', label: 'ROE', text: `${queryParams.min_roe ?? 0}% ~ ${queryParams.max_roe ?? '∞'}%` })
    }
    if (queryParams.min_net_profit_growth != null || queryParams.max_net_profit_growth != null) {
      tags.push({ key: 'net_profit_growth', label: '净利增速', text: `${queryParams.min_net_profit_growth ?? '-∞'}% ~ ${queryParams.max_net_profit_growth ?? '+∞'}%` })
    }
    if (queryParams.min_revenue_growth != null || queryParams.max_revenue_growth != null) {
      tags.push({ key: 'revenue_growth', label: '营收增速', text: `${queryParams.min_revenue_growth ?? '-∞'}% ~ ${queryParams.max_revenue_growth ?? '+∞'}%` })
    }
    if (queryParams.min_gross_margin != null || queryParams.max_gross_margin != null) {
      tags.push({ key: 'gross_margin', label: '毛利率', text: `${queryParams.min_gross_margin ?? 0}% ~ ${queryParams.max_gross_margin ?? '∞'}%` })
    }
    if (queryParams.min_amount != null || queryParams.max_amount != null) {
      tags.push({
        key: 'amount_range',
        label: '日均成交额',
        text: `¥${queryParams.min_amount ?? 0}亿 ~ ${queryParams.max_amount ?? '∞'}亿`
      })
    } else if (queryParams.volume_level) {
      const volMap: Record<string, string> = { high: '高活跃(>10亿)', medium: '正常(3-10亿)', low: '清淡(<3亿)' }
      tags.push({ key: 'volume_level', label: '成交活跃度', text: volMap[queryParams.volume_level] || queryParams.volume_level })
    }

    if (queryParams.min_market_cap != null || queryParams.max_market_cap != null) {
      tags.push({ key: 'market_cap_num', label: '市值区间', text: `${queryParams.min_market_cap ?? 0}亿 ~ ${queryParams.max_market_cap ?? '∞'}亿` })
    } else if (queryParams.market_cap_range) {
      const capMap: Record<string, string> = { small: '小盘(<100亿)', medium: '中盘(100-500亿)', large: '大盘(>500亿)' }
      tags.push({ key: 'market_cap_range', label: '市值规模', text: capMap[queryParams.market_cap_range] || queryParams.market_cap_range })
    }
    return tags
  })

  // 移除单个筛选标签
  const removeFilterTag = (key: string) => {
    switch (key) {
      case 'preset':
        queryParams.preset = undefined
        if (router.currentRoute.value.query.preset) {
          const q = { ...router.currentRoute.value.query }
          delete q.preset
          router.replace({ query: q })
        }
        break
      case 'keyword': queryParams.keyword = ''; break
      case 'market': queryParams.market = '全部'; break
      case 'source': queryParams.source = '全部'; break
      case 'pe': queryParams.min_pe = null; queryParams.max_pe = null; break
      case 'pb': queryParams.min_pb = null; queryParams.max_pb = null; break
      case 'ps': queryParams.min_ps = null; queryParams.max_ps = null; break
      case 'close': queryParams.min_close = null; queryParams.max_close = null; break
      case 'pct_chg': queryParams.min_pct_chg = null; queryParams.max_pct_chg = null; break
      case 'turnover_rate': queryParams.min_turnover_rate = null; queryParams.max_turnover_rate = null; break
      case 'volume_ratio': queryParams.min_volume_ratio = null; queryParams.max_volume_ratio = null; break
      case 'roe': queryParams.min_roe = null; queryParams.max_roe = null; break
      case 'net_profit_growth': queryParams.min_net_profit_growth = null; queryParams.max_net_profit_growth = null; break
      case 'revenue_growth': queryParams.min_revenue_growth = null; queryParams.max_revenue_growth = null; break
      case 'gross_margin': queryParams.min_gross_margin = null; queryParams.max_gross_margin = null; break
      case 'volume_level':
      case 'amount_range':
        queryParams.volume_level = ''
        queryParams.min_amount = null
        queryParams.max_amount = null
        break
      case 'market_cap_range':
      case 'market_cap_num':
        queryParams.market_cap_range = ''
        queryParams.min_market_cap = null
        queryParams.max_market_cap = null
        break
    }
    handleSearch()
  }

  // 展开/收起高级筛选
  const toggleAdvancedFilter = () => {
    showAdvancedFilter.value = !showAdvancedFilter.value
  }

  // 清除所有高级指标筛选参数
  const clearFilterParams = () => {
    queryParams.preset = undefined
    if (router.currentRoute.value.query.preset) {
      const q = { ...router.currentRoute.value.query }
      delete q.preset
      router.replace({ query: q })
    }
    queryParams.min_pe = null
    queryParams.max_pe = null
    queryParams.min_pb = null
    queryParams.max_pb = null
    queryParams.min_ps = null
    queryParams.max_ps = null
    queryParams.min_close = null
    queryParams.max_close = null
    queryParams.min_pct_chg = null
    queryParams.max_pct_chg = null
    queryParams.min_turnover_rate = null
    queryParams.max_turnover_rate = null
    queryParams.min_volume_ratio = null
    queryParams.max_volume_ratio = null
    queryParams.min_roe = null
    queryParams.max_roe = null
    queryParams.min_net_profit_growth = null
    queryParams.max_net_profit_growth = null
    queryParams.min_revenue_growth = null
    queryParams.max_revenue_growth = null
    queryParams.min_gross_margin = null
    queryParams.max_gross_margin = null
    queryParams.volume_level = ''
    queryParams.market_cap_range = ''
    queryParams.min_market_cap = null
    queryParams.max_market_cap = null
    queryParams.min_amount = null
    queryParams.max_amount = null
  }

  // 应用策略预设
  const applyStrategyPreset = (preset: any) => {
    clearFilterParams()
    queryParams.preset = (preset.params as any)?.preset || undefined
    Object.assign(queryParams, preset.params)
    ElMessage.success(`已应用策略预设：${preset.name}`)
    handleSearch()
  }

  // 清空高级筛选条件
  const resetAdvancedFilters = () => {
    clearFilterParams()
    handleSearch()
  }

  // 加载数据
  const loadData = async () => {
    loading.value = true
    try {
      // 过滤掉无效参数（null, undefined, 空字符串）以保证请求严谨
      const cleanParams: Record<string, any> = {}
      for (const [k, v] of Object.entries(queryParams)) {
        if (v !== null && v !== undefined && v !== '') {
          cleanParams[k] = v
        }
      }
      const res = await stocksApi.getPool(cleanParams)
      const poolData = res?.data || (res as any)
      if (poolData && poolData.items) {
        stockList.value = poolData.items
        total.value = poolData.total
        if (poolData.stats) {
          Object.assign(stats, poolData.stats)
        }
      }
    } catch (err: any) {
      ElMessage.error(`加载股票池数据失败: ${err.message || err}`)
    } finally {
      loading.value = false
    }
  }

  // 快速点击顶部卡片过滤板块
  const quickFilterMarket = (marketName: string) => {
    queryParams.market = marketName
    queryParams.page = 1
    loadData()
  }

  // 搜索操作
  const handleSearch = () => {
    queryParams.page = 1
    loadData()
  }

  // 全局重置操作
  const handleReset = () => {
    queryParams.keyword = ''
    queryParams.market = '全部'
    queryParams.source = '全部'
    queryParams.preset = undefined
    if (router.currentRoute.value.query.preset) {
      const q = { ...router.currentRoute.value.query }
      delete q.preset
      router.replace({ query: q })
    }
    resetAdvancedFilters()
  }

  // 表格多选变化
  const handleSelectionChange = (selection: StockPoolItem[]) => {
    selectedStocks.value = selection
  }

  // 批量智能研判
  const handleBatchAnalyze = async () => {
    if (selectedStocks.value.length === 0) {
      ElMessage.warning('请先在表格中勾选要分析的标的')
      return
    }
    try {
      await ElMessageBox.confirm(
        `确定要对选中的 ${selectedStocks.value.length} 只股票启动多智能体批量投研研判吗？`,
        '启动批量研判',
        {
          confirmButtonText: '立即研判',
          cancelButtonText: '取消',
          type: 'info'
        }
      )
      const codes = selectedStocks.value.map(s => s.code).join(',')
      router.push({
        path: '/analysis/batch',
        query: { stocks: codes, market: 'CN' }
      })
    } catch {
      // 取消
    }
  }

  // 导出 CSV 文件
  const exportCSV = () => {
    if (stockList.value.length === 0) {
      ElMessage.warning('当前无数据可导出')
      return
    }

    const headers = ['股票代码', '股票名称', '所属板块', '最新价(元)', '日涨跌幅(%)', '换手率(%)', '量比', '成交额(元)', '流通市值(亿)', '市盈率(PE)', '市净率(PB)', '市销率(PS)', 'ROE(%)', '净利润增速(%)', '营收增速(%)', '毛利率(%)', '数据源', '最新交易日']
    const rows = stockList.value.map(item => [
      `"${item.code}"`,
      `"${item.name}"`,
      `"${item.market}"`,
      item.close ?? '',
      item.pct_chg ?? '',
      item.turnover_rate ?? '',
      item.volume_ratio ?? '',
      item.amount ?? '',
      item.circ_mv ?? '',
      item.pe ?? '',
      item.pb ?? '',
      item.ps ?? '',
      item.roe ?? '',
      item.net_profit_growth ?? '',
      item.revenue_growth ?? '',
      item.gross_margin ?? '',
      `"${item.source}"`,
      `"${item.trade_date || ''}"`
    ])

    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const now = new Date()
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    link.href = URL.createObjectURL(blob)
    link.setAttribute('download', `QuantAgent_股票池_导出_${dateStr}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success(`成功导出当前页 ${stockList.value.length} 条数据为 CSV 文件`)
  }

  // 自选股加载与检查
  const loadFavorites = async () => {
    await favoritesStore.fetchFavorites()
  }

  const isFavorited = (code: string) => favoritesStore.isFavorite(code)

  // 加入/移出自选股
  const toggleFavorite = async (row: StockPoolItem) => {
    await favoritesStore.toggleFavorite(row)
  }

  // 分页变化
  const handleSizeChange = (val: number) => {
    queryParams.page_size = val
    queryParams.page = 1
    loadData()
  }

  const handleCurrentChange = (val: number) => {
    queryParams.page = val
    loadData()
  }

  // 表格排序
  const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
    if (!order) {
      queryParams.sort_field = 'code'
      queryParams.sort_order = 'asc'
    } else {
      queryParams.sort_field = prop
      queryParams.sort_order = order === 'ascending' ? 'asc' : 'desc'
    }
    loadData()
  }

  // 跳转智能研判联动（终端内直达个股研究，传统工作台直达单股分析）
  const goToAnalysis = (row: StockPoolItem) => {
    if (router.currentRoute.value.path.startsWith('/terminal')) {
      router.push({
        path: '/terminal/stock',
        query: { code: row.code }
      })
      return
    }
    router.push({
      path: '/analysis/single',
      query: {
        code: row.code,
        name: row.name,
        market: 'CN'
      }
    })
  }

  // 触发多源同步
  const handleTriggerSync = async () => {
    syncing.value = true
    try {
      await ApiClient.post('/api/sync/multi-source/start', {})
      ElNotification({
        title: '同步任务已启动',
        message: '全市场 5500+ 只股票数据多源同步任务已在后台启动，将自动拉取最新基础数据与行情。',
        type: 'success'
      })
      setTimeout(() => {
        loadData()
        syncing.value = false
      }, 3000)
    } catch (err: any) {
      ElMessage.error(`启动同步失败: ${err.message || err}`)
      syncing.value = false
    }
  }

  onMounted(() => {
    const routeQuery = router.currentRoute.value.query
    if (routeQuery.preset && typeof routeQuery.preset === 'string') {
      queryParams.preset = routeQuery.preset
    }
    if (routeQuery.market && typeof routeQuery.market === 'string') {
      queryParams.market = routeQuery.market
    }
    if (routeQuery.keyword && typeof routeQuery.keyword === 'string') {
      queryParams.keyword = routeQuery.keyword
    }
    loadData()
    loadFavorites()
  })

  // 监听路由参数变化（支持在概览与选股池间自由跳转更新）
  watch(
    () => router.currentRoute.value.query.preset,
    (newPreset) => {
      const val = typeof newPreset === 'string' ? newPreset : undefined
      if (queryParams.preset !== val) {
        queryParams.preset = val
        queryParams.page = 1
        loadData()
      }
    }
  )

  // 自定义量化策略管理
  const strategyEditVisible = ref(false)
  const strategyManageVisible = ref(false)
  const currentEditingStrategy = ref<CustomQuantStrategy | null>(null)

  const openCreateStrategy = () => {
    currentEditingStrategy.value = null
    strategyEditVisible.value = true
  }

  const openEditStrategy = (strat: CustomQuantStrategy) => {
    currentEditingStrategy.value = strat
    strategyEditVisible.value = true
  }

  const openManageStrategies = () => {
    strategyManageVisible.value = true
  }

  const applyCustomStrategy = (strat: CustomQuantStrategy) => {
    clearFilterParams()
    Object.assign(queryParams, strat.params)
    if (strat.params.preset) {
      queryParams.preset = strat.params.preset
    }
    ElMessage.success(`已应用量化策略：${strat.name}`)
    handleSearch()
  }

  const handleSaveStrategy = async (payload: any, id?: string) => {
    try {
      if (id) {
        await quantStrategiesStore.updateStrategy(id, payload)
      } else {
        await quantStrategiesStore.createStrategy(payload)
      }
      strategyEditVisible.value = false
      if (id === 'preset_quant_candidate' || queryParams.preset === 'quant_candidate') {
        loadData()
      }
    } catch (e: any) {
      ElMessage.error(e.message || '保存策略失败')
    }
  }

  const handleDeleteStrategy = async (id: string) => {
    await quantStrategiesStore.deleteStrategy(id)
  }

  return {
    loading,
    syncing,
    showAdvancedFilter,
    stockList,
    selectedStocks,
    total,
    favoriteSet: favoritesStore.favoriteCodes,
    stats,
    queryParams,
    strategyPresets,
    customStrategies: quantStrategiesStore.customStrategies,
    resetToDefaultTemplates: quantStrategiesStore.resetToDefaultTemplates,
    strategyEditVisible,
    strategyManageVisible,
    currentEditingStrategy,
    openCreateStrategy,
    openEditStrategy,
    openManageStrategies,
    applyCustomStrategy,
    handleSaveStrategy,
    handleDeleteStrategy,
    activeAdvancedCount,
    hasActiveAdvancedFilters,
    activeFilterTags,
    removeFilterTag,
    toggleAdvancedFilter,
    applyStrategyPreset,
    resetAdvancedFilters,
    loadData,
    quickFilterMarket,
    handleSearch,
    handleReset,
    handleSelectionChange,
    handleBatchAnalyze,
    exportCSV,
    loadFavorites,
    isFavorited,
    toggleFavorite,
    handleSizeChange,
    handleCurrentChange,
    handleSortChange,
    goToAnalysis,
    handleTriggerSync
  }
}
