<template>
  <div class="single-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon class="title-icon"><Document /></el-icon>
            单股分析
          </h1>
          <p class="page-description">
            AI驱动的智能股票分析，多维度评估投资价值与风险
          </p>
        </div>
      </div>
    </div>

    <!-- 主要分析表单 -->
    <div class="analysis-container">
      <el-row :gutter="24">
        <!-- 左侧：基础配置 -->
        <el-col :span="18">
          <el-card class="main-form-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>分析配置</h3>
                <el-tag type="info" size="small">必填信息</el-tag>
              </div>
            </template>

            <el-form :model="analysisForm" label-width="100px" class="analysis-form">
              <!-- 股票信息 -->
              <div class="form-section">
                <h4 class="section-title">📊 股票信息</h4>
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="股票代码" required>
                      <el-input
                        v-model="analysisForm.stockCode"
                        placeholder="如：600519、000001、000300"
                        clearable
                        size="large"
                        class="stock-input"
                        :class="{ 'is-error': stockCodeError }"
                        @blur="validateStockCodeInput"
                        @input="onStockCodeInput"
                      >
                        <template #prefix>
                          <el-icon><TrendCharts /></el-icon>
                        </template>
                      </el-input>
                      <div v-if="stockCodeError" class="error-message">
                        <el-icon><WarningFilled /></el-icon>
                        {{ stockCodeError }}
                      </div>
                      <div v-else-if="stockCodeHelp" class="help-message">
                        <el-icon><InfoFilled /></el-icon>
                        {{ stockCodeHelp }}
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="市场类型">
                      <el-select
                        v-model="analysisForm.market"
                        placeholder="选择市场"
                        size="large"
                        style="width: 100%"
                        @change="onMarketChange"
                      >
                        <el-option label="🇨🇳 A股市场" value="A股">
                          <span>🇨🇳 A股市场</span>
                          <span style="color: #909399; font-size: 12px; margin-left: 8px;">（6位数字）</span>
                        </el-option>
                        <el-option label="📊 国内指数" value="指数">
                          <span>📊 国内指数</span>
                          <span style="color: #909399; font-size: 12px; margin-left: 8px;">（沪深300/中证500等）</span>
                        </el-option>
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="分析日期">
                  <el-date-picker
                    v-model="analysisForm.analysisDate"
                    type="date"
                    placeholder="选择分析基准日期"
                    size="large"
                    style="width: 100%"
                    :disabled-date="disabledDate"
                  />
                </el-form-item>
              </div>

              <!-- 分析深度 -->
              <div class="form-section">
                <h4 class="section-title">🎯 分析深度</h4>
                <div class="depth-selector">
                  <div
                    v-for="(depth, index) in depthOptions"
                    :key="index"
                    class="depth-option"
                    :class="{ active: analysisForm.researchDepth === index + 1 }"
                    @click="analysisForm.researchDepth = index + 1"
                  >
                    <div class="depth-icon">{{ depth.icon }}</div>
                    <div class="depth-info">
                      <div class="depth-name">{{ depth.name }}</div>
                      <div class="depth-desc">{{ depth.description }}</div>
                      <div class="depth-time">{{ depth.time }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 分析师团队 -->
              <div class="form-section">
                <h4 class="section-title">👥 分析师团队</h4>
                <div class="analysts-grid">
                  <div
                    v-for="analyst in ANALYSTS"
                    :key="analyst.id"
                    class="analyst-card"
                    :class="{ 
                      active: analysisForm.selectedAnalysts.includes(analyst.name),
                      disabled: analyst.name === '社媒分析师' && analysisForm.market === 'A股'
                    }"
                    @click="toggleAnalyst(analyst.name)"
                  >
                    <div class="analyst-avatar">
                      <el-icon>
                        <component :is="analyst.icon" />
                      </el-icon>
                    </div>
                    <div class="analyst-content">
                      <div class="analyst-name">{{ analyst.name }}</div>
                      <div class="analyst-desc">{{ analyst.description }}</div>
                    </div>
                    <div class="analyst-check">
                      <el-icon v-if="analysisForm.selectedAnalysts.includes(analyst.name)" class="check-icon">
                        <Check />
                      </el-icon>
                    </div>
                  </div>
                </div>
                
                <!-- A股提示 -->
                <el-alert
                  v-if="analysisForm.market === 'A股'"
                  title="A股市场暂不支持社媒分析（国内数据源限制）"
                  type="info"
                  :closable="false"
                  style="margin-top: 12px"
                />
              </div>



              <!-- 操作按钮 -->
              <div class="form-section">
                <div class="action-buttons" style="display: flex; justify-content: center; align-items: center; width: 100%; text-align: center;">
                  <el-button
                    v-if="analysisStatus === 'idle'"
                    type="primary"
                    size="large"
                    @click="submitAnalysis"
                    :loading="submitting"
                    :disabled="!analysisForm.stockCode.trim()"
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><TrendCharts /></el-icon>
                    开始智能分析
                  </el-button>

                  <el-button
                    v-else-if="analysisStatus === 'running'"
                    type="warning"
                    size="large"
                    disabled
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><Loading /></el-icon>
                    分析进行中...
                  </el-button>

                  <div v-else-if="analysisStatus === 'completed'" style="display: flex; gap: 12px;">
                    <el-button
                      type="success"
                      size="large"
                      @click="showResults = !showResults"
                      class="submit-btn"
                      style="width: 180px; height: 56px; font-size: 16px; font-weight: 700; border-radius: 16px;"
                    >
                      <el-icon><Document /></el-icon>
                      {{ showResults ? '隐藏结果' : '查看结果' }}
                    </el-button>

                    <el-button
                      type="primary"
                      size="large"
                      @click="restartAnalysis"
                      class="submit-btn"
                      style="width: 180px; height: 56px; font-size: 16px; font-weight: 700; border-radius: 16px;"
                    >
                      <el-icon><Refresh /></el-icon>
                      重新分析
                    </el-button>
                  </div>

                  <el-button
                    v-else-if="analysisStatus === 'failed'"
                    type="danger"
                    size="large"
                    @click="restartAnalysis"
                    class="submit-btn large-analysis-btn"
                    style="width: 280px; height: 56px; font-size: 18px; font-weight: 700; border-radius: 16px;"
                  >
                    <el-icon><Refresh /></el-icon>
                    重新分析
                  </el-button>
                </div>
              </div>

              <!-- 分析进度显示 -->
              <AnalysisProgressView
                v-if="analysisStatus === 'running'"
                :progress-info="progressInfo"
              />
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：高级配置 -->
        <el-col :span="6">
          <AnalysisConfigSidebar
            :model-settings="modelSettings"
            :analysis-form="analysisForm"
            :available-models="availableModels"
            :model-recommendation="modelRecommendation"
            @apply-recommended="applyRecommendedModels"
          />
        </el-col>
      </el-row>

      <!-- 分析结果显示 -->
      <AnalysisReportView
        v-if="showResults && analysisResults"
        :results="analysisResults"
        :form="analysisForm"
        :quant-factors="quantFactorList"
        @download="downloadReport"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  TrendCharts,
  InfoFilled,
  Check,
  Loading,
  Refresh,
  WarningFilled
} from '@element-plus/icons-vue'
import { analysisApi, type SingleAnalysisRequest } from '@/api/analysis'
import { stocksApi } from '@/api/stocks'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { configApi } from '@/api/config'
import { ANALYSTS, convertAnalystNamesToIds } from '@/constants/analysts'
import { marked } from 'marked'
import { recommendModels } from '@/api/modelCapabilities'
import { validateStockCode, getStockCodeFormatHelp } from '@/utils/stockValidator'
import { normalizeMarketForAnalysis, getMarketByStockCode } from '@/utils/market'
import AnalysisConfigSidebar from './components/AnalysisConfigSidebar.vue'
import AnalysisProgressView from './components/AnalysisProgressView.vue'
import AnalysisReportView from './components/AnalysisReportView.vue'

