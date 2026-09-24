<template>
  <div class="overview-view">
    <!-- 顶部 5 大宏观量化 KPI 卡片栏 -->
    <div class="kpi-banner">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">市场研判状态</span>
          <span class="kpi-tag" :class="kpis.sentiment_score >= 60 ? 'status-bull' : 'status-bear'">{{ kpis.sentiment_status }}</span>
        </div>
        <div class="kpi-val tabular-nums">{{ kpis.sentiment_score.toFixed(1) }} <span class="sub-val">/ 100</span></div>
        <div class="kpi-sub">
          <span>情绪动能</span>
          <span :class="kpis.sentiment_momentum.startsWith('+') ? 'trend-up' : 'trend-down'" class="tabular-nums">{{ kpis.sentiment_momentum }}</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">市场宽度 (涨跌分布)</span>
          <span class="kpi-tag">{{ kpis.up_count >= kpis.down_count ? '多头占优' : '空头占优' }}</span>
        </div>
        <div class="kpi-val tabular-nums">
          <span class="up-count">{{ kpis.up_count.toLocaleString() }}</span>
          <span class="mid-slash">/</span>
          <span class="down-count">{{ kpis.down_count.toLocaleString() }}</span>
        </div>
        <div class="kpi-sub">
          <span>涨停 {{ kpis.limit_up }} 家</span>
          <span class="neutral">跌停 {{ kpis.limit_down }} 家</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">两市总成交额</span>
          <span class="kpi-tag">{{ kpis.total_amount_yi >= 8000 ? '活跃放量' : '量能平稳' }}</span>
        </div>
        <div class="kpi-val tabular-nums">{{ kpis.total_amount_desc.split(' ')[0] }} <span class="sub-val">{{ kpis.total_amount_desc.split(' ')[1] || '万亿' }}</span></div>
        <div class="kpi-sub">
          <span>较上一日</span>
          <span class="trend-up tabular-nums">{{ kpis.amount_change_desc }}</span>
        </div>
      </div>

      <div class="kpi-card clickable" @click="$router.push({ path: '/terminal/screening', query: { preset: 'quant_candidate' } })">
        <div class="kpi-header">
          <span class="kpi-title">量化候选股票池</span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
        <div class="kpi-val tabular-nums">{{ kpis.pool_count.toLocaleString() }} <span class="sub-val">只</span></div>
        <div class="kpi-sub">
          <span>全市场 {{ kpis.total_stocks.toLocaleString() }} 只初筛</span>
          <span class="highlight tabular-nums">筛选率 {{ kpis.pool_rate }}</span>
        </div>
      </div>

      <div class="kpi-card clickable" @click="$router.push('/terminal/workflow')">
        <div class="kpi-header">
          <span class="kpi-title">多智能体协同任务</span>
          <el-icon class="arrow-icon"><ArrowRight /></el-icon>
        </div>
        <div class="kpi-val tabular-nums">{{ kpis.running_tasks }} <span class="sub-val">组运行中</span></div>
        <div class="kpi-sub">
          <span>已输出 {{ kpis.completed_tasks }} 份案卷</span>
          <span class="highlight">{{ kpis.failed_tasks }} 异常阻塞</span>
        </div>
      </div>
    </div>

    <!-- 01->05 核心全景链路横幅 -->
    <div class="pipeline-section">
      <PipelineBanner :kpis="kpis" />
    </div>

    <!-- 主展示网格 -->
    <div id="market-dashboard-anchor" class="main-dashboard-grid">
      <!-- 左侧：市场分时走势与行业表现 -->
      <div class="grid-left-panel">
        <!-- 分时走势 -->
        <MarketTrendChart />

        <!-- 行业与风格板块看板 -->
        <div class="sectors-card">
          <div class="card-header">
            <div class="header-left">
              <span class="header-title">高频行业资金与涨跌监测</span>
              <span class="header-sub">申万一级行业实时监测</span>
            </div>
            <div class="header-right">
              <span class="time-tip tabular-nums">更新于 {{ lastUpdateTime }}</span>
            </div>
          </div>

          <div class="sectors-table-wrapper">
            <table class="sectors-table">
              <thead>
                <tr>
                  <th class="text-left">行业板块</th>
                  <th class="text-right">涨跌幅</th>
                  <th class="text-right">主力净流入</th>
                  <th class="text-right">领涨龙头</th>
                  <th class="text-right">量化强度分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sec in industryList" :key="sec.name">
                  <td class="text-left fw-semibold">{{ sec.name }}</td>
                  <td :class="['text-right tabular-nums', sec.change >= 0 ? 'color-up' : 'color-down']">
                    {{ sec.change >= 0 ? '+' : '' }}{{ sec.change.toFixed(2) }}%
                  </td>
                  <td :class="['text-right tabular-nums', sec.flow >= 0 ? 'color-up' : 'color-down']">
                    {{ sec.flow >= 0 ? '+' : '' }}{{ sec.flow }} 亿
                  </td>
                  <td class="text-right">
                    <span 
                      class="leader-badge clickable" 
                      :title="'点击立即个股研判: ' + sec.leader"
                      @click.stop="goToStock(sec.leaderCode)"
                    >
                      {{ sec.leader }}
                    </span>
                  </td>
                  <td class="text-right tabular-nums fw-bold">
                    <span class="score-pill" :class="sec.score >= 85 ? 'high' : 'medium'">{{ sec.score }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 右侧：量化主线与实时多智能体分析流水线流 -->
      <div class="grid-right-panel">
        <!-- 量化主线卡片 -->
        <div class="themes-card">
          <div class="card-header">
            <span class="header-title">量化重点进攻主线 (Quant Alpha)</span>
            <span class="badge-blue">{{ themeList.length }} 个主线共振</span>
          </div>

          <div class="theme-items" v-if="themeList.length > 0">
            <div 
              v-for="t in themeList" 
              :key="t.name" 
              class="theme-item"
              @click="$router.push('/terminal/screening')"
            >
              <div class="theme-top">
                <span class="theme-name">{{ t.name }}</span>
                <span class="theme-score tabular-nums">评分 {{ t.score }}</span>
              </div>
              <p class="theme-logic">{{ t.logic }}</p>
              <div class="theme-stocks">
                <span class="stocks-label">核心成分池:</span>
                <span 
                  v-for="s in t.stocks" 
                  :key="s.code" 
                  class="stock-pill clickable"
                  :title="'点击前往个股研判: ' + s.name"
                  @click.stop="goToStock(s.code)"
                >
                  {{ s.name }}
                </span>
              </div>
            </div>
          </div>
          <div class="theme-empty" v-else>
            <span class="empty-icon">🛡️</span>
            <span class="empty-text">当前市场处于低波动或普跌防守周期，暂无满足量化进攻阈值的重点共振主线</span>
          </div>
        </div>

        <!-- 实时智能体协同研判流 -->
        <div class="feed-card">
          <div class="card-header">
            <div class="feed-header-left">
              <span class="pulse-indicator"></span>
              <div class="header-titles">
                <span class="header-title">智能体协同事件流</span>
                <span class="header-sub">Live Event Feed</span>
              </div>
              <el-tooltip :content="cycleTooltip" placement="top">
                <span class="online-tag">
                  {{ cycleBadgeText }}
                </span>
              </el-tooltip>
            </div>
            <div class="feed-header-right">
              <button 
                class="icon-refresh-btn" 
                title="刷新事件流" 
                :class="{ spinning: isRefreshing }"
                @click="refreshEvents"
              >
                <el-icon><RefreshRight /></el-icon>
              </button>
              <button class="text-btn" @click="goToWorkflow()">进入工作流 →</button>
            </div>
          </div>

          <!-- 分类筛选胶囊条 -->
          <div class="feed-filter-bar">
            <button 
              v-for="tab in eventFilterTabs" 
              :key="tab.key"
              class="filter-pill-btn" 
              :class="{ active: currentEventFilter === tab.key }"
              @click="currentEventFilter = tab.key"
            >
              <span>{{ tab.label }}</span>
              <span class="tab-count">{{ getTabCount(tab.key) }}</span>
            </button>
          </div>

          <!-- 事件流列表容器 -->
          <div class="feed-list-container">
            <div v-if="filteredEvents.length > 0" class="feed-list">
              <div 
                v-for="(ev, idx) in filteredEvents" 
                :key="ev.id || 'ev-' + idx" 
                class="feed-item"
                :class="ev.badgeClass"
              >
                <!-- 顶部元信息行：相对时间、Agent徽章、事件类型、操作评级、右侧快捷入口 -->
                <div class="feed-item-top">
                  <div class="meta-left">
                    <span class="feed-time-badge" :title="'触发时间: ' + ev.time">{{ ev.relativeTime || ev.time }}</span>
                    <span class="feed-badge" :class="ev.badgeClass">{{ ev.agentName || ev.agent }}</span>
                    <span class="event-type-badge" v-if="ev.eventType">{{ ev.eventType }}</span>
                    <span 
                      v-if="ev.action" 
                      class="action-pill" 
                      :class="ev.actionType || 'info'"
                    >
                      {{ ev.action }}<span v-if="ev.score" class="score-num"> {{ ev.score }}分</span>
                    </span>
                  </div>

                  <div class="meta-right">
                    <button 
                      v-if="ev.code" 
                      class="quick-action-btn"
                      title="打开该标的 7 级协同流水线"
                      @click.stop="goToWorkflow(ev.code)"
                    >
                      流水线 ↗
                    </button>
                  </div>
                </div>

                <!-- 标的与核心研判内容行 -->
                <div class="feed-content">
                  <span 
                    class="feed-target"
                    :class="{ clickable: !!ev.code }"
                    :title="ev.code ? '点击立即前往个股研判: ' + ev.stock : ''"
                    @click.stop="ev.code && goToStock(ev.code)"
                  >
                    {{ ev.stock }}
                  </span>
                  <span class="feed-text">{{ ev.msg }}</span>
                </div>

                <!-- 可折叠/展开的深度证据链 -->
                <div class="feed-detail-section" v-if="ev.detail">
                  <button 
                    class="toggle-detail-btn"
                    @click.stop="toggleDetail(ev.id || idx)"
                  >
                    {{ expandedDetails[ev.id || idx] ? '收起证据链 ▴' : '展开推理依据 ▾' }}
                  </button>
                  <transition name="fade">
                    <div v-if="expandedDetails[ev.id || idx]" class="feed-detail-box">
                      <div class="detail-label">智能体协同证据链:</div>
                      <div class="detail-body">{{ ev.detail }}</div>
                    </div>
                  </transition>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="feed-filter-empty">
              <span class="empty-icon">🔍</span>
              <span>当前分类下暂无协同事件</span>
              <button class="reset-filter-btn" @click="currentEventFilter = 'all'">查看全部事件</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, RefreshRight } from '@element-plus/icons-vue'
