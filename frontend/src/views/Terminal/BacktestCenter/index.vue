<template>
  <div class="backtest-center-view">
    <!-- 顶部状态栏 -->
    <div class="bc-header-banner">
      <div class="banner-title-group">
        <span class="bc-badge">A-SHARE QUANT ENGINE</span>
        <h1 class="bc-title">策略历史回测中心</h1>
        <span class="bc-subtitle">严格遵循 A 股规则 · T+1 撮合约束 · 涨跌停限制 · 真实交易摩擦成本</span>
      </div>
      <div class="banner-quick-actions">
        <el-button size="small" type="primary" plain @click="loadPreset('600519', 'dual_ma')">
          茅台 · 双均线回测
        </el-button>
        <el-button size="small" type="primary" plain @click="loadPreset('300750', 'macd')">
          宁德时代 · MACD回测
        </el-button>
        <el-button size="small" type="primary" plain @click="loadPreset('510300', 'bollinger')">
          300ETF · 布林带回归
        </el-button>
      </div>
    </div>

    <!-- 主工作区：左侧参数配置 + 右侧绩效曲线与明细 -->
    <div class="bc-workspace-grid">
      <!-- 左栏：回测控制台 (360px) -->
      <aside class="bc-control-col">
        <el-card shadow="never" class="control-card">
          <div class="card-section-title">1. 选择回测策略</div>
          <el-select v-model="form.strategy_name" class="full-width" @change="onStrategyChange">
            <el-option label="📈 双均线金叉死叉策略 (Dual MA)" value="dual_ma" />
            <el-option label="🌊 MACD 动量趋势策略 (MACD)" value="macd" />
            <el-option label="🎯 布林带均值回归策略 (Bollinger)" value="bollinger" />
          </el-select>
          <div class="strategy-desc-box">
            {{ currentStrategyDesc }}
          </div>

          <div class="card-section-title" style="margin-top: 14px;">2. 回测标的与周期</div>
          <el-form label-position="top" size="small">
            <el-form-item label="股票/ETF代码">
              <el-input v-model="form.symbol" placeholder="如 600519、300750、510300" />
            </el-form-item>

            <el-form-item label="初始回测本金 (元)">
              <el-input-number
                v-model="form.initial_capital"
                :min="10000"
                :max="100000000"
                :step="10000"
                class="full-width"
              />
            </el-form-item>

            <el-form-item label="回测时间区间">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                class="full-width"
              />
              <div class="quick-date-chips">
                <el-button size="small" link @click="setQuickDateRange(1)">最近 1 年</el-button>
                <el-button size="small" link @click="setQuickDateRange(2)">最近 2 年</el-button>
                <el-button size="small" link @click="setQuickDateRange(3)">最近 3 年</el-button>
              </div>
            </el-form-item>
          </el-form>

          <div class="card-section-title" style="margin-top: 10px;">3. 策略专用参数</div>
          <el-form label-position="top" size="small">
            <!-- 双均线参数 -->
            <template v-if="form.strategy_name === 'dual_ma'">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="快线周期 (日)">
                    <el-input-number v-model="strategyParams.fast_period" :min="2" :max="60" class="full-width" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="慢线周期 (日)">
                    <el-input-number v-model="strategyParams.slow_period" :min="5" :max="250" class="full-width" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- MACD参数 -->
            <template v-else-if="form.strategy_name === 'macd'">
              <el-row :gutter="10">
                <el-col :span="8">
                  <el-form-item label="快线(12)">
                    <el-input-number v-model="strategyParams.fast" :min="2" :max="30" class="full-width" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="慢线(26)">
                    <el-input-number v-model="strategyParams.slow" :min="10" :max="60" class="full-width" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="信号(9)">
                    <el-input-number v-model="strategyParams.signal" :min="2" :max="20" class="full-width" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <!-- 布林带参数 -->
            <template v-else-if="form.strategy_name === 'bollinger'">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="布林窗口 (日)">
                    <el-input-number v-model="strategyParams.window" :min="5" :max="60" class="full-width" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="标准差倍数">
                    <el-input-number v-model="strategyParams.num_std" :min="1.0" :max="3.5" :step="0.1" class="full-width" />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>
          </el-form>

          <!-- A股交易摩擦硬性约束说明 -->
          <div class="friction-rules-box">
            <div class="fr-title">⚖️ A 股真实交易摩擦撮合规则:</div>
            <ul class="fr-list">
              <li>严格 T+1 持仓限制（买入当日不可卖出）</li>
              <li>涨停板 (10%/20%) 无法买入，跌停板无法卖出</li>
              <li>卖出单边印花税 0.05% (万5)</li>
              <li>买卖双边佣金 0.025% (万2.5，最低5元起征)</li>
              <li>双边执行滑点 0.1%</li>
            </ul>
          </div>

          <div class="action-btn-row">
            <el-button
              type="primary"
              size="large"
              :loading="running"
              @click="runBacktest"
              class="full-width-btn"
            >
              🚀 启动 A 股历史回测
            </el-button>
          </div>
        </el-card>
      </aside>

      <!-- 右栏：回测结果可视化展示区 -->
      <main class="bc-result-col" v-loading="running">
        <!-- 未运行状态引导卡 -->
        <div v-if="!result && !running" class="empty-backtest-card">
          <div class="eb-icon">📊</div>
          <h3>尚未执行回测</h3>
          <p>请在左侧选择策略并配置标的代码与参数，点击「启动 A 股历史回测」即可生成专业量化报告与净值曲线。</p>
          <div class="quick-try-row">
            <el-button type="primary" @click="runBacktest">使用默认参数立即试跑</el-button>
          </div>
        </div>

        <!-- 结果面板 -->
        <div v-if="result" class="result-dashboard">
          <!-- 1. 核心 KPI 指标卡片网格 -->
          <div class="kpi-cards-grid">
            <div class="kpi-card" :class="result.metrics.total_return >= 0 ? 'color-up-bg' : 'color-down-bg'">
              <span class="kpi-lbl">策略累计总收益率</span>
              <span class="kpi-val font-mono tabular-nums" :class="result.metrics.total_return >= 0 ? 'color-up' : 'color-down'">
                {{ result.metrics.total_return >= 0 ? '+' : '' }}{{ result.metrics.total_return.toFixed(2) }}%
              </span>
              <span class="kpi-sub">基准收益: {{ (result.metrics.benchmark_total_return || 0) >= 0 ? '+' : '' }}{{ (result.metrics.benchmark_total_return || 0).toFixed(2) }}%</span>
            </div>

            <div class="kpi-card">
              <span class="kpi-lbl">年化复合收益率 (CAGR)</span>
              <span class="kpi-val font-mono tabular-nums" :class="result.metrics.cagr >= 0 ? 'color-up' : 'color-down'">
                {{ result.metrics.cagr >= 0 ? '+' : '' }}{{ result.metrics.cagr.toFixed(2) }}%
              </span>
              <span class="kpi-sub">年化波动率: {{ result.metrics.annualized_volatility?.toFixed(2) }}%</span>
            </div>

            <div class="kpi-card danger-card">
              <span class="kpi-lbl">历史最大回撤 (Max DD)</span>
              <span class="kpi-val font-mono tabular-nums color-down">
                {{ result.metrics.max_drawdown.toFixed(2) }}%
              </span>
              <span class="kpi-sub">持续天数: {{ result.metrics.max_drawdown_duration_days }} 天</span>
            </div>

            <div class="kpi-card highlight-card">
              <span class="kpi-lbl">夏普比率 (Sharpe)</span>
              <span class="kpi-val font-mono tabular-nums" :class="result.metrics.sharpe_ratio >= 1.0 ? 'text-primary' : ''">
                {{ result.metrics.sharpe_ratio.toFixed(2) }}
              </span>
              <span class="kpi-sub">索提诺比率: {{ result.metrics.sortino_ratio?.toFixed(2) }}</span>
            </div>

            <div class="kpi-card">
              <span class="kpi-lbl">策略胜率 (Win Rate)</span>
              <span class="kpi-val font-mono tabular-nums">
                {{ result.metrics.win_rate.toFixed(1) }}%
              </span>
              <span class="kpi-sub">盈利 {{ result.metrics.profitable_trades }} 笔 / 亏损 {{ result.metrics.losing_trades }} 笔</span>
            </div>

            <div class="kpi-card">
              <span class="kpi-lbl">盈亏比 (Profit Factor)</span>
              <span class="kpi-val font-mono tabular-nums">
                {{ result.metrics.profit_factor.toFixed(2) }}
              </span>
              <span class="kpi-sub">总交易次数: {{ result.metrics.total_trades }} 笔</span>
            </div>
          </div>

          <!-- 2. ECharts 净值曲线图容器 -->
          <el-card shadow="never" class="chart-card">
            <div class="chart-header">
              <div class="ch-left">
                <span class="ch-title">📈 资产累计净值曲线 (NAV vs Benchmark)</span>
                <span class="ch-sub font-mono">标的: {{ result.symbol }} | 回测耗时: {{ result.execution_time_seconds }}s</span>
              </div>
              <div class="ch-right">
                <span class="legend-pill nav">■ 策略净值</span>
                <span class="legend-pill bm">■ 买入持有基准</span>
              </div>
            </div>
            <div ref="chartRef" class="nav-chart-view"></div>
          </el-card>

          <!-- 3. 详细交易明细与记录 -->
          <el-card shadow="never" class="table-card">
            <div class="table-header">
              <span class="th-title">📋 逐笔撮合成交流水清单 (共 {{ result.trades.length }} 笔)</span>
              <span class="th-note">所有买卖均经过 T+1 撮合校验与滑点手续费扣减</span>
            </div>

            <el-table
              :data="result.trades"
              size="small"
              style="width: 100%"
              max-height="300"
            >
              <el-table-column prop="date" label="成交日期" width="110" />
              <el-table-column prop="symbol" label="标的代码" width="90" />
              <el-table-column prop="action" label="方向" width="80">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.action === 'BUY' ? 'danger' : 'success'">
                    {{ row.action === 'BUY' ? '买入' : '卖出' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="price" label="成交价" width="90" align="right">
                <template #default="{ row }">
                  <span class="font-mono">¥{{ row.price?.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="shares" label="股数" width="90" align="right">
                <template #default="{ row }">
                  <span class="font-mono">{{ row.shares }} 股</span>
                </template>
              </el-table-column>
              <el-table-column prop="amount" label="交易金额" width="110" align="right">
                <template #default="{ row }">
                  <span class="font-mono">¥{{ row.amount?.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="fee" label="摩擦费用" width="90" align="right">
                <template #default="{ row }">
                  <span class="font-mono text-fee">¥{{ row.fee?.toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="realized_pnl" label="已实现盈亏" width="110" align="right">
                <template #default="{ row }">
                  <span v-if="row.action === 'SELL'" class="font-mono" :class="row.realized_pnl >= 0 ? 'color-up' : 'color-down'">
                    {{ row.realized_pnl >= 0 ? '+' : '' }}¥{{ row.realized_pnl?.toFixed(2) }}
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="return_pct" label="收益率" width="100" align="right">
                <template #default="{ row }">
                  <span v-if="row.action === 'SELL'" class="font-mono tabular-nums" :class="row.return_pct >= 0 ? 'color-up' : 'color-down'">
                    {{ row.return_pct >= 0 ? '+' : '' }}{{ row.return_pct?.toFixed(2) }}%
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { quantApi, type BacktestResponse } from '@/api/quant'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const route = useRoute()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const running = ref(false)
const result = ref<BacktestResponse | null>(null)

const dateRange = ref<[string, string]>(['2023-01-01', '2024-01-01'])

const form = ref({
  symbol: '600519',
  strategy_name: 'dual_ma',
  initial_capital: 100000
})

const strategyParams = ref<Record<string, any>>({
  fast_period: 5,
  slow_period: 20,
  fast: 12,
  slow: 26,
  signal: 9,
  window: 20,
  num_std: 2.0
})

const currentStrategyDesc = computed(() => {
  switch (form.value.strategy_name) {
    case 'dual_ma':
      return '经典趋势跟踪策略：短期快线自下向上穿越慢线（金叉）全仓买入，自上向下穿越慢线（死叉）坚决止损止盈清仓。'
    case 'macd':
      return '经典动量震荡策略：DIF 线上穿 DEA 信号线且柱线翻红时买入建仓，死叉且柱线翻绿时卖出离场。'
    case 'bollinger':
      return '均值回归策略：价格触及布林带下轨向上反弹时买入，触及上轨遇阻时止盈卖出。'
    default:
      return ''
  }
})

function onStrategyChange() {
  // 保持默认参数
}

function setQuickDateRange(years: number) {
  const end = new Date()
  const start = new Date()
  start.setFullYear(end.getFullYear() - years)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
}

function loadPreset(symbol: string, strategy: string) {
  form.value.symbol = symbol
  form.value.strategy_name = strategy
  runBacktest()
}

async function runBacktest() {
  if (!form.value.symbol) {
    ElMessage.warning('请输入回测标的代码')
    return
  }
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择回测时间区间')
    return
  }

  running.value = true
  try {
    const res = await quantApi.runBacktest({
      symbol: form.value.symbol,
      strategy_name: form.value.strategy_name,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      initial_capital: form.value.initial_capital,
      strategy_params: strategyParams.value
    })

    const data = ((res as any)?.data || res) as BacktestResponse
    result.value = data
    ElMessage.success('A 股规则级历史回测完成！')

    await nextTick()
    renderChart()
  } catch (err: any) {
    console.error('回测失败:', err)
    ElMessage.error(err.message || '回测执行失败，请检查网络或数据源')
  } finally {
    running.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !result.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    window.addEventListener('resize', () => chartInstance?.resize())
  }

  const dates = result.value.daily_nav.map(d => d.date)
  const navs = result.value.daily_nav.map(d => +d.nav.toFixed(3))
  const benchmarks = result.value.daily_nav.map(d => +(d.benchmark_nav || 1.0).toFixed(3))
  const drawdowns = result.value.daily_nav.map(d => -(d.drawdown_pct || 0).toFixed(2))

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: [
      { left: '4%', right: '3%', top: '10%', height: '55%' },
      { left: '4%', right: '3%', top: '72%', height: '22%' }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: dates, gridIndex: 1, boundaryGap: false }
    ],
    yAxis: [
      { type: 'value', name: '累计净值 (NAV)', gridIndex: 0, scale: true },
      { type: 'value', name: '回撤 %', gridIndex: 1, min: -50, max: 0 }
    ],
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: navs,
        xAxisIndex: 0,
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 2.5, color: '#2563eb' }
      },
      {
        name: '基准净值',
        type: 'line',
        data: benchmarks,
        xAxisIndex: 0,
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#94a3b8', type: 'dashed' }
      },
      {
        name: '动态回撤',
        type: 'line',
        data: drawdowns,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        areaStyle: { color: 'rgba(239, 68, 68, 0.35)' },
        lineStyle: { width: 1, color: '#ef4444' }
      }
    ]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  setQuickDateRange(1)
  const codeFromQuery = (route.query.code as string) || (route.query.symbol as string)
  if (codeFromQuery) {
    form.value.symbol = codeFromQuery
  }
})
</script>

<style scoped lang="scss">
.backtest-center-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 1680px;
  margin: 0 auto;
}

.bc-header-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 10px;
  color: #ffffff;

  .banner-title-group {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .bc-badge {
      font-size: 11px;
      color: #38bdf8;
      font-weight: 700;
      letter-spacing: 1px;
    }
    .bc-title {
      font-size: 20px;
      font-weight: 800;
      margin: 0;
    }
    .bc-subtitle {
      font-size: 12px;
      color: #94a3b8;
    }
  }

  .banner-quick-actions {
    display: flex;
    gap: 8px;
  }
}

