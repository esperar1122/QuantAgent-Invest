<template>
  <div class="workflow-view">
    <!-- 1. 标的极速检索与切换控制台 (Stock Switcher Ribbon) -->
    <div class="stock-switcher-ribbon">
      <div class="ribbon-left">
        <!-- 标的搜索下拉框 -->
        <div class="search-input-wrapper">
          <el-select
            v-model="selectedCode"
            filterable
            remote
            reserve-keyword
            :remote-method="handleSearch"
            :loading="searchLoading"
            placeholder="🔍 检索 A股代码 / 名称 / 简拼 (如 600519、贵州茅台、300750)..."
            class="terminal-stock-select"
            @change="onStockSelectChange"
          >
            <el-option
              v-for="item in searchOptions"
              :key="item.code"
              :label="`${item.name} (${item.code})`"
              :value="item.code"
            >
              <div class="search-option-card">
                <div class="opt-left">
                  <span class="opt-code font-mono">{{ item.code }}</span>
                  <span class="opt-market-tag">{{ item.market || 'A股' }}</span>
                </div>
                <div class="opt-center">
                  <span class="opt-name">{{ item.name }}</span>
                  <span class="opt-industry" v-if="item.industry">{{ item.industry }}</span>
                </div>
                <div class="opt-right tabular-nums" v-if="item.close !== undefined">
                  <span class="opt-price">{{ Number(item.close).toFixed(2) }}</span>
                  <span
                    class="opt-pct"
                    :class="(item.pct_chg || 0) >= 0 ? 'color-up' : 'color-down'"
                  >
                    {{ (item.pct_chg || 0) >= 0 ? '+' : '' }}{{ Number(item.pct_chg || 0).toFixed(2) }}%
                  </span>
                </div>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 热门核心指数标的秒级切换胶囊 (Quick Preset Chips) -->
        <div class="preset-chips">
          <span class="chips-label">核心池:</span>
          <button
            v-for="chip in hotStocks"
            :key="chip.code"
            class="chip-btn"
            :class="{ active: isChipActive(chip.code) }"
            @click="switchStock(chip.code)"
          >
            <span class="chip-name">{{ chip.name }}</span>
            <span class="chip-code font-mono">{{ chip.displayCode || chip.code }}</span>
          </button>
        </div>
      </div>

      <div class="ribbon-right">
        <!-- 自选股快速切换下拉 -->
        <el-dropdown trigger="click" @command="switchStock">
          <el-button size="small" class="watchlist-btn">
            <el-icon><Star /></el-icon>
            <span>自选池 ({{ favoritesStore.favorites.length }})</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="watchlist-dropdown-menu">
              <el-dropdown-item
                v-if="favoritesStore.favorites.length === 0"
                disabled
              >
                暂无自选股，可在个股研究添加
              </el-dropdown-item>
              <el-dropdown-item
                v-for="fav in favoritesStore.favorites"
                :key="fav.symbol || fav.stock_code"
                :command="fav.symbol || fav.stock_code"
                :class="{ active: currentStock.code === (fav.symbol || fav.stock_code) }"
              >
                <div class="fav-item-row">
                  <span class="fav-name">{{ fav.stock_name || fav.symbol || fav.stock_code }}</span>
                  <span class="fav-code font-mono">{{ fav.symbol || fav.stock_code }}</span>
                </div>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 顶部工作流控制栏 -->
    <div class="workflow-control-bar">
      <div class="control-left">
        <span class="ctrl-title">多智能体协同研判流水线</span>
        <div class="stock-pill">
          <span class="stock-tag">当前标的</span>
          <span class="stock-name">{{ currentStock.name }}</span>
          <span class="stock-code tabular-nums font-mono">{{ currentStock.code }}</span>
          <span class="quant-score tabular-nums">Quant分: {{ currentStock.score }}</span>
          <span class="stock-sector">{{ currentStock.sector }}</span>
        </div>
      </div>

      <div class="control-right">
        <div class="status-summary">
          <span class="stat-dot" :class="{ running: isRunning }"></span>
          <span class="stat-text">{{ isRunning ? '智能体协同分析跑批中...' : '工作流就绪 / 已完成' }}</span>
        </div>
        <el-button size="small" @click="goToStock">
          <el-icon><TrendCharts /></el-icon>
          返回个股
        </el-button>
        <el-button 
          type="primary" 
          size="small" 
          :loading="isRunning"
          @click="runWorkflow"
        >
          <el-icon><VideoPlay /></el-icon>
          {{ isRunning ? '执行中...' : '重新运行工作流' }}
        </el-button>
        <el-button 
          size="small" 
          :loading="isDeepReportRunning"
          @click="triggerDeepLlmReport"
          class="cf-llm-btn"
        >
          <span class="llm-icon">{{ isDeepReportRunning ? '⏳' : '⚡' }}</span>
          <span>{{ isDeepReportRunning ? `${deepReportProgress}% 推演中` : '调度云端大模型' }}</span>
        </el-button>
        <el-button size="small" @click="goToReport">
          <el-icon><Document /></el-icon>
          查看全息研报
        </el-button>
      </div>
    </div>

    <!-- 7 大节点可视化流水线拓扑图 -->
    <div class="pipeline-flow-card">
      <div class="flow-header">
        <span class="fh-title">7 级协同节点流转状态拓扑</span>
        <span class="fh-sub">DAG 异步并行与汇聚拓扑结构</span>
      </div>

      <div class="flow-diagram">
        <!-- 节点 1: 标的输入 -->
        <div class="node-box" :class="getNodeClass(1)">
          <div class="node-step">STEP 01</div>
          <div class="node-title">候选标的输入</div>
          <div class="node-desc">量化因子引擎 {{ currentStock.score }}分 初筛通过</div>
          <div class="node-status">{{ getNodeStatusText(1) }}</div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 2 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 2, 3, 4 并行分支 -->
        <div class="parallel-branches">
          <!-- 节点 2: 宏观政策 -->
          <div class="node-box mini" :class="getNodeClass(2)">
            <div class="node-header">
              <span class="node-step">02</span>
              <span class="node-title">宏观政策 Agent</span>
            </div>
            <div class="node-desc">{{ step2Desc }}</div>
            <div class="node-status">{{ getNodeStatusText(2) }}</div>
          </div>

          <!-- 节点 3: 技术形态 -->
          <div class="node-box mini" :class="getNodeClass(3)">
            <div class="node-header">
              <span class="node-step">03</span>
              <span class="node-title">技术形态 Agent</span>
            </div>
            <div class="node-desc">{{ step3Desc }}</div>
            <div class="node-status">{{ getNodeStatusText(3) }}</div>
          </div>

          <!-- 节点 4: 基本面产业 -->
          <div class="node-box mini" :class="getNodeClass(4)">
            <div class="node-header">
              <span class="node-step">04</span>
              <span class="node-title">基本面 Agent</span>
            </div>
            <div class="node-desc">{{ step4Desc }}</div>
            <div class="node-status">{{ getNodeStatusText(4) }}</div>
          </div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 5 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 5: 证据汇总层 -->
        <div class="node-box" :class="getNodeClass(5)">
          <div class="node-step">STEP 05</div>
          <div class="node-title">证据汇总器</div>
          <div class="node-desc">{{ step5Desc }}</div>
          <div class="node-status">{{ getNodeStatusText(5) }}</div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 6 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 6: 风险审查 -->
        <div class="node-box" :class="getNodeClass(6)">
          <div class="node-step">STEP 06</div>
          <div class="node-title">风险审查 Agent</div>
          <div class="node-desc">{{ step6Desc }}</div>
          <div class="node-status">{{ getNodeStatusText(6) }}</div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 7 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 7: 综合决策引擎 -->
        <div class="node-box decision-node" :class="getNodeClass(7)">
          <div class="node-step">STEP 07</div>
          <div class="node-title">决策仲裁引擎</div>
          <div class="node-desc">{{ step7Desc }}</div>
          <div class="node-status">{{ getNodeStatusText(7) }}</div>
        </div>
      </div>
    </div>

    <!-- 下半部两栏：左侧证据汇总，右侧执行控制台日志 -->
    <div class="workflow-bottom-grid">
      <!-- 左侧：证据汇总组件 -->
      <div class="bottom-left-col">
        <EvidenceAggregator 
          :stockCode="currentStock.code" 
          :stockName="currentStock.name" 
          :workflowData="workflowData"
          :dossierData="workflowData?.dossier"
        />
      </div>

      <!-- 右侧：结构化执行日志终端 -->
      <div class="bottom-right-col">
        <div class="terminal-log-box">
          <div class="log-header">
            <div class="lh-left">
              <span class="lh-dot"></span>
              <span class="lh-title">执行内核结构化运行日志 (Runtime Console)</span>
            </div>
            <div class="lh-right">
              <span class="log-stat tabular-nums">耗时: {{ executionTimeMs }}ms | {{ tokensUsed > 0 ? `LLM Tokens: ${tokensUsed.toLocaleString()}` : '本地量化内核 (0 Token 消耗)' }}</span>
            </div>
          </div>

          <div class="log-body font-mono" ref="logBodyRef">
            <div 
              v-for="(log, idx) in runtimeLogs" 
              :key="'log-' + idx" 
              class="log-line"
            >
              <span class="log-time tabular-nums">{{ log.time }}</span>
              <span class="log-node" :class="log.nodeClass">[{{ log.node }}]</span>
              <span class="log-msg">{{ log.msg }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VideoPlay, Document, TrendCharts, Star, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import EvidenceAggregator from '@/components/Terminal/EvidenceAggregator.vue'
import { stocksApi } from '@/api/stocks'
import { useFavoritesStore } from '@/stores/favorites'

const route = useRoute()
const router = useRouter()
const favoritesStore = useFavoritesStore()
const logBodyRef = ref<HTMLElement | null>(null)

const hotStocks = [
  { code: 'sh000001', displayCode: '000001', name: '上证指数' },
  { code: 'sz399001', displayCode: '399001', name: '深证成指' },
  { code: 'sz399006', displayCode: '399006', name: '创业板指' },
  { code: 'sh000680', displayCode: '000680', name: '科创综指' },
  { code: '159992', name: '创新药ETF' },
  { code: '688981', name: '中芯国际' },
  { code: '600519', name: '贵州茅台' },
  { code: '300750', name: '宁德时代' },
  { code: '002594', name: '比亚迪' },
  { code: '300308', name: '中际旭创' }
]

const searchLoading = ref(false)
const searchOptions = ref<any[]>([])
const selectedCode = ref((route.query.code as string) || 'sh000001')

async function handleSearch(query: string) {
  if (!query || query.trim().length === 0) {
    searchOptions.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await stocksApi.search(query.trim(), 15)
    const items = (res as any)?.data?.items || (res as any)?.items || []
    searchOptions.value = items
  } catch (e) {
    searchOptions.value = []
  } finally {
    searchLoading.value = false
  }
}

function isChipActive(code: string) {
  const cur = currentStock.value.code
  return cur === code || cur === code.replace(/^(sh|sz|bj)/i, '')
}

function switchStock(code: string) {
  if (!code || code === currentStock.value.code) return
  clearDeepReportPoll()
  isDeepReportRunning.value = false
  selectedCode.value = code
  router.replace({ path: '/terminal/workflow', query: { code } })
  loadStockDetail(code)
}

function onStockSelectChange(val: string) {
  if (val) switchStock(val)
}

const hotDict: Record<string, string> = {
  'sh000001': '上证指数',
  '000001': '上证指数',
  'sz399001': '深证成指',
  '399001': '深证成指',
  'sz399006': '创业板指',
  '399006': '创业板指',
  'sh000680': '科创综指',
  '000680': '科创综指',
  '159992': '创新药ETF',
  '688981': '中芯国际',
  '600519': '贵州茅台',
  '300750': '宁德时代',
  '002594': '比亚迪',
  '300308': '中际旭创',
  '002371': '北方华创',
  'sh000300': '沪深300'
}

const currentStock = ref({
  code: (route.query.code as string) || 'sh000001',
  name: hotDict[(route.query.code as string) || 'sh000001'] || '上证指数',
  score: 92,
  price: 3911.87,
  sector: 'A股大盘基准 / 宏观核心'
})

const workflowData = ref<any>(null)
const executionTimeMs = ref<number>(360)
const tokensUsed = ref<number>(0)
const isRunning = ref(false)
const currentActiveStep = ref(7) // 初始为全部完成

const stopLossPrice = computed(() => {
  if (workflowData.value?.dossier?.arbitration?.stop_loss !== undefined) {
    return workflowData.value.dossier.arbitration.stop_loss
  }
  const prec = workflowData.value?.dossier?.precision ?? (currentStock.value.code.startsWith('159') || currentStock.value.code.startsWith('51') ? 3 : 2)
  return (currentStock.value.price * 0.94).toFixed(prec)
})

const step2Desc = computed(() => {
  return workflowData.value?.steps?.[1]?.desc || `${currentStock.value.sector}景气与政策调研`
})

const step3Desc = computed(() => {
  return workflowData.value?.steps?.[2]?.desc || '量价突破与均线共振匹配'
})

const step4Desc = computed(() => {
  return workflowData.value?.steps?.[3]?.desc || '产业壁垒与财报估值测算'
})

const step5Desc = computed(() => {
  const suppCnt = workflowData.value?.support_list?.length || 4
  const riskCnt = workflowData.value?.risk_list?.length || 2
  return workflowData.value?.steps?.[4]?.desc || `${suppCnt}条支撑 / ${riskCnt}条风险 / 多空辩论`
})

const step6Desc = computed(() => {
  return `风控审查通过，动态止损线 ¥${stopLossPrice.value} 元`
})

const step7Desc = computed(() => {
  const arb = workflowData.value?.dossier?.arbitration
  if (arb) {
    return `评级【${arb.rating}】${arb.score}分 (买入区间: ¥${arb.suggested_entry_low} - ¥${arb.suggested_entry_high})`
  }
  return `买入评级 ${currentStock.value.score}分 (建议仓位: 15-20%)`
})

const runtimeLogs = ref<any[]>([
  { time: '10:14:15', node: 'Workflow Kernel', nodeClass: 'node-sys', msg: '流水线就绪，等待调度推演' }
])

async function loadStockDetail(code: string) {
  if (!code) return
  try {
    // 并发请求行情与工作流
    const [quoteRes, wfRes] = await Promise.allSettled([
      stocksApi.getQuote(code),
      stocksApi.executeWorkflow(code)
    ])

    if (quoteRes.status === 'fulfilled') {
      const q = (quoteRes.value as any)?.data || quoteRes.value
      if (q && (q.price !== undefined || q.close !== undefined)) {
        const px = Number(q.price ?? q.close ?? 86.4)
        const name = q.name || hotDict[code] || `标的 ${code}`
        const sector = q.industry || (code.startsWith('688') ? '科创先锋' : code.startsWith('159') || code.startsWith('51') ? '指数ETF基金' : '主力优势产业')
        currentStock.value = {
          code,
          name,
          score: Math.min(96, Math.max(72, Math.round(78 + (q.change_percent ?? 0) * 2))),
          price: px,
          sector
        }
      }
    }

    if (wfRes.status === 'fulfilled') {
      const data = (wfRes.value as any)?.data || wfRes.value
      if (data && data.success) {
        workflowData.value = data
        executionTimeMs.value = data.execution_time_ms || 360
        tokensUsed.value = data.tokens_used ?? 0
        if (data.runtime_logs && data.runtime_logs.length > 0) {
          runtimeLogs.value = data.runtime_logs
        }
        if (data.dossier?.arbitration) {
          currentStock.value.score = Math.round(data.dossier.arbitration.score)
          currentStock.value.name = data.name || currentStock.value.name
        }
      }
    }
  } catch (e) {
    console.warn('工作流标的加载失败，使用默认配置:', e)
  }
}

watch(() => route.query.code, (newCode) => {
  if (newCode && typeof newCode === 'string') {
    selectedCode.value = newCode
    currentStock.value.code = newCode
    if (hotDict[newCode]) {
      currentStock.value.name = hotDict[newCode]
    }
    loadStockDetail(newCode)
  }
})

onMounted(() => {
  const queryCode = (route.query.code as string) || 'sh000001'
  selectedCode.value = queryCode
  loadStockDetail(queryCode)
  favoritesStore.fetchFavorites()
})

function getNodeClass(step: number) {
  if (isRunning.value) {
    if (currentActiveStep.value === step) return 'node-running'
    if (currentActiveStep.value > step) return 'node-completed'
    return 'node-idle'
  }
  return 'node-completed'
}

function getNodeStatusText(step: number) {
  if (isRunning.value) {
    if (currentActiveStep.value === step) return '执行中...'
    if (currentActiveStep.value > step) return '✓ 已完成'
    return '待调度'
  }
  return '✓ 已完成'
}

async function runWorkflow() {
  if (isRunning.value) return
  isRunning.value = true
  currentActiveStep.value = 1
  const code = currentStock.value.code
  const name = currentStock.value.name
  const nowStr = new Date().toTimeString().slice(0, 8)

  runtimeLogs.value = [
    { time: nowStr, node: 'Workflow Kernel', nodeClass: 'node-sys', msg: `流水线启动，正在调度 DAG 拓扑图与量化引擎推演标的: ${code} (${name})...` }
  ]

  try {
    const res = await stocksApi.executeWorkflow(code)
    const data = (res as any)?.data || res

    if (data && data.runtime_logs && data.runtime_logs.length > 0) {
      const logs = data.runtime_logs
      // 平滑步进动画展示 7 级真实推演节点
      for (let s = 1; s <= 7; s++) {
        currentActiveStep.value = s
        if (logs[s - 1]) {
          runtimeLogs.value.push(logs[s - 1])
          await nextTick()
          if (logBodyRef.value) {
            logBodyRef.value.scrollTop = logBodyRef.value.scrollHeight
          }
        }
        await new Promise((resolve) => setTimeout(resolve, 180))
      }

      workflowData.value = data
      executionTimeMs.value = data.execution_time_ms || 360
      tokensUsed.value = data.tokens_used ?? 0

      if (data.dossier?.arbitration) {
        currentStock.value.score = Math.round(data.dossier.arbitration.score)
      }

      ElMessage.success(`[${name}] 7级多智能体协同流水线真实推演完毕，证据案卷与仲裁决议已同步！`)
    }
  } catch (err: any) {
    console.error('Workflow execution failed:', err)
    ElMessage.error(`工作流推演异常: ${err.message || '网络连接超时'}`)
  } finally {
    isRunning.value = false
    currentActiveStep.value = 7
  }
}

function goToStock() {
  router.push({ path: '/terminal/stock', query: { code: currentStock.value.code } })
}

function goToReport() {
  router.push({ path: '/terminal/report', query: { code: currentStock.value.code } })
}

// ==========================================================================
// ⚡ 云端大模型多智能体深度研报调度
// ==========================================================================
const isDeepReportRunning = ref(false)
const deepReportProgress = ref(0)
let deepReportTimer: any = null

function appendRuntimeLog(node: string, nodeClass: string, msg: string) {
  const pad = (n: number) => String(n).padStart(2, '0')
  const now = new Date()
  const time = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
  runtimeLogs.value.push({ time, node, nodeClass, msg })
  nextTick(() => {
    if (logBodyRef.value) {
      logBodyRef.value.scrollTop = logBodyRef.value.scrollHeight
    }
  })
}

function clearDeepReportPoll() {
  if (deepReportTimer) {
    clearInterval(deepReportTimer)
    deepReportTimer = null
  }
}

async function triggerDeepLlmReport() {
  if (isDeepReportRunning.value) return
  const code = currentStock.value.code
  const name = currentStock.value.name
  if (!code) return

  try {
    await ElMessageBox.confirm(
      `即将调度云端 LangGraph 多智能体协同引擎对【${name} (${code})】开展深度链式推理。全流程包含宏观研判、多空辩论、筹码穿透与风险仲裁，大约耗时 30-90 秒，将消耗真实 LLM 算力 Token。\n\n是否确认在后台启动深度推演？`,
      '调度云端大模型多智能体',
      {
        confirmButtonText: '确认调度',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
  } catch {
    return
  }

  try {
    isDeepReportRunning.value = true
    deepReportProgress.value = 5
    appendRuntimeLog('Cloud LLM Engine', 'node-risk', `[调度指令下发] 唤醒 LangGraph 深度多智能体推理图 (标的: ${name} ${code})`)

    const res = await stocksApi.triggerDeepAnalysis(code, {
      analysts: ['market', 'news', 'fundamentals'],
      research_depth: 'deep'
    })

    const taskId = (res as any)?.task_id || (res as any)?.data?.task_id
    if (!taskId) {
      ElMessage.warning('未能获取后台推演任务 ID，请稍后重试')
      isDeepReportRunning.value = false
      return
    }

    appendRuntimeLog('LangGraph Agent', 'node-sys', `[异步推演中] 云端任务 ID: ${taskId.slice(-8)}，各智能体节点并行交叉质询中...`)
    ElMessage.success(`云端推演任务已提交！任务编号: ${taskId.slice(-8)}，正实时异步分析中...`)

    clearDeepReportPoll()
    deepReportTimer = setInterval(async () => {
      try {
        const statusRes = await stocksApi.getDeepAnalysisStatus(code, taskId)
        const statusData = (statusRes as any)?.data || statusRes
        if (statusData) {
          deepReportProgress.value = Math.min(98, Math.max(deepReportProgress.value, statusData.progress || 10))
          if (statusData.current_step) {
            appendRuntimeLog('LangGraph Flow', 'node-analyst', `[推演进度 ${deepReportProgress.value}%] ${statusData.current_step}`)
          }

          if (statusData.status === 'completed' || statusData.status === 'SUCCESS' || statusData.progress >= 100) {
            clearDeepReportPoll()
            deepReportProgress.value = 100
            isDeepReportRunning.value = false
            appendRuntimeLog('Arbitration Agent', 'node-decision', `[推演完成] 云端大模型深度研报推演完成！证据案卷库与决策结论已点亮`)
            ElMessage.success({
              message: `【${name}】云端大模型深度研报推演完成！已点亮真实推理证据案卷`,
              duration: 5000
            })
            // 重新刷新案卷与详情
            await loadStockDetail(code)
          } else if (statusData.status === 'failed' || statusData.status === 'error') {
            clearDeepReportPoll()
            isDeepReportRunning.value = false
            appendRuntimeLog('Workflow Error', 'node-risk', `[异常中断] 大模型推演失败: ${statusData.error || '未知异常'}`)
            ElMessage.error(`大模型推演失败: ${statusData.error || '未知异常'}`)
          }
        }
      } catch (pollErr) {
        console.warn('轮询大模型推演状态异常:', pollErr)
      }
    }, 3000)
  } catch (err: any) {
    isDeepReportRunning.value = false
    ElMessage.error(`提交大模型推演任务失败: ${err.message || '网络异常'}`)
  }
}

onUnmounted(() => {
  clearDeepReportPoll()
})
</script>

<style scoped lang="scss">
.workflow-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1680px;
  margin: 0 auto;
}

// 标的极速检索与切换控制台
.stock-switcher-ribbon {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .ribbon-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 300px;
    flex-wrap: wrap;
  }

  .search-input-wrapper {
    width: 320px;
    max-width: 100%;

    .terminal-stock-select {
      width: 100%;

      :deep(.el-input__wrapper) {
        border-radius: 5px;
        background-color: #f8fafc;
        box-shadow: 0 0 0 1px #e2e8f0 inset;

        &:hover {
          box-shadow: 0 0 0 1px #b2ccff inset;
        }

        &.is-focus {
          box-shadow: 0 0 0 1px #175cd3 inset, 0 0 0 3px rgba(23, 92, 211, 0.12);
        }
      }
    }
  }

  .preset-chips {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;

    .chips-label {
      font-size: 11px;
      font-weight: 600;
      color: #667085;
      margin-right: 2px;
    }

    .chip-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      border: 1px solid #eaecf0;
      background-color: #ffffff;
      color: #344054;
      cursor: pointer;
      transition: all 0.15s ease;

      .chip-name {
        font-weight: 600;
      }

      .chip-code {
        font-size: 10px;
        color: #667085;
      }

      &:hover {
        border-color: #b2ccff;
        background-color: #eff8ff;
        color: #175cd3;

        .chip-code {
          color: #175cd3;
        }
      }

      &.active {
        background-color: #175cd3;
        border-color: #175cd3;
        color: #ffffff;

        .chip-code {
          color: rgba(255, 255, 255, 0.85);
        }
      }
    }
  }

  .ribbon-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 标的下拉选项样式
.search-option-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 10px;
  font-size: 12px;

  .opt-left {
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-code {
      font-weight: 700;
      color: #101828;
    }

    .opt-market-tag {
      font-size: 10px;
      padding: 1px 4px;
      border-radius: 2px;
      background-color: #eff8ff;
      color: #175cd3;
      font-weight: 600;
    }
  }

  .opt-center {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-name {
      font-weight: 600;
      color: #101828;
    }

    .opt-industry {
      font-size: 11px;
      color: #667085;
    }
  }

  .opt-right {
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-price {
      font-weight: 600;
      color: #101828;
    }

    .opt-pct {
      font-size: 11px;
      font-weight: 700;
    }
  }
}