import PipelineBanner from '@/components/Terminal/PipelineBanner.vue'
import MarketTrendChart from '@/components/Terminal/MarketTrendChart.vue'
import { stocksApi } from '@/api/stocks'

const router = useRouter()

function goToStock(code?: string) {
  if (!code) return
  router.push({ path: '/terminal/stock', query: { code } })
}

function goToWorkflow(code?: string) {
  if (code) {
    router.push({ path: '/terminal/workflow', query: { code } })
  } else {
    router.push('/terminal/workflow')
  }
}

// 顶部 5 大宏观 KPI 响应式对象
const kpis = ref({
  sentiment_score: 64.5,
  sentiment_status: '震荡偏强',
  sentiment_momentum: '+3.2 pt',
  up_count: 3214,
  down_count: 1842,
  flat_count: 120,
  limit_up: 68,
  limit_down: 4,
  total_amount_yi: 20800,
  total_amount_desc: '2.08 万亿',
  amount_change_desc: '+1,420 亿 (+7.3%)',
  total_stocks: 5564,
  pool_count: 126,
  pool_rate: '2.6%',
  running_tasks: 0,
  completed_tasks: 0,
  failed_tasks: 0
})

// 行业板块列表（真实动态数据）
const industryList = ref([
  { name: '半导体与芯片', change: 3.82, flow: 42.6, leader: '中芯国际 (+4.8%)', leaderCode: '688981', score: 94 },
  { name: '光通信/光模块', change: 3.15, flow: 28.3, leader: '中际旭创 (+5.2%)', leaderCode: '300308', score: 91 },
  { name: '算力与服务器', change: 2.78, flow: 21.5, leader: '浪潮信息 (+3.9%)', leaderCode: '000977', score: 88 },
  { name: '人形机器人', change: 2.45, flow: 15.2, leader: '绿的谐波 (+4.1%)', leaderCode: '688017', score: 86 },
  { name: '电力电网设备', change: 1.20, flow: 8.4, leader: '国电南瑞 (+1.6%)', leaderCode: '600406', score: 79 },
  { name: '白酒与食品饮料', change: -1.12, flow: -18.6, leader: '贵州茅台 (-0.9%)', leaderCode: '600519', score: 58 },
  { name: '煤炭与开采', change: -1.45, flow: -12.1, leader: '中国神华 (-1.3%)', leaderCode: '601088', score: 52 },
])