.bc-workspace-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  align-items: start;
}

.control-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;

  .card-section-title {
    font-size: 13px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 8px;
  }

  .full-width {
    width: 100%;
  }

  .strategy-desc-box {
    margin-top: 8px;
    padding: 8px 10px;
    background: #f8fafc;
    border-radius: 6px;
    font-size: 11px;
    color: #64748b;
    line-height: 1.5;
  }

  .quick-date-chips {
    display: flex;
    gap: 6px;
    margin-top: 4px;
  }

  .friction-rules-box {
    margin: 12px 0 16px 0;
    padding: 10px 12px;
    background: #fffbeb;
    border: 1px solid #fef3c7;
    border-radius: 6px;

    .fr-title {
      font-size: 12px;
      font-weight: 700;
      color: #b45309;
      margin-bottom: 4px;
    }
    .fr-list {
      margin: 0;
      padding-left: 18px;
      font-size: 11px;
      color: #92400e;
      line-height: 1.6;
    }
  }

  .action-btn-row {
    .full-width-btn {
      width: 100%;
      font-weight: 700;
    }
  }
}

.bc-result-col {
  min-height: 600px;
}

.empty-backtest-card {
  text-align: center;
  padding: 80px 20px;
  background: #ffffff;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;

  .eb-icon {
    font-size: 48px;
    margin-bottom: 12px;
  }
  h3 {
    font-size: 18px;
    color: #1e293b;
    margin-bottom: 6px;
  }
  p {
    font-size: 13px;
    color: #64748b;
    max-width: 480px;
    margin: 0 auto 16px auto;
  }
}