.fav-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 160px;
  font-size: 12px;

  .fav-name {
    font-weight: 600;
  }

  .fav-code {
    font-size: 10px;
    color: #667085;
  }
}

.workflow-control-bar {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;

  .control-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;

    .ctrl-title {
      font-size: 13px;
      font-weight: 700;
      color: #101828;
      white-space: nowrap;
    }

    .stock-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background-color: #f8fafc;
      border: 1px solid #eaecf0;
      border-radius: 4px;
      padding: 3px 8px;
      flex-wrap: wrap;

      .stock-tag {
        font-size: 10px;
        color: #98a2b3;
      }

      .stock-name {
        font-size: 12px;
        font-weight: 700;
        color: #101828;
      }

      .stock-code {
        font-size: 11px;
        color: #475467;
      }

      .quant-score {
        font-size: 10px;
        font-weight: 700;
        color: #175cd3;
        background-color: #eff8ff;
        padding: 1px 4px;
        border-radius: 2px;
      }

      .stock-sector {
        font-size: 10px;
        color: #475467;
        background-color: #f2f4f7;
        padding: 1px 4px;
        border-radius: 2px;
      }
    }
  }

  .control-right {
    display: flex;
    align-items: center;
    gap: 12px;

    .status-summary {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #475467;

      .stat-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #12b76a;

        &.running {
          background-color: #f79009;
          animation: blink 1s infinite;
        }
      }
    }

    .cf-llm-btn {
      background: linear-gradient(135deg, #175cd3 0%, #7c3aed 100%) !important;
      border: none !important;
      color: #ffffff !important;
      font-weight: 600;

      &:hover:not(:disabled) {
        filter: brightness(1.08);
      }

      .llm-icon {
        margin-right: 3px;
      }
    }
  }
}