// 量化重点进攻主线
const themeList = ref([
  {
    name: '先进封测与先进制程国产化',
    score: 94,
    logic: '大基金三期扩容带动核心晶圆厂产能利用率由 76% 攀升至 88%，上游设备与材料景气度持续处于上行通道。',
    stocks: [
      { name: '中芯国际', code: '688981' },
      { name: '北方华创', code: '002371' },
      { name: '中微公司', code: '688012' },
      { name: '拓荆科技', code: '688072' }
    ]
  },
  {
    name: 'AI 数据中心超算与高速光互联',
    score: 91,
    logic: '全球 1.6T 光模块批量出货加速，头部通信硬件厂商 Q3 订单饱满，供应链具备极强盈利弹性。',
    stocks: [
      { name: '中际旭创', code: '300308' },
      { name: '新易盛', code: '300502' },
      { name: '天孚通信', code: '300394' }
    ]
  },
  {
    name: '具身智能与机器人核心零组件',
    score: 86,
    logic: '特斯拉与国内主机厂供应链定点逐步清晰，高精度减速器及六维力传感器出货量呈现倍增势头。',
    stocks: [
      { name: '绿的谐波', code: '688017' },
      { name: '三花智控', code: '002050' },
      { name: '鸣志电器', code: '603728' }
    ]
  }
])