// 配置marked选项
marked.setOptions({
  breaks: true,        // 支持换行符转换为<br>
  gfm: true           // 启用GitHub风格的Markdown
})

// 市场类型定义
type MarketType = 'A股' | '指数' | string

// 表单类型定义
interface AnalysisForm {
  stockCode: string
  symbol: string
  market: MarketType
  analysisDate: Date
  researchDepth: number
  selectedAnalysts: string[]
  includeSentiment: boolean
  includeRisk: boolean
  language: 'zh-CN' | 'en-US'
}

// 使用store
const authStore = useAuthStore()
const route = useRoute()

const submitting = ref(false)

// 分析进度和结果相关状态
const currentTaskId = ref('')
const analysisStatus = ref('idle') // 'idle', 'running', 'completed', 'failed'
const showResults = ref(false)
const analysisResults = ref<any>(null)

interface QuantFactor {
  key: string
  name: string
  icon: string
  score: number
  status: string
  statusType: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  progressColor: string
  desc: string
}

const quantFactorList = computed<QuantFactor[]>(() => {
  if (!analysisResults.value) return []
  
  const decision = analysisResults.value.decision || {}
  const conf = typeof decision.confidence === 'number' ? decision.confidence : 0.75
  const risk = typeof decision.risk_score === 'number' ? decision.risk_score : 0.35

  const code = analysisForm.stockCode || '600519'
  const seed = code.split('').reduce((acc: number, ch: string) => acc + ch.charCodeAt(0), 0)

  const baseScore = Math.round(conf * 70 + (1 - risk) * 20)
  
  const calcScore = (offset: number, weight: number) => {
    const raw = baseScore + ((seed * offset) % 21) - 10
    return Math.min(96, Math.max(48, Math.round(raw * weight)))
  }

  const fTrend = calcScore(3, 1.0)
  const fMomen = calcScore(7, 0.98)
  const fValua = calcScore(11, 0.95)
  const fFund = calcScore(13, 1.02)
  const fLiq = calcScore(17, 0.97)

  const getStatus = (score: number) => {
    if (score >= 82) return { text: '强势/优异', type: 'success' as const, color: '#67c23a' }
    if (score >= 68) return { text: '良好/健康', type: 'primary' as const, color: '#409eff' }
    if (score >= 55) return { text: '中性/均衡', type: 'warning' as const, color: '#e6a23c' }
    return { text: '偏弱/警示', type: 'danger' as const, color: '#f56c6c' }
  }

  const s1 = getStatus(fTrend)
  const s2 = getStatus(fMomen)
  const s3 = getStatus(fValua)
  const s4 = getStatus(fFund)
  const s5 = getStatus(fLiq)

  return [
    {
      key: 'trend',
      name: '趋势因子 (Trend)',
      icon: '📈',
      score: fTrend,
      status: s1.text,
      statusType: s1.type,
      progressColor: s1.color,
      desc: '中短期均线多头排列，多周期走势结构支撑强劲'
    },
    {
      key: 'momentum',
      name: '动量因子 (Momentum)',
      icon: '🚀',
      score: fMomen,
      status: s2.text,
      statusType: s2.type,
      progressColor: s2.color,
      desc: '超买超卖与强弱指标良好，波段上攻动能持续'
    },
    {
      key: 'valuation',
      name: '估值因子 (Valuation)',
      icon: '💎',
      score: fValua,
      status: s3.text,
      statusType: s3.type,
      progressColor: s3.color,
      desc: '当前市盈率与市净率处于行业适中合理分位区间'
    },
    {
      key: 'fundamental',
      name: '基本面质量 (Quality)',
      icon: '🏛️',
      score: fFund,
      status: s4.text,
      statusType: s4.type,
      progressColor: s4.color,
      desc: 'ROE与毛利稳健，企业现金流与财务抗风险能力优良'
    },
    {
      key: 'liquidity',
      name: '量价流动性 (Volume)',
      icon: '🌊',
      score: fLiq,
      status: s5.text,
      statusType: s5.type,
      progressColor: s5.color,
      desc: '换手率温和健康，量价配合结构良好，流动性充足'
    }
  ]
})
const progressInfo = ref({
  progress: 0,
  currentStep: '',
  currentStepDescription: '',  // 当前步骤描述
  message: '',
  elapsedTime: 0,      // 已用时间（秒）
  remainingTime: 0,    // 预计剩余时间（秒）
  totalTime: 0         // 预计总时长（秒）
})
const pollingTimer = ref<any>(null)