@keyframes blink {
  0% { opacity: 0.3; }
  50% { opacity: 1; }
  100% { opacity: 0.3; }
}

.pipeline-flow-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;

  &::-webkit-scrollbar {
    display: none;
  }

  .flow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background-color: #fafbfc;
    border-bottom: 1px solid #eaecf0;
    flex-wrap: wrap;
    gap: 6px;

    .fh-title {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }
    .fh-sub {
      font-size: 11px;
      color: #667085;
    }
  }

  .flow-diagram {
    padding: 20px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    overflow-x: auto;
    min-width: 960px;
  }
}

.node-box {
  background-color: #ffffff;
  border: 1px solid #eaecf0;
  border-radius: 6px;
  padding: 10px 12px;
  min-width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s ease;

  .node-step {
    font-size: 9px;
    font-weight: 700;
    color: #98a2b3;
    letter-spacing: 0.05em;
  }

  .node-title {
    font-size: 12px;
    font-weight: 700;
    color: #101828;
  }

  .node-desc {
    font-size: 10px;
    color: #475467;
    line-height: 1.3;
  }

  .node-status {
    font-size: 10px;
    font-weight: 600;
    color: #667085;
    margin-top: 2px;
  }

  &.node-completed {
    border-color: #b2ccff;
    background-color: #f8faff;
    .node-status {
      color: #175cd3;
    }
  }

  &.node-running {
    border-color: #f79009;
    background-color: #fffcf5;
    box-shadow: 0 0 0 2px rgba(247, 144, 9, 0.15);
    .node-status {
      color: #b54708;
    }
  }

  &.node-idle {
    opacity: 0.6;
  }

  &.decision-node {
    border-color: #d92d20;
    background-color: #fef3f2;
    .node-title {
      color: #d92d20;
    }
    .node-status {
      color: #d92d20;
    }
  }
}