// 实时智能体协同研判流接口与响应式状态
interface LiveAgentEvent {
  id?: string
  timestamp?: number
  time: string
  relativeTime?: string
  agent: string
  agentName?: string
  badgeClass: string
  eventType?: string
  stock: string
  stockName?: string
  code?: string
  score?: number
  action?: string
  actionType?: 'buy' | 'warn' | 'bull' | 'info'
  msg: string
  detail?: string
}

const liveEvents = ref<LiveAgentEvent[]>([
  {
    time: '10:28:40',
    relativeTime: '刚刚',
    agent: 'Decision Engine',
    agentName: '决策仲裁引擎',
    badgeClass: 'badge-decision',
    eventType: '裁决达成',
    stock: '洛轴股份 (301699)',
    code: '301699',
    score: 90,
    action: '强烈推荐',
    actionType: 'buy',
    msg: '综合裁决达成：风电设备龙头共振，量化得分 90，建议配置仓位 15%-20%，案卷归档',
    detail: '多空辩论阶段多方论据占优达 86%，基本面高景气与技术放量双轮驱动，风控回撤压力测试通过。'
  },
  {
    time: '10:26:20',
    relativeTime: '2m前',
    agent: 'Risk Agent',
    agentName: '风险审计',
    badgeClass: 'badge-risk',
    eventType: '风控核验',
    stock: '华茂股份 (000850)',
    code: '000850',
    score: 76,
    action: '防守预警',
    actionType: 'warn',
    msg: '风险审查完成：静态估值处于近三年合理分位，测算动态防守止损位，单票敞口上限控制在 15%',
    detail: '最大回撤预期测算在 3.6% 以内，商誉减值与解禁减持排查完毕，建议严格设动态防守点位。'
  },
  {
    time: '10:23:10',
    relativeTime: '5m前',
    agent: 'Tech Agent',
    agentName: '技术形态量化',
    badgeClass: 'badge-tech',
    eventType: '形态突破',
    stock: '科德教育 (300192)',
    code: '300192',
    score: 84,
    action: '放量共振',
    actionType: 'bull',
    msg: '技术形态共振：放量突破 60 日均线压制与前期平台箱体，MACD 零轴上方二次金叉成立',
    detail: '日线成交量较5日均量放大 1.5 倍，呈现典型主升浪放量推升结构，短期动量信号强烈。'
  },
  {
    time: '10:19:00',
    relativeTime: '9m前',
    agent: 'Fund Agent',
    agentName: '基本面产业',
    badgeClass: 'badge-fund',
    eventType: '业绩催化',
    stock: '华帝股份 (002035)',
    code: '002035',
    score: 89,
    action: '景气上行',
    actionType: 'bull',
    msg: '产业链景气验证：下游头部企业招标需求释放，Q3 盈利预期上调，核心竞争壁垒稳固',
    detail: '在手订单覆盖倍数达 1.7x，产能利用率攀升至 86%，行业处于新一轮资本开支上行周期。'
  },
  {
    time: '10:14:00',
    relativeTime: '14m前',
    agent: 'Macro Agent',
    agentName: '宏观与政策雷达',
    badgeClass: 'badge-macro',
    eventType: '政策催化',
    stock: '风电设备产业链',
    code: '',
    score: 85,
    action: '政策红利',
    actionType: 'bull',
    msg: '风电设备迎顶层产业支持政策落地，多部委协同推进高质量发展与技术迭代',
    detail: '财政贴息与专项产业基金双向扶持，产业链投资回报率与资本开支预期显著提振。'
  },
  {
    time: '10:05:00',
    relativeTime: '23m前',
    agent: 'Quant Engine',
    agentName: '量化因子引擎',
    badgeClass: 'badge-quant',
    eventType: '因子跑批',
    stock: 'A股全市场',
    code: '',
    score: 95,
    action: '全域扫描',
    actionType: 'info',
    msg: '全市场 5,564 只标的多因子动态打分跑批完成，多维共振初筛池精炼至 126 只',
    detail: '动量因子、波动率因子、量价反转与资金流向四维对齐，初筛合格率 2.6%。'
  }
])