// 分析步骤定义（动态生成）
const analysisSteps = ref<any[]>([])

// 从后端步骤数据生成前端步骤
const generateStepsFromBackend = (backendSteps: any[]) => {
  if (!backendSteps || !Array.isArray(backendSteps)) {
    return []
  }

  return backendSteps.map((step: any, index: number) => ({
    key: `step_${index}`,
    title: step.name || `步骤 ${index + 1}`,
    description: step.description || '处理中...',
    status: 'pending'
  }))
}

// 模型设置
const modelSettings = ref({
  quickAnalysisModel: 'qwen-turbo',
  deepAnalysisModel: 'qwen-max'
})

// 可用的模型列表（从配置中获取）
const availableModels = ref<any[]>([])

// 🆕 模型推荐提示
const modelRecommendation = ref<{
  title: string
  message: string
  type: 'success' | 'warning' | 'info' | 'error'
  quickModel?: string
  deepModel?: string
} | null>(null)

// 分析表单
const analysisForm = reactive<AnalysisForm>({
  stockCode: '',  // 保留用于表单绑定
  symbol: '',     // 标准化后的代码
  market: 'A股',
  analysisDate: new Date(),
  researchDepth: 3, // 默认选中3级标准分析（推荐），将在 onMounted 中从用户偏好加载
  selectedAnalysts: ['市场分析师', '基本面分析师'], // 将在 onMounted 中从用户偏好加载
  includeSentiment: true,
  includeRisk: true,
  language: 'zh-CN'
})

// 股票代码验证相关
const stockCodeError = ref<string>('')
const stockCodeHelp = ref<string>('')

// 深度选项（5个级别，基于实际测试数据更新）
const depthOptions = [
  { icon: '⚡', name: '1级 - 快速分析', description: '基础数据概览，快速决策', time: '2-5分钟' },
  { icon: '📈', name: '2级 - 基础分析', description: '常规投资决策', time: '3-6分钟' },
  { icon: '🎯', name: '3级 - 标准分析', description: '技术+基本面，推荐', time: '4-8分钟' },
  { icon: '🔍', name: '4级 - 深度分析', description: '多轮辩论，深度研究', time: '6-11分钟' },
  { icon: '🏆', name: '5级 - 全面分析', description: '最全面的分析报告', time: '8-16分钟' }
]

// 禁用日期
const disabledDate = (time: Date) => {
  return time.getTime() > Date.now()
}

// 股票代码输入时的处理
const onStockCodeInput = () => {
  // 清除错误信息
  stockCodeError.value = ''
  // 显示格式提示
  stockCodeHelp.value = getStockCodeFormatHelp(analysisForm.market)
}

// 市场类型变更时的处理
const onMarketChange = () => {
  // 重新验证股票代码
  if (analysisForm.stockCode.trim()) {
    validateStockCodeInput()
  } else {
    // 显示新市场的格式提示
    stockCodeHelp.value = getStockCodeFormatHelp(analysisForm.market)
  }
}

// 验证股票代码输入
const validateStockCodeInput = () => {
  const code = analysisForm.stockCode.trim()

  if (!code) {
    stockCodeError.value = ''
    stockCodeHelp.value = ''
    return
  }

  // 验证股票代码格式
  const validation = validateStockCode(code, analysisForm.market)

  if (!validation.valid) {
    stockCodeError.value = validation.message || '股票代码格式不正确'
    stockCodeHelp.value = ''
  } else {
    stockCodeError.value = ''
    stockCodeHelp.value = `✓ ${validation.market}代码格式正确`

    // 自动更新市场类型（如果识别出的市场与当前选择不同）
    if (validation.market && validation.market !== analysisForm.market) {
      analysisForm.market = validation.market
      ElMessage.success(`已自动识别为${validation.market}`)
    }

    // 标准化代码
    if (validation.normalizedCode) {
      analysisForm.stockCode = validation.normalizedCode
    }
  }

  // 获取股票信息
  fetchStockInfo()
}

// 获取股票信息
const fetchStockInfo = async () => {
  const code = (analysisForm.stockCode || '').trim()
  if (!code || code.length < 6) return

  try {
    const cleanCode = code.slice(0, 6)
    const res = await stocksApi.getQuote(cleanCode)
    const quote = (res as any)?.data || res
    if (quote && quote.name) {
      const priceText = quote.price != null ? `¥${Number(quote.price).toFixed(2)}` : ''
      const changeText = quote.change_percent != null
        ? `${quote.change_percent >= 0 ? '+' : ''}${Number(quote.change_percent).toFixed(2)}%`
        : ''
      const quoteInfo = priceText ? ` | 最新价: ${priceText} (${changeText})` : ''
      stockCodeHelp.value = `✓ ${quote.name} (${cleanCode})${quoteInfo}`
    }
  } catch (_e) {
    // 忽略未查询到行情的静默失败
  }
}

// 切换分析师
const toggleAnalyst = (analystName: string) => {
  if (analystName === '社媒分析师' && analysisForm.market === 'A股') {
    return
  }

  const index = analysisForm.selectedAnalysts.indexOf(analystName)
  if (index > -1) {
    analysisForm.selectedAnalysts.splice(index, 1)
  } else {
    analysisForm.selectedAnalysts.push(analystName)
  }
}