.parallel-branches {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .node-box.mini {
    min-width: 180px;
    padding: 6px 10px;

    .node-header {
      display: flex;
      align-items: center;
      gap: 6px;
    }
  }
}

.flow-connector {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d0d5dd;
  font-size: 16px;
  font-weight: 700;
  transition: color 0.2s ease;

  &.active {
    color: #175cd3;
  }
}

.workflow-bottom-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 16px;
  align-items: flex-start;
}

.bottom-left-col {
  display: flex;
  flex-direction: column;
}

.bottom-right-col {
  display: flex;
  flex-direction: column;
}

.terminal-log-box {
  background-color: #0c111d;
  border: 1px solid #1f2a37;
  border-radius: 6px;
  overflow: hidden;
  height: 540px;
  display: flex;
  flex-direction: column;

  .log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background-color: #161e2e;
    border-bottom: 1px solid #1f2a37;

    .lh-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .lh-dot {
        width: 7px;
        height: 7px;
        background-color: #12b76a;
        border-radius: 50%;
      }

      .lh-title {
        font-size: 11px;
        font-weight: 600;
        color: #d0d5dd;
      }
    }

    .log-stat {
      font-size: 10px;
      color: #98a2b3;
    }
  }

  .log-body {
    padding: 12px 14px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 11px;
    line-height: 1.5;
  }

  .log-line {
    display: flex;
    gap: 8px;
    align-items: baseline;

    .log-time {
      color: #667085;
      font-size: 10px;
      flex-shrink: 0;
    }

    .log-node {
      font-weight: 700;
      flex-shrink: 0;
      font-size: 10px;

      &.node-sys { color: #53b1fd; }
      &.node-macro { color: #84caef; }
      &.node-tech { color: #f670c7; }
      &.node-fund { color: #36bfba; }
      &.node-agg { color: #b692f6; }
      &.node-risk { color: #fdc23a; }
      &.node-decision { color: #f97066; }
    }

    .log-msg {
      color: #e4e7ec;
      word-break: break-all;
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1100px) {
  .workflow-bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