const currentEventFilter = ref('all')
const expandedDetails = ref<Record<string | number, boolean>>({})
const isRefreshing = ref(false)

const eventFilterTabs = [
  { key: 'all', label: '全部' },
  { key: 'decision', label: '裁决' },
  { key: 'risk', label: '风控' },
  { key: 'tech', label: '形态' },
  { key: 'fund', label: '基本面' },
  { key: 'macro', label: '宏观' },
  { key: 'quant', label: '量化' }
]

function getTabCount(key: string) {
  if (key === 'all') return liveEvents.value.length
  return liveEvents.value.filter(e => {
    const ag = (e.agent || '').toLowerCase()
    if (key === 'decision') return ag.includes('decision')
    if (key === 'risk') return ag.includes('risk')
    if (key === 'tech') return ag.includes('tech')
    if (key === 'fund') return ag.includes('fund')
    if (key === 'macro') return ag.includes('macro')
    if (key === 'quant') return ag.includes('quant')
    return false
  }).length
}

const filteredEvents = computed(() => {
  let list = liveEvents.value
  if (currentEventFilter.value !== 'all') {
    list = list.filter(e => {
      const ag = (e.agent || '').toLowerCase()
      if (currentEventFilter.value === 'decision') return ag.includes('decision')
      if (currentEventFilter.value === 'risk') return ag.includes('risk')
      if (currentEventFilter.value === 'tech') return ag.includes('tech')
      if (currentEventFilter.value === 'fund') return ag.includes('fund')
      if (currentEventFilter.value === 'macro') return ag.includes('macro')
      if (currentEventFilter.value === 'quant') return ag.includes('quant')
      return true
    })
  }

  // 严格按时间倒序排列：最新的在最上方
  return [...list].sort((a, b) => {
    const tsA = a.timestamp || 0
    const tsB = b.timestamp || 0
    if (tsA && tsB && tsA !== tsB) return tsB - tsA
    return (b.time || '').localeCompare(a.time || '')
  })
})

function toggleDetail(idOrIdx: string | number) {
  expandedDetails.value[idOrIdx] = !expandedDetails.value[idOrIdx]
}

async function refreshEvents() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await fetchOverviewData(true)
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 600)
  }
}

const lastUpdateTime = ref('10:15:30')

interface CycleInfo {
  current_cycle?: string
  phase_name?: string
  phase_desc?: string
  next_refresh?: string
  cycle_interval_minutes?: number
}

const cycleInfo = ref<CycleInfo>({})

const cycleBadgeText = computed(() => {
  if (cycleInfo.value?.current_cycle && cycleInfo.value?.phase_name) {
    return `${cycleInfo.value.current_cycle} · ${cycleInfo.value.phase_name}`
  }
  return '半小时量化推演轮转'
})

const cycleTooltip = computed(() => {
  if (cycleInfo.value?.phase_name) {
    return `当前阶段【${cycleInfo.value.phase_name}】：${cycleInfo.value.phase_desc || ''}（每 30 分钟量化推演轮转，下次轮换: ${cycleInfo.value.next_refresh || '--:--'}，支持手动即刻强刷）`
  }
  return '智能体协同事件流每 30 分钟深度轮转推演一次，支持随时点击右侧按钮即刻强刷'
})

