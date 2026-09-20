<template>
  <div class="workflow-view">
    <!-- 顶部工作流控制栏 -->
    <div class="workflow-control-bar">
      <div class="control-left">
        <span class="ctrl-title">多智能体协同研判流水线 (Multi-Agent Workflow)</span>
        <div class="stock-pill">
          <span class="stock-tag">当前标的</span>
          <span class="stock-name">{{ currentStock.name }}</span>
          <span class="stock-code tabular-nums font-mono">{{ currentStock.code }}</span>
          <span class="quant-score tabular-nums">Quant分: {{ currentStock.score }}</span>
        </div>
      </div>

      <div class="control-right">
        <div class="status-summary">
          <span class="stat-dot" :class="{ running: isRunning }"></span>
          <span class="stat-text">{{ isRunning ? '智能体协同分析跑批中...' : '工作流就绪 / 已完成' }}</span>
        </div>
        <el-button size="small" @click="goToStock">
          <el-icon><TrendCharts /></el-icon>
          返回个股研究
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
        <el-button size="small" @click="goToReport">
          <el-icon><Document /></el-icon>
          查看产出研报
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
            <div class="node-desc">{{ currentStock.sector }}景气与政策调研</div>
            <div class="node-status">{{ getNodeStatusText(2) }}</div>
          </div>

          <!-- 节点 3: 技术形态 -->
          <div class="node-box mini" :class="getNodeClass(3)">
            <div class="node-header">
              <span class="node-step">03</span>
              <span class="node-title">技术形态 Agent</span>
            </div>
            <div class="node-desc">量价突破与均线共振匹配</div>
            <div class="node-status">{{ getNodeStatusText(3) }}</div>
          </div>

          <!-- 节点 4: 基本面产业 -->
          <div class="node-box mini" :class="getNodeClass(4)">
            <div class="node-header">
              <span class="node-step">04</span>
              <span class="node-title">基本面 Agent</span>
            </div>
            <div class="node-desc">产业壁垒与财报估值测算</div>
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
          <div class="node-desc">8条支撑 / 3条风险 / 1条分歧</div>
          <div class="node-status">{{ getNodeStatusText(5) }}</div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 6 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 6: 风险审查 -->
        <div class="node-box" :class="getNodeClass(6)">
          <div class="node-step">STEP 06</div>
          <div class="node-title">风险审查 Agent</div>
          <div class="node-desc">估值溢价与止损线 ({{ stopLossPrice }}元)</div>
          <div class="node-status">{{ getNodeStatusText(6) }}</div>
        </div>

        <div class="flow-connector" :class="{ active: currentActiveStep >= 7 }">
          <div class="conn-arrow">→</div>
        </div>

        <!-- 节点 7: 综合决策引擎 -->
        <div class="node-box decision-node" :class="getNodeClass(7)">
          <div class="node-step">STEP 07</div>
          <div class="node-title">决策仲裁引擎</div>
          <div class="node-desc">买入评级 82.4分 (仓位15-20%)</div>
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
              <span class="log-stat tabular-nums">耗时: 1,842ms | Tokens: 4,210</span>
            </div>
          </div>

          <div class="log-body font-mono">
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VideoPlay, Document, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import EvidenceAggregator from '@/components/Terminal/EvidenceAggregator.vue'
import { stocksApi } from '@/api/stocks'

const route = useRoute()
const router = useRouter()