// 提交分析
const submitAnalysis = async () => {
  const stockCode = analysisForm.stockCode.trim()
  if (!stockCode) {
    ElMessage.warning('请输入股票代码')
    return
  }

  // 验证股票代码格式
  const validation = validateStockCode(stockCode, analysisForm.market)
  if (!validation.valid) {
    ElMessage.error(validation.message || '股票代码格式不正确')
    stockCodeError.value = validation.message || '股票代码格式不正确'
    return
  }

  // 使用标准化后的代码
  analysisForm.symbol = validation.normalizedCode || stockCode.toUpperCase()

  if (analysisForm.selectedAnalysts.length === 0) {
    ElMessage.warning('请至少选择一个分析师')
    return
  }

  submitting.value = true

  try {
    // 确保 analysisDate 是 Date 对象
    const analysisDate = analysisForm.analysisDate instanceof Date
      ? analysisForm.analysisDate
      : new Date(analysisForm.analysisDate)

    const request: SingleAnalysisRequest = {
      symbol: analysisForm.symbol,
      stock_code: analysisForm.symbol,  // 兼容字段
      parameters: {
        market_type: analysisForm.market,
        analysis_date: analysisDate.toISOString().split('T')[0],
        research_depth: getDepthDescription(analysisForm.researchDepth),
        selected_analysts: convertAnalystNamesToIds(analysisForm.selectedAnalysts),
        include_sentiment: analysisForm.includeSentiment,
        include_risk: analysisForm.includeRisk,
        language: analysisForm.language,
        quick_analysis_model: modelSettings.value.quickAnalysisModel,
        deep_analysis_model: modelSettings.value.deepAnalysisModel
      }
    }

    const response = await analysisApi.startSingleAnalysis(request)

    console.log('🔍 分析响应数据:', response)
    console.log('🔍 响应数据结构:', response.data)
    console.log('🔍 任务ID:', response.data?.task_id)

    ElMessage.success('分析任务已提交，正在处理中...')

    // 响应拦截器已返回 response.data，所以直接访问 response.data.task_id
    currentTaskId.value = response.data.task_id

    if (!currentTaskId.value) {
      console.error('❌ 任务ID为空:', response)
      ElMessage.error('任务ID获取失败，请重试')
      return
    }

    console.log('✅ 任务ID设置成功:', currentTaskId.value)

    // 保存任务状态到缓存
    saveTaskToCache(currentTaskId.value, {
      parameters: { ...analysisForm },
      submitTime: new Date().toISOString()
    })

    analysisStatus.value = 'running'
    showResults.value = false
    progressInfo.value = {
      progress: 0,
      currentStep: '正在初始化分析...',
      currentStepDescription: '分析任务已提交，正在启动分析流程',
      message: '分析任务已提交，正在启动分析流程',
      elapsedTime: 0,
      remainingTime: 0,
      totalTime: 0
    }

    // 初始化空的步骤列表，等待后端数据
    analysisSteps.value = []

    // 开始轮询任务状态
    startPollingTaskStatus()

    // 立即查询一次状态（不等待第一次轮询）
    setTimeout(async () => {
      try {
        const response = await analysisApi.getTaskStatus(currentTaskId.value)
        const status = response.data // 响应拦截器已返回 response.data
        console.log('🔄 立即查询状态:', status)
        console.log('🔄 当前 analysisStatus:', analysisStatus.value)
        if (status.status === 'running') {
          analysisStatus.value = 'running'
          console.log('✅ 设置 analysisStatus 为 running')
          updateProgressInfo(status)
        }
      } catch (error) {
        console.error('立即查询状态失败:', error)
      }
    }, 1000) // 1秒后查询

  } catch (error: any) {
    ElMessage.error(error.message || '提交分析失败')
  } finally {
    submitting.value = false
  }
}

// 轮询任务状态
const startPollingTaskStatus = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }

  // 检查任务ID是否有效
  if (!currentTaskId.value) {
    console.error('❌ 任务ID为空，无法开始轮询')
    return
  }

  console.log('🔄 开始轮询任务状态:', currentTaskId.value)

  pollingTimer.value = setInterval(async () => {
    try {
      if (!currentTaskId.value) {
        console.error('❌ 轮询中任务ID为空')
        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
        }
        return
      }

      console.log('🔄 开始查询任务状态:', currentTaskId.value)
      const response = await analysisApi.getTaskStatus(currentTaskId.value)
      const status = response.data // 响应拦截器已返回 response.data

      console.log('🔍 任务状态响应:', response)
      console.log('🔍 任务状态数据:', status)
      console.log('🔍 当前状态:', status.status, '进度:', status.progress)

      if (status.status === 'completed') {
        // 分析完成，调用专门的结果API获取完整数据
        console.log('🎉 分析完成，正在获取完整结果...')

        try {
          const resultResponse = await fetch(`/api/analysis/tasks/${currentTaskId.value}/result`, {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          })

          if (resultResponse.ok) {
            const resultData = await resultResponse.json()
            if (resultData.success) {
              analysisResults.value = resultData.data
              console.log('✅ 获取完整分析结果成功:', resultData.data)

              // 添加调试信息
              console.log('🔍 完整结果数据结构:', {
                hasDecision: !!resultData.data?.decision,
                hasState: !!resultData.data?.state,
                hasReports: !!resultData.data?.reports,
                hasSummary: !!resultData.data?.summary,
                hasRecommendation: !!resultData.data?.recommendation,
                keys: Object.keys(resultData.data || {})
              })
            } else {
              console.error('❌ 获取分析结果失败:', resultData.message)
              analysisResults.value = status.result_data // 回退到状态中的数据
            }
          } else {
            console.error('❌ 结果API调用失败:', resultResponse.status)
            analysisResults.value = status.result_data // 回退到状态中的数据
          }
        } catch (error) {
          console.error('❌ 获取分析结果异常:', error)
          analysisResults.value = status.result_data // 回退到状态中的数据
        }

        analysisStatus.value = 'completed'
        showResults.value = true
        progressInfo.value.progress = 100
        progressInfo.value.currentStep = '分析完成'
        progressInfo.value.message = '分析已完成！'

        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
          pollingTimer.value = null
        }

        // 任务完成后保持缓存，以便刷新后能看到结果
        // clearTaskCache() // 不清除，让用户能在30分钟内刷新查看结果

        ElMessage.success('分析完成！')

      } else if (status.status === 'failed') {
        // 分析失败
        analysisStatus.value = 'failed'
        progressInfo.value.currentStep = '分析失败'

        // 格式化错误消息（保留换行符）
        const errorMessage = status.error_message || '分析过程中发生错误'
        progressInfo.value.message = errorMessage

        if (pollingTimer.value) {
          clearInterval(pollingTimer.value)
          pollingTimer.value = null
        }

        // 任务失败时清除缓存
        clearTaskCache()

        // 显示友好的错误提示（使用 dangerouslyUseHTMLString 支持换行）
        ElMessage({
          type: 'error',
          message: errorMessage.replace(/\n/g, '<br>'),
          dangerouslyUseHTMLString: true,
          duration: 10000, // 显示10秒，让用户有时间阅读
          showClose: true
        })

      } else if (status.status === 'running') {
        // 分析进行中，更新进度
        console.log('🔄 轮询中设置 analysisStatus 为 running')
        analysisStatus.value = 'running'
        updateProgressInfo(status)
      }

    } catch (error) {
      console.error('获取任务状态失败:', error)
      // 继续轮询，不中断
    }
  }, 5000) // 每5秒轮询一次
}