// 从真实后台 API 获取市场总览全景数据
async function fetchOverviewData(force = false) {
  try {
    const res = await stocksApi.getMarketOverview(force)
    const data = (res as any)?.data || (res as any)
    if (data && data.kpis) {
      kpis.value = { ...kpis.value, ...data.kpis }
      if (Array.isArray(data.sectors) && data.sectors.length > 0) {
        industryList.value = data.sectors
      }
      if (Array.isArray(data.themes) && data.themes.length > 0) {
        themeList.value = data.themes
      }
      if (Array.isArray(data.events) && data.events.length > 0) {
        liveEvents.value = data.events
      }
      if (data.cycle_info) {
        cycleInfo.value = data.cycle_info
      }
      if (data.updated_at) {
        lastUpdateTime.value = data.updated_at
      }
    }
  } catch (err) {
    console.error('获取市场总览实时数据失败:', err)
  }
}

let refreshTimer: number | null = null

onMounted(() => {
  fetchOverviewData()
  // 30 秒静默轮询平滑刷新最新市场数据
  refreshTimer = window.setInterval(() => {
    fetchOverviewData(false)
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped lang="scss">
.overview-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1600px;
  margin: 0 auto;
}

.kpi-banner {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.kpi-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.15s ease;

  &.clickable {
    cursor: pointer;
    &:hover {
      border-color: #175cd3;
      box-shadow: 0 2px 8px rgba(23, 92, 211, 0.08);
      .arrow-icon {
        transform: translateX(3px);
        color: #175cd3;
      }
    }
  }

  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .kpi-title {
      font-size: 11px;
      font-weight: 600;
      color: #667085;
    }

    .arrow-icon {
      font-size: 13px;
      color: #98a2b3;
      transition: transform 0.15s ease;
    }

    .kpi-tag {
      font-size: 10px;
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 3px;
      background-color: #f2f4f7;
      color: #344054;

      &.status-bull {
        background-color: #fef3f2;
        color: #d92d20;
      }
      &.status-bear {
        background-color: #edfcf2;
        color: #039855;
      }
    }
  }

  .kpi-val {
    font-size: 20px;
    font-weight: 700;
    color: #101828;
    margin: 6px 0 4px 0;
    line-height: 1.2;

    .sub-val {
      font-size: 11px;
      font-weight: 500;
      color: #667085;
    }

    .up-count { color: #d92d20; }
    .down-count { color: #039855; }
    .mid-slash { color: #d0d5dd; margin: 0 4px; font-weight: 400; }
  }

  .kpi-sub {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #475467;

    .trend-up {
      color: #d92d20;
      font-weight: 600;
    }
    .trend-down {
      color: #039855;
      font-weight: 600;
    }
    .neutral {
      color: #667085;
    }
    .highlight {
      color: #175cd3;
      font-weight: 600;
    }
  }
}

.pipeline-section {
  width: 100%;
}

.main-dashboard-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 16px;
  align-items: flex-start;
}

.grid-left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sectors-card, .themes-card, .feed-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eaecf0;
  background-color: #fafbfc;

  .header-left {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .header-title {
    font-size: 13px;
    font-weight: 700;
    color: #101828;
  }

  .header-sub {
    font-size: 11px;
    color: #667085;
  }

  .time-tip {
    font-size: 11px;
    color: #98a2b3;
  }

  .badge-blue {
    font-size: 11px;
    font-weight: 600;
    color: #175cd3;
    background-color: #eff8ff;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .text-btn {
    border: none;
    background: transparent;
    color: #175cd3;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    &:hover {
      text-decoration: underline;
    }
  }
}

.sectors-table-wrapper {
  overflow-x: auto;
}

.sectors-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;

  th {
    padding: 8px 16px;
    background-color: #f8fafc;
    color: #475467;
    font-weight: 600;
    border-bottom: 1px solid #eaecf0;
    font-size: 11px;
  }

  td {
    padding: 9px 16px;
    border-bottom: 1px solid #f2f4f7;
    color: #101828;
  }

  tbody tr:hover {
    background-color: #f8fafc;
  }

  .text-left { text-align: left; }
  .text-right { text-align: right; }
  .fw-semibold { font-weight: 600; }
  .fw-bold { font-weight: 700; }

  .color-up { color: #d92d20; font-weight: 600; }
  .color-down { color: #039855; font-weight: 600; }

  .leader-badge {
    color: #344054;
    font-size: 11px;
    background-color: #f2f4f7;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid transparent;

    &.clickable {
      cursor: pointer;
      transition: all 0.15s ease;
      &:hover {
        background-color: #eff8ff;
        color: #175cd3;
        border-color: #b2ddff;
      }
    }
  }

  .score-pill {
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 11px;
    &.high {
      background-color: #fef3f2;
      color: #d92d20;
    }
    &.medium {
      background-color: #eff8ff;
      color: #175cd3;
    }
  }
}

.grid-right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.theme-items {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.theme-empty {
  padding: 24px 16px;
  text-align: center;
  color: #667085;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;

  .empty-icon {
    font-size: 22px;
  }
}

.theme-item {
  border: 1px solid #eaecf0;
  border-radius: 5px;
  padding: 10px 12px;
  background-color: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    border-color: #175cd3;
    background-color: #f8fafc;
  }

  .theme-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;

    .theme-name {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }

    .theme-score {
      font-size: 11px;
      font-weight: 700;
      color: #175cd3;
      background-color: #eff8ff;
      padding: 1px 6px;
      border-radius: 3px;
    }
  }

  .theme-logic {
    font-size: 11px;
    color: #475467;
    line-height: 1.45;
    margin: 0 0 6px 0;
  }

  .theme-stocks {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;

    .stocks-label {
      color: #98a2b3;
    }

    .stock-pill {
      background-color: #f2f4f7;
      color: #344054;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 500;
      border: 1px solid transparent;

      &.clickable {
        cursor: pointer;
        transition: all 0.15s ease;
        &:hover {
          background-color: #eff8ff;
          color: #175cd3;
          border-color: #b2ddff;
        }
      }
    }
  }
}

.feed-header-left {
  display: flex;
  align-items: center;
  gap: 10px;

  .pulse-indicator {
    width: 8px;
    height: 8px;
    background-color: #12b76a;
    border-radius: 50%;
    animation: pulse 1.8s infinite;
    flex-shrink: 0;
  }

  .header-titles {
    display: flex;
    flex-direction: column;
    gap: 1px;

    .header-title {
      font-size: 13px;
      font-weight: 700;
      color: #101828;
      line-height: 1.2;
    }

    .header-sub {
      font-size: 10px;
      color: #98a2b3;
      font-family: monospace;
      letter-spacing: 0.2px;
    }
  }

  .online-tag {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 10px;
    background-color: #ecfdf3;
    color: #027a48;
    border: 1px solid #abefc6;
    letter-spacing: 0.1px;
    display: inline-flex;
    align-items: center;
  }
}

.feed-header-right {
  display: flex;
  align-items: center;
  gap: 8px;

  .icon-refresh-btn {
    background: transparent;
    border: 1px solid #eaecf0;
    border-radius: 4px;
    padding: 3px 6px;
    cursor: pointer;
    color: #667085;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    transition: all 0.15s ease;

    &:hover {
      color: #175cd3;
      border-color: #b2ddff;
      background: #eff8ff;
    }

    &.spinning {
      animation: spin 0.8s linear infinite;
    }
  }
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.feed-filter-bar {
  display: flex;
  gap: 5px;
  padding: 8px 14px;
  background-color: #fafbfc;
  border-bottom: 1px solid #eaecf0;
  overflow-x: auto;
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }

  .filter-pill-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 12px;
    border: 1px solid #e4e7ec;
    background-color: #ffffff;
    color: #475467;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;

    .tab-count {
      font-size: 10px;
      padding: 0 4px;
      border-radius: 8px;
      background-color: #f2f4f7;
      color: #667085;
      font-variant-numeric: tabular-nums;
    }

    &:hover {
      border-color: #b2ddff;
      color: #175cd3;
      background-color: #eff8ff;
    }

    &.active {
      background-color: #175cd3;
      border-color: #175cd3;
      color: #ffffff;

      .tab-count {
        background-color: rgba(255, 255, 255, 0.25);
        color: #ffffff;
      }
    }
  }
}

.feed-list-container {
  max-height: 480px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #eaecf0 transparent;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: #d0d5dd;
    border-radius: 2px;
  }
}

.feed-list {
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feed-item {
  border-left: 3px solid #d0d5dd;
  background-color: #ffffff;
  padding: 8px 10px;
  border-radius: 0 5px 5px 0;
  border-top: 1px solid #f2f4f7;
  border-right: 1px solid #f2f4f7;
  border-bottom: 1px solid #f2f4f7;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 5px;

  &:hover {
    background-color: #f8fafc;
    border-color: #e4e7ec;
    box-shadow: 0 1px 4px rgba(16, 24, 40, 0.04);
  }

  &.badge-decision { border-left-color: #d92d20; }
  &.badge-risk { border-left-color: #f79009; }
  &.badge-tech { border-left-color: #7a5af8; }
  &.badge-fund { border-left-color: #0ba5ec; }
  &.badge-macro { border-left-color: #6172f3; }
  &.badge-quant { border-left-color: #175cd3; }

  .feed-item-top {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .meta-left {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .feed-time-badge {
      color: #98a2b3;
      font-family: monospace;
      font-size: 10px;
      background-color: #f8fafc;
      padding: 1px 4px;
      border-radius: 3px;
    }

    .feed-badge {
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 700;
      flex-shrink: 0;

      &.badge-decision { background-color: #fef3f2; color: #d92d20; }
      &.badge-risk { background-color: #fffaeb; color: #b54708; }
      &.badge-fund { background-color: #f0f9ff; color: #026aa2; }
      &.badge-tech { background-color: #f9f5ff; color: #6941c6; }
      &.badge-macro { background-color: #eef4ff; color: #3538cd; }
      &.badge-quant { background-color: #eff8ff; color: #175cd3; }
    }

    .event-type-badge {
      font-size: 10px;
      color: #475467;
      background-color: #f2f4f7;
      padding: 1px 5px;
      border-radius: 2px;
      font-weight: 500;
    }

    .action-pill {
      font-size: 10px;
      font-weight: 600;
      padding: 1px 5px;
      border-radius: 2px;

      &.buy {
        background-color: #fef3f2;
        color: #b42318;
        border: 1px solid #fee4e2;
      }
      &.warn {
        background-color: #fffaeb;
        color: #b54708;
        border: 1px solid #fedf89;
      }
      &.bull {
        background-color: #eff8ff;
        color: #175cd3;
        border: 1px solid #b2ddff;
      }
      &.info {
        background-color: #f8fafc;
        color: #475467;
        border: 1px solid #eaecf0;
      }

      .score-num {
        font-weight: 700;
      }
    }

    .meta-right {
      .quick-action-btn {
        background: transparent;
        border: none;
        color: #175cd3;
        font-size: 10px;
        font-weight: 600;
        cursor: pointer;
        padding: 1px 5px;
        border-radius: 3px;
        transition: background 0.15s ease;
        &:hover {
          background-color: #eff8ff;
          text-decoration: underline;
        }
      }
    }
  }

  .feed-content {
    font-size: 11px;
    line-height: 1.48;
    color: #344054;

    .feed-target {
      font-weight: 700;
      color: #101828;
      margin-right: 6px;

      &.clickable {
        cursor: pointer;
        color: #175cd3;
        transition: color 0.15s ease;
        &:hover {
          color: #154cbd;
          text-decoration: underline;
        }
      }
    }

    .feed-text {
      color: #344054;
    }
  }

  .feed-detail-section {
    margin-top: 2px;

    .toggle-detail-btn {
      background: transparent;
      border: none;
      color: #667085;
      font-size: 10px;
      cursor: pointer;
      padding: 0;
      display: inline-flex;
      align-items: center;
      gap: 2px;
      transition: color 0.15s ease;

      &:hover {
        color: #175cd3;
      }
    }

    .feed-detail-box {
      margin-top: 4px;
      background-color: #f8fafc;
      border: 1px dashed #d0d5dd;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 10.5px;
      color: #475467;
      line-height: 1.45;

      .detail-label {
        font-weight: 600;
        color: #344054;
        margin-bottom: 2px;
      }
      .detail-body {
        color: #475467;
      }
    }
  }
}

.feed-filter-empty {
  padding: 28px 16px;
  text-align: center;
  color: #667085;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;

  .empty-icon {
    font-size: 20px;
  }

  .reset-filter-btn {
    margin-top: 4px;
    background: #eff8ff;
    border: 1px solid #b2ddff;
    color: #175cd3;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: background 0.15s ease;
    &:hover {
      background: #d1e9ff;
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1280px) {
  .kpi-banner {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1100px) {
  .main-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .kpi-banner {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .kpi-banner {
    grid-template-columns: 1fr;
  }
}
</style>