.result-dashboard {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kpi-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;

  .kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 2px;

    .kpi-lbl {
      font-size: 12px;
      color: #64748b;
    }
    .kpi-val {
      font-size: 22px;
      font-weight: 800;
    }
    .kpi-sub {
      font-size: 11px;
      color: #94a3b8;
    }

    &.color-up-bg {
      border-left: 4px solid #ef4444;
    }
    &.color-down-bg {
      border-left: 4px solid #10b981;
    }
    &.danger-card {
      border-left: 4px solid #f97316;
    }
    &.highlight-card {
      border-left: 4px solid #2563eb;
    }
  }
}

.chart-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    .ch-title {
      font-size: 14px;
      font-weight: 700;
      color: #1e293b;
    }
    .ch-sub {
      margin-left: 10px;
      font-size: 11px;
      color: #94a3b8;
    }
    .legend-pill {
      font-size: 12px;
      margin-left: 12px;
      &.nav {
        color: #2563eb;
      }
      &.bm {
        color: #64748b;
      }
    }
  }

  .nav-chart-view {
    width: 100%;
    height: 380px;
  }
}

.table-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;

  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .th-title {
      font-size: 13px;
      font-weight: 700;
      color: #1e293b;
    }
    .th-note {
      font-size: 11px;
      color: #94a3b8;
    }
  }
}

.color-up {
  color: #ef4444;
}
.color-down {
  color: #10b981;
}
.text-fee {
  color: #94a3b8;
}
</style>