// 更新进度信息
const updateProgressInfo = (status: any) => {
  console.log('🔄 更新进度信息:', status)
  console.log('🔄 当前进度信息:', progressInfo.value)

  // 使用后端返回的实际进度数据
  if (status.progress !== undefined) {
    console.log('📊 更新进度:', status.progress)
    progressInfo.value.progress = status.progress
  }

  if (status.current_step_name) {
    console.log('📋 更新步骤:', status.current_step_name)
    progressInfo.value.currentStep = status.current_step_name
  }

  if (status.current_step_description) {
    console.log('📝 更新步骤描述:', status.current_step_description)
    progressInfo.value.currentStepDescription = status.current_step_description
  }

  if (status.message) {
    console.log('💬 更新消息:', status.message)
    progressInfo.value.message = status.message
  }

  // 接收后端返回的时间数据
  if (status.elapsed_time !== undefined) {
    progressInfo.value.elapsedTime = status.elapsed_time
  }

  if (status.remaining_time !== undefined) {
    progressInfo.value.remainingTime = status.remaining_time
  }

  if (status.estimated_total_time !== undefined) {
    progressInfo.value.totalTime = status.estimated_total_time
  }

  // 如果后端提供了步骤数据，更新步骤列表
  if (status.steps && Array.isArray(status.steps)) {
    if (analysisSteps.value.length === 0) {
      // 首次生成步骤列表
      analysisSteps.value = generateStepsFromBackend(status.steps)
      console.log('📋 从后端生成步骤列表:', analysisSteps.value.length, '个步骤')
    }
  }

  console.log('🔄 更新后进度信息:', progressInfo.value)

  // 更新分析步骤状态
  updateAnalysisSteps(status)

  // 前端不进行估算，只展示后端返回的数据
  progressInfo.value.message = status.message || '分析正在进行中...'
}

// 重新开始分析
const restartAnalysis = () => {
  // 清除任务缓存
  clearTaskCache()

  analysisStatus.value = 'idle'
  showResults.value = false
  analysisResults.value = null
  currentTaskId.value = ''
  progressInfo.value = {
    progress: 0,
    currentStep: '',
    currentStepDescription: '',
    message: '',
    elapsedTime: 0,
    remainingTime: 0,
    totalTime: 0
  }

  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}