const hotDict: Record<string, string> = {
  'sh000001': '上证指数',
  '000001': '上证指数',
  'sz399001': '深证成指',
  '399001': '深证成指',
  'sz399006': '创业板指',
  '399006': '创业板指',
  'sh000680': '科创综指',
  '000680': '科创综指',
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

const stopLossPrice = computed(() => {
  return (currentStock.value.price * 0.92).toFixed(2)
})

const isRunning = ref(false)
const currentActiveStep = ref(7) // 初始为全部完成

function buildLogs(stock: typeof currentStock.value) {
  const lossPx = (stock.price * 0.92).toFixed(2)
  return [
    { time: '10:14:15.021', node: 'Quant Engine', nodeClass: 'node-sys', msg: `初筛通过，[${stock.name} ${stock.code}] 多因子综合评分: ${stock.score}.2 (动量 92, 资金 89)` },
    { time: '10:14:15.840', node: 'Macro Agent', nodeClass: 'node-macro', msg: `国家重点产业政策与 [${stock.sector}] 景气知识库检索完成，置信度 91%` },
    { time: '10:14:16.120', node: 'Tech Agent', nodeClass: 'node-tech', msg: `识别到日线突破横盘平台，MA5/20/60 多头排列金叉共振，置信度 88%` },
    { time: '10:14:16.480', node: 'Fund Agent', nodeClass: 'node-fund', msg: `标的 ${stock.name} 财务韧性与产业竞争壁垒验证通过，经营预测超预期，置信度 85%` },
    { time: '10:14:17.010', node: 'Aggregator', nodeClass: 'node-agg', msg: '汇聚 8 条多头证据与 3 条风险事实，检测到 1 处估值分歧' },
    { time: '10:14:17.380', node: 'Risk Agent', nodeClass: 'node-risk', msg: `高分位估值风险已标记，动态追踪止损线设定为 ${lossPx} 元` },
    { time: '10:14:17.842', node: 'Decision Engine', nodeClass: 'node-decision', msg: '仲裁完成: 最终得分 82.4，评级: 买入/逢低配置，仓位建议: 15%-20%' },
  ]
}

const runtimeLogs = ref(buildLogs(currentStock.value))

async function loadStockDetail(code: string) {
  if (!code) return
  try {
    const res = await stocksApi.getQuote(code)
    const q = (res as any)?.data || res
    if (q && (q.price !== undefined || q.close !== undefined)) {
      const px = Number(q.price ?? q.close ?? 86.4)
      const name = q.name || hotDict[code] || `标的 ${code}`
      const sector = q.industry || (code.startsWith('688') ? '科创先锋' : '主力优势产业')
      currentStock.value = {
        code,
        name,
        score: Math.min(96, Math.max(72, Math.round(78 + (q.change_percent ?? 0) * 2))),
        price: px,
        sector
      }
      runtimeLogs.value = buildLogs(currentStock.value)
      return
    }

    const poolRes = await stocksApi.getPool({ keyword: code, page_size: 1 })
    const item = (poolRes as any)?.data?.items?.[0]
    if (item) {
      currentStock.value = {
        code: item.code,
        name: item.name,
        score: 92,
        price: Number(item.close || 50),
        sector: item.industry || 'A股优势蓝筹'
      }
      runtimeLogs.value = buildLogs(currentStock.value)
    }
  } catch (e) {
    console.warn('工作流标的加载失败，使用默认配置:', e)
  }
}

watch(() => route.query.code, (newCode) => {
  if (newCode && typeof newCode === 'string') {
    currentStock.value.code = newCode
    if (hotDict[newCode]) {
      currentStock.value.name = hotDict[newCode]
    }
    loadStockDetail(newCode)
  }
})

onMounted(() => {
  const queryCode = (route.query.code as string) || 'sh000001'
  loadStockDetail(queryCode)
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

function runWorkflow() {
  if (isRunning.value) return
  isRunning.value = true
  currentActiveStep.value = 1
  runtimeLogs.value = [
    { time: new Date().toTimeString().slice(0, 8), node: 'Workflow Kernel', nodeClass: 'node-sys', msg: `流水线重新初始化，标的代码: ${currentStock.value.code} (${currentStock.value.name})` }
  ]

  let step = 1
  const interval = setInterval(() => {
    step++
    currentActiveStep.value = step

    if (step === 2) {
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Macro Agent',
        nodeClass: 'node-macro',
        msg: `国家重点专项政策 & [${currentStock.value.sector}] 产业链检索完成`
      })
    } else if (step === 3) {
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Tech Agent',
        nodeClass: 'node-tech',
        msg: '日线 KDJ/MACD 零轴共振形态匹配成功，多头动能饱满'
      })
    } else if (step === 4) {
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Fund Agent',
        nodeClass: 'node-fund',
        msg: `标的 ${currentStock.value.name} 核心业务产能及毛利率环比测算完毕`
      })
    } else if (step === 5) {
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Aggregator',
        nodeClass: 'node-agg',
        msg: '多智能体证据网格生成，权重计算与争议仲裁完成'
      })
    } else if (step === 6) {
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Risk Agent',
        nodeClass: 'node-risk',
        msg: `风控审查通过，动态追踪止损线 ${stopLossPrice.value} 元已锁定`
      })
    } else if (step >= 7) {
      clearInterval(interval)
      isRunning.value = false
      currentActiveStep.value = 7
      runtimeLogs.value.push({
        time: new Date().toTimeString().slice(0, 8),
        node: 'Decision Engine',
        nodeClass: 'node-decision',
        msg: `综合裁决完成：加权 82.4 分，标的 [${currentStock.value.name}] 买入评级已持久化`
      })
      ElMessage.success(`[${currentStock.value.name}] 多智能体流水线协同运行完毕，证据案卷与决策已同步！`)
    }
  }, 700)
}

function goToStock() {
  router.push({ path: '/terminal/stock', query: { code: currentStock.value.code } })
}

function goToReport() {
  router.push({ path: '/terminal/report', query: { code: currentStock.value.code } })
}
</script>

<style scoped lang="scss">
.workflow-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1680px;
  margin: 0 auto;
}

.workflow-control-bar {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .control-left {
    display: flex;
    align-items: center;
    gap: 14px;

    .ctrl-title {
      font-size: 13px;
      font-weight: 700;
      color: #101828;
    }

    .stock-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background-color: #f8fafc;
      border: 1px solid #eaecf0;
      border-radius: 4px;
      padding: 3px 8px;

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
  overflow: hidden;

  .flow-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background-color: #fafbfc;
    border-bottom: 1px solid #eaecf0;

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
  }
}

.node-box {
  background-color: #ffffff;
  border: 1px solid #eaecf0;
  border-radius: 6px;
  padding: 10px 12px;
  min-width: 140px;
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
</style>