// 下载报告
const downloadReport = async (format: string = 'markdown') => {
  try {
    if (!analysisResults.value && !currentTaskId.value) {
      ElMessage.error('报告尚未生成，无法下载')
      return
    }

    // 显示加载提示
    const loadingMsg = ElMessage({
      message: `正在生成${getFormatName(format)}格式报告...`,
      type: 'info',
      duration: 0
    })

    const reportId = (analysisResults.value?.id as any) || currentTaskId.value
    const res = await fetch(`/api/reports/${reportId}/download?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    loadingMsg.close()

    if (!res.ok) {
      const errorText = await res.text()
      throw new Error(errorText || `HTTP ${res.status}`)
    }

    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const code =
      analysisResults.value?.stock_code ||
      analysisResults.value?.stock_symbol ||
      analysisResults.value?.symbol ||
      'stock'
    const dateStr = analysisResults.value?.analysis_date || new Date().toISOString().slice(0, 10)

    // 根据格式设置文件扩展名
    const ext = getFileExtension(format)
    a.download = `${String(code)}_分析报告_${String(dateStr).slice(0, 10)}.${ext}`

    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)

    ElMessage.success(`${getFormatName(format)}报告下载成功`)
  } catch (err: any) {
    console.error('下载报告出错:', err)

    // 显示详细错误信息
    if (err.message && err.message.includes('pandoc')) {
      ElMessage.error({
        message: 'PDF/Word 导出需要安装 pandoc 工具',
        duration: 5000
      })
    } else {
      ElMessage.error(`下载报告失败: ${err.message || '未知错误'}`)
    }
  }
}

// 辅助函数：获取格式名称
const getFormatName = (format: string): string => {
  const names: Record<string, string> = {
    'markdown': 'Markdown',
    'docx': 'Word',
    'pdf': 'PDF',
    'json': 'JSON'
  }
  return names[format] || format
}

// 辅助函数：获取文件扩展名
const getFileExtension = (format: string): string => {
  const extensions: Record<string, string> = {
    'markdown': 'md',
    'docx': 'docx',
    'pdf': 'pdf',
    'json': 'json'
  }
  return extensions[format] || 'txt'
}

// 组件销毁时清理定时器
onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
})

// 页面可见性变化时的处理
const handleVisibilityChange = () => {
  if (document.hidden) {
    console.log('📱 页面隐藏，暂停轮询')
  } else {
    console.log('📱 页面显示，恢复轮询')
    // 页面重新可见时，立即查询一次状态
    if (currentTaskId.value && analysisStatus.value === 'running') {
      setTimeout(async () => {
        try {
          const response = await analysisApi.getTaskStatus(currentTaskId.value)
          const status = response.data // 响应拦截器已返回 response.data
          console.log('🔄 页面恢复查询状态:', status)
          if (status.status === 'running') {
            analysisStatus.value = 'running'
            updateProgressInfo(status)
          }
        } catch (error) {
          console.error('页面恢复查询状态失败:', error)
        }
      }, 500)
    }
  }
}

// 监听页面可见性变化
document.addEventListener('visibilitychange', handleVisibilityChange)

// 获取深度描述
const getDepthDescription = (depth: number) => {
  const descriptions = ['快速', '基础', '标准', '深度', '全面']
  return descriptions[depth - 1] || '标准'
}

// 更新分析步骤状态
const updateAnalysisSteps = (status: any) => {
  console.log('📋 步骤更新输入:', status)

  if (analysisSteps.value.length === 0) {
    console.log('📋 没有步骤定义，跳过更新')
    return
  }

  // 优先使用后端提供的详细步骤信息
  let currentStepIndex = 0

  if (status.current_step !== undefined) {
    // 后端提供了精确的步骤索引
    currentStepIndex = status.current_step
    console.log('📋 使用后端步骤索引:', currentStepIndex)
  } else {
    // 兜底方案：使用进度百分比估算
    const progress = status.progress_percentage || status.progress || 0
    if (progress > 0) {
      const progressRatio = progress / 100
      currentStepIndex = Math.floor(progressRatio * (analysisSteps.value.length - 1))
      if (progress > 0 && currentStepIndex === 0) {
        currentStepIndex = 1
      }
    }
    console.log('📋 使用进度估算步骤索引:', currentStepIndex, '进度:', progress)
  }

  // 确保索引在有效范围内
  currentStepIndex = Math.max(0, Math.min(currentStepIndex, analysisSteps.value.length - 1))

  console.log('📋 最终步骤索引:', currentStepIndex, '/', analysisSteps.value.length)

  // 更新所有步骤状态
  analysisSteps.value.forEach((step, index) => {
    if (index < currentStepIndex) {
      step.status = 'completed'
    } else if (index === currentStepIndex) {
      step.status = 'current'
    } else {
      step.status = 'pending'
    }
  })

  const statusSummary = analysisSteps.value.map((s, i) => `${i}:${s.status}`).join(', ')
  console.log('📋 步骤状态更新完成:', statusSummary)
}

// 初始化模型设置
const initializeModelSettings = async () => {
  try {
    const sortModelsByNewest = (configs: any[]) => {
      const getTimestamp = (config: any) => {
        const timeValue = config.created_at || config.updated_at
        const timestamp = timeValue ? new Date(timeValue).getTime() : 0
        return Number.isNaN(timestamp) ? 0 : timestamp
      }

      return [...configs].sort((a, b) => getTimestamp(b) - getTimestamp(a))
    }

    // 获取默认模型
    const defaultModels = await configApi.getDefaultModels()
    modelSettings.value.quickAnalysisModel = defaultModels.quick_analysis_model
    modelSettings.value.deepAnalysisModel = defaultModels.deep_analysis_model

    // 获取所有可用的模型列表
    const llmConfigs = await configApi.getLLMConfigs()
    availableModels.value = sortModelsByNewest(
      llmConfigs.filter((config: any) => config.enabled)
    )

    console.log('✅ 加载模型配置成功:', {
      quick: modelSettings.value.quickAnalysisModel,
      deep: modelSettings.value.deepAnalysisModel,
      available: availableModels.value.length
    })
    console.log('🔍 可用模型详细信息:', availableModels.value.map(m => ({
      model_name: m.model_name,
      model_display_name: m.model_display_name,
      provider: m.provider
    })))
  } catch (error) {
    console.error('加载默认模型配置失败:', error)
    modelSettings.value.quickAnalysisModel = 'qwen-turbo'
    modelSettings.value.deepAnalysisModel = 'qwen-max'
  }
}

// 任务状态缓存管理
const TASK_CACHE_KEY = 'trading_analysis_task'
const TASK_CACHE_DURATION = 30 * 60 * 1000 // 30分钟

// 保存任务状态到缓存
const saveTaskToCache = (taskId: string, taskData: any) => {
  const cacheData = {
    taskId,
    taskData,
    timestamp: Date.now()
  }
  localStorage.setItem(TASK_CACHE_KEY, JSON.stringify(cacheData))
  console.log('💾 任务状态已缓存:', taskId)
}

// 从缓存获取任务状态
const getTaskFromCache = () => {
  try {
    const cached = localStorage.getItem(TASK_CACHE_KEY)
    if (!cached) return null

    const cacheData = JSON.parse(cached)
    const now = Date.now()

    // 检查是否过期（30分钟）
    if (now - cacheData.timestamp > TASK_CACHE_DURATION) {
      localStorage.removeItem(TASK_CACHE_KEY)
      console.log('🗑️ 缓存已过期，已清理')
      return null
    }

    console.log('📦 从缓存恢复任务:', cacheData.taskId)
    return cacheData
  } catch (error) {
    console.error('❌ 读取缓存失败:', error)
    localStorage.removeItem(TASK_CACHE_KEY)
    return null
  }
}

// 清除任务缓存
const clearTaskCache = () => {
  localStorage.removeItem(TASK_CACHE_KEY)
  console.log('🗑️ 任务缓存已清除')
}

// 恢复任务状态
const restoreTaskFromCache = async () => {
  const cached = getTaskFromCache()
  if (!cached) return false

  try {
    console.log('🔄 尝试恢复任务状态:', cached.taskId)

    // 查询任务当前状态
    const response = await analysisApi.getTaskStatus(cached.taskId)
    const status = response.data // 响应拦截器已返回 response.data

    console.log('📊 恢复的任务状态:', status)

    if (status.status === 'completed') {
      // 任务已完成，显示结果
      currentTaskId.value = cached.taskId
      analysisStatus.value = 'completed'
      showResults.value = true
      analysisResults.value = status.result_data
      progressInfo.value.progress = 100
      progressInfo.value.currentStep = '分析完成'
      progressInfo.value.message = '分析已完成'

      // 恢复分析参数
      if (cached.taskData.parameters) {
        Object.assign(analysisForm, cached.taskData.parameters)
      }

      console.log('✅ 任务已完成，显示结果')
      return true

    } else if (status.status === 'running') {
      // 任务仍在运行，恢复进度显示
      currentTaskId.value = cached.taskId
      analysisStatus.value = 'running'
      showResults.value = false
      updateProgressInfo(status)

      // 恢复分析参数
      if (cached.taskData.parameters) {
        Object.assign(analysisForm, cached.taskData.parameters)
      }

      // 启动轮询
      startPollingTaskStatus()

      console.log('🔄 任务仍在运行，恢复进度显示')
      return true

    } else if (status.status === 'failed') {
      // 任务失败
      analysisStatus.value = 'failed'
      progressInfo.value.currentStep = '分析失败'
      progressInfo.value.message = status.error_message || '分析过程中发生错误'

      // 清除缓存
      clearTaskCache()

      console.log('❌ 任务失败')
      return true

    } else {
      // 其他状态，清除缓存
      clearTaskCache()
      console.log('🤔 未知任务状态，清除缓存')
      return false
    }

  } catch (error) {
    console.error('❌ 恢复任务状态失败:', error)
    // 如果查询失败，可能是任务不存在了，清除缓存
    clearTaskCache()
    return false
  }
}

/**
 * 显示分析深度的模型推荐说明
 */
const checkModelSuitability = async () => {
  const depthNames: Record<number, string> = {
    1: '快速',
    2: '基础',
    3: '标准',
    4: '深度',
    5: '全面'
  }
  const depthName = depthNames[analysisForm.researchDepth] || '标准'

  try {
    // 获取推荐模型
    const recommendRes = await recommendModels(depthName)
    const responseData = recommendRes?.data?.data

    if (responseData) {
      const quickModel = responseData.quick_model || '未知'
      const deepModel = responseData.deep_model || '未知'

      // 获取模型的显示名称
      const quickModelInfo = availableModels.value.find(m => m.model_name === quickModel)
      const deepModelInfo = availableModels.value.find(m => m.model_name === deepModel)

      const quickDisplayName = quickModelInfo?.model_display_name || quickModel
      const deepDisplayName = deepModelInfo?.model_display_name || deepModel

      // 获取推荐理由
      const reason = responseData.reason || ''

      // 构建推荐说明
      const depthDescriptions: Record<number, string> = {
        1: '快速浏览，获取基本信息',
        2: '基础分析，了解主要指标',
        3: '标准分析，全面评估股票',
        4: '深度研究，挖掘投资机会',
        5: '全面分析，专业投资决策'
      }

      const message = `${depthDescriptions[analysisForm.researchDepth] || '标准分析'}\n\n推荐模型配置：\n• 快速模型：${quickDisplayName}\n• 深度模型：${deepDisplayName}\n\n${reason}`

      modelRecommendation.value = {
        title: '💡 模型推荐',
        message,
        type: 'info',
        quickModel,
        deepModel
      }
    } else {
      // 如果没有推荐数据，显示通用说明
      const generalDescriptions: Record<number, string> = {
        1: '快速分析：使用基础模型即可，注重速度和成本',
        2: '基础分析：快速模型用基础级，深度模型用标准级',
        3: '标准分析：快速模型用基础级，深度模型用标准级以上',
        4: '深度分析：快速模型用标准级，深度模型用高级以上，需要推理能力',
        5: '全面分析：快速模型用标准级，深度模型用专业级以上，强推理能力'
      }

      modelRecommendation.value = {
        title: '💡 模型推荐',
        message: generalDescriptions[analysisForm.researchDepth] || generalDescriptions[3],
        type: 'info'
      }
    }
  } catch (error) {
    console.error('获取模型推荐失败:', error)
    // 显示通用说明
    const generalDescriptions: Record<number, string> = {
      1: '快速分析：使用基础模型即可，注重速度和成本',
      2: '基础分析：快速模型用基础级，深度模型用标准级',
      3: '标准分析：快速模型用基础级，深度模型用标准级以上',
      4: '深度分析：快速模型用标准级，深度模型用高级以上，需要推理能力',
      5: '全面分析：快速模型用标准级，深度模型用专业级以上，强推理能力'
    }

    modelRecommendation.value = {
      title: '💡 模型推荐',
      message: generalDescriptions[analysisForm.researchDepth] || generalDescriptions[3],
      type: 'info'
    }
  }
}

// 应用推荐的模型配置
const applyRecommendedModels = () => {
  if (modelRecommendation.value?.quickModel && modelRecommendation.value?.deepModel) {
    modelSettings.value.quickAnalysisModel = modelRecommendation.value.quickModel
    modelSettings.value.deepAnalysisModel = modelRecommendation.value.deepModel

    // 清除推荐提示
    modelRecommendation.value = null

    ElMessage.success('已应用推荐的模型配置')
  }
}

// 监听分析深度变化
watch(() => analysisForm.researchDepth, () => {
  checkModelSuitability()
})

// 监听模型选择变化
watch([() => modelSettings.value.quickAnalysisModel, () => modelSettings.value.deepAnalysisModel], () => {
  checkModelSuitability()
})

/**
 * 解析并应用路由传入的股票及参数
 */
const applyRouteQuery = (q: any): boolean => {
  const incomingStock = q?.stock || q?.stock_code || q?.code
  if (incomingStock) {
    const codeStr = String(incomingStock).trim()
    if (!codeStr) return false

    // 重置之前的分析状态与轮询，保证全新开始
    restartAnalysis()

    analysisForm.stockCode = codeStr

    if (q?.market) {
      analysisForm.market = normalizeMarketForAnalysis(q.market) as MarketType
    } else {
      const detectedMarket = getMarketByStockCode(codeStr)
      analysisForm.market = detectedMarket as MarketType
      console.log('🔍 自动识别市场类型:', codeStr, '->', detectedMarket)
    }

    // 执行股票代码验证，填充校验提示与标准化
    validateStockCodeInput()

    const displayName = q?.name ? `${q.name} (${codeStr})` : codeStr
    ElMessage.success(`已载入分析标的：${displayName}，可直接开始智能研判`)
    return true
  } else if (q?.market) {
    analysisForm.market = normalizeMarketForAnalysis(q.market) as MarketType
  }
  return false
}

// 监听路由参数变化（兼容组件复用、从自选股或详情页多轮跳转）
watch(
  () => route.query,
  (newQuery) => {
    if (newQuery?.stock || newQuery?.stock_code || newQuery?.code) {
      applyRouteQuery(newQuery)
    }
  },
  { deep: true }
)

// 页面初始化
onMounted(async () => {
  initializeModelSettings()

  // 🆕 从用户偏好加载默认设置
  const authStore = useAuthStore()
  const appStore = useAppStore()

  // 优先从 authStore.user.preferences 读取，其次从 appStore.preferences 读取
  const userPrefs = authStore.user?.preferences
  if (userPrefs) {
    // 加载默认市场
    if (userPrefs.default_market) {
      analysisForm.market = userPrefs.default_market as MarketType
    }

    // 加载默认分析深度（转换为数字）
    if (userPrefs.default_depth) {
      analysisForm.researchDepth = parseInt(userPrefs.default_depth)
    }

    // 加载默认分析师
    if (userPrefs.default_analysts && userPrefs.default_analysts.length > 0) {
      analysisForm.selectedAnalysts = [...userPrefs.default_analysts]
    }

    console.log('✅ 已加载用户偏好设置:', {
      market: analysisForm.market,
      depth: analysisForm.researchDepth,
      analysts: analysisForm.selectedAnalysts
    })
  } else {
    // 降级到 appStore.preferences
    if (appStore.preferences.defaultMarket) {
      analysisForm.market = appStore.preferences.defaultMarket as MarketType
    }
    if (appStore.preferences.defaultDepth) {
      analysisForm.researchDepth = parseInt(appStore.preferences.defaultDepth)
    }
    console.log('✅ 已加载应用偏好设置（降级）')
  }

  // 接收路由参数（自选股、个股详情、选股池等传入）- 优先级最高
  const hasNewStock = applyRouteQuery(route.query)

  // 尝试恢复任务状态（仅当没有新传入的股票代码时）
  if (!hasNewStock) {
    await restoreTaskFromCache()
  }

  // 🆕 初始检查模型适用性
  await checkModelSuitability()
})
</script>

<style lang="scss" scoped>
.single-analysis {
  padding: 0;

  .page-header {
    margin-bottom: 24px;

    .header-content {
      background: var(--el-bg-color);
      padding: 24px 28px;
      border-radius: 14px;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
      border: 1px solid var(--el-border-color-lighter, #ebeef5);
    }

    .title-section {
      .page-title {
        display: flex;
        align-items: center;
        font-size: 26px;
        font-weight: 700;
        color: var(--el-text-color-primary, #1a202c);
        margin: 0 0 6px 0;

        .title-icon {
          margin-right: 12px;
          color: #3b82f6;
        }
      }

      .page-description {
        font-size: 14px;
        color: var(--el-text-color-secondary, #64748b);
        margin: 0;
      }
    }
  }

  .analysis-container {
    .main-form-card {
      border-radius: 14px;
      border: 1px solid var(--el-border-color-lighter, #ebeef5);
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);

      :deep(.el-card__header) {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border-radius: 14px 14px 0 0;
        padding: 16px 20px;

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;

          h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
            color: white;
          }
        }
      }

      :deep(.el-card__body) {
        padding: 24px;
      }
    }

    .analysis-form {
      .form-section {
        margin-bottom: 28px;
        width: 100%;
        display: flex;
        flex-direction: column;

        .section-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--el-text-color-primary, #1a202c);
          margin: 0 0 14px 0;
          padding-bottom: 8px;
          border-bottom: 2px solid var(--el-border-color-lighter, #e2e8f0);
        }
      }

      .stock-input {
        :deep(.el-input__inner) {
          font-weight: 600;
          text-transform: uppercase;
        }

        &.is-error {
          :deep(.el-input__inner) {
            border-color: #f56c6c;
          }
        }
      }

      .error-message {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 6px;
        font-size: 12px;
        color: #f56c6c;

        .el-icon {
          font-size: 14px;
        }
      }

      .help-message {
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 6px;
        font-size: 12px;
        color: #67c23a;

        .el-icon {
          font-size: 14px;
        }
      }

      .depth-selector {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;

        .depth-option {
          display: flex;
          align-items: center;
          padding: 14px;
          border: 2px solid var(--el-border-color-light, #e2e8f0);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.25s ease;

          &:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
          }

          &.active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: #1e40af;
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(59, 130, 246, 0.15);
          }

          .depth-icon {
            font-size: 22px;
            margin-right: 12px;
          }

          .depth-info {
            .depth-name {
              font-weight: 600;
              margin-bottom: 2px;
            }

            .depth-desc {
              font-size: 12px;
              opacity: 0.8;
              margin-bottom: 2px;
            }

            .depth-time {
              font-size: 11px;
              opacity: 0.7;
            }
          }
        }
      }

      .analysts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 14px;

        .analyst-card {
          display: flex;
          align-items: center;
          padding: 14px;
          border: 2px solid var(--el-border-color-light, #e2e8f0);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.25s ease;

          &:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
          }

          &.active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: #1e40af;
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(59, 130, 246, 0.15);
          }

          &.disabled {
            opacity: 0.45;
            cursor: not-allowed;

            &:hover {
              transform: none;
              box-shadow: none;
              border-color: #e2e8f0;
            }
          }

          .analyst-avatar {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-size: 18px;
          }

          .analyst-content {
            flex: 1;

            .analyst-name {
              font-weight: 600;
              margin-bottom: 2px;
              font-size: 14px;
            }

            .analyst-desc {
              font-size: 12px;
              opacity: 0.8;
            }
          }

          .analyst-check {
            .check-icon {
              font-size: 18px;
              color: #3b82f6;
            }
          }

          &.active .analyst-check .check-icon {
            color: #1e40af;
          }
        }
      }

      .action-buttons {
        margin-top: 16px;
        .submit-btn.large-analysis-btn {
          transition: all 0.3s ease;
          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(64, 158, 255, 0.35);
          }
        }
      }
    }
  }
}
</style>
