<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="86%"
    top="4vh"
    destroy-on-close
    class="tech-indicator-dialog"
  >
    <div v-loading="loading" class="dialog-content">
      <!-- 1. 顶部：股票行情与多因子综合评级横幅 -->
      <div v-if="snapshot" class="summary-banner">
        <div class="stock-meta">
          <div class="meta-title">
            <span class="stock-name">{{ snapshot.name }}</span>
            <span class="stock-code">{{ snapshot.code }}</span>
            <el-tag size="small" effect="plain" class="market-tag">{{ snapshot.market }}</el-tag>
          </div>
          <div class="meta-price">
            <span class="price-label">最新收盘价:</span>
            <span class="price-num">¥ {{ snapshot.close ? Number(snapshot.close).toFixed(2) : '--' }}</span>
            <span class="trade-date">交易日: {{ snapshot.trade_date }}</span>
          </div>
        </div>

        <div class="rating-box">
          <div class="rating-badge" :class="ratingBadgeClass">
            <div class="score">{{ snapshot.overall.score }}分</div>
            <div class="rating-text">{{ snapshot.overall.rating }}</div>
          </div>
          <div class="rating-counts">
            <el-tag type="danger" size="small" effect="light">🔴 看多 {{ snapshot.overall.bullish_count }} 项</el-tag>
            <el-tag type="success" size="small" effect="light">🟢 看空 {{ snapshot.overall.bearish_count }} 项</el-tag>
            <el-tag type="info" size="small" effect="light">⚪ 中性 {{ snapshot.overall.neutral_count }} 项</el-tag>
          </div>
        </div>
      </div>

      <!-- 2. 方案1核心：全套技术指标多维度诊断卡片组 -->
      <div v-if="snapshot" class="indicator-cards-grid">
        <!-- MACD 卡片 -->
        <div class="indicator-card">
          <div class="card-header">
            <span class="card-title">📈 MACD 趋势动能</span>
            <el-tag :type="getTagType(snapshot.macd.type)" size="small" effect="dark">
              {{ snapshot.macd.signal }}
            </el-tag>
          </div>
          <div class="card-body">
            <div class="val-row">
              <span class="val-item"><b>DIF:</b> {{ snapshot.macd.dif }}</span>
              <span class="val-item"><b>DEA:</b> {{ snapshot.macd.dea }}</span>
              <span class="val-item">
                <b>柱状值:</b>
                <span :class="snapshot.macd.macd_hist >= 0 ? 'text-up' : 'text-down'">
                  {{ snapshot.macd.macd_hist }}
                </span>
              </span>
            </div>
            <div class="status-desc">
              <span class="badge-dot" :class="snapshot.macd.type"></span>
              柱体态势：<b>{{ snapshot.macd.hist_trend }}</b>
            </div>
          </div>
        </div>

        <!-- RSI 卡片 -->
        <div class="indicator-card">
          <div class="card-header">
            <span class="card-title">⚡ RSI 相对强弱</span>
            <el-tag :type="getTagType(snapshot.rsi.type)" size="small" effect="dark">
              {{ snapshot.rsi.status }}
            </el-tag>
          </div>
          <div class="card-body">
            <div class="val-row">
              <span class="val-item"><b>RSI(6):</b> <span class="highlight">{{ snapshot.rsi.rsi6 }}</span></span>
              <span class="val-item"><b>RSI(12):</b> {{ snapshot.rsi.rsi12 }}</span>
              <span class="val-item"><b>RSI(24):</b> {{ snapshot.rsi.rsi24 }}</span>
            </div>
            <div class="rsi-progress-bar">
              <div class="rsi-fill" :style="{ width: `${Math.min(Math.max(snapshot.rsi.rsi6, 0), 100)}%`, background: getRsiColor(snapshot.rsi.rsi6) }"></div>
              <div class="mark line-20">20超卖</div>
              <div class="mark line-80">80超买</div>
            </div>
          </div>
        </div>

        <!-- KDJ 卡片 -->
        <div class="indicator-card">
          <div class="card-header">
            <span class="card-title">🎯 KDJ 随机摆动</span>
            <el-tag :type="getTagType(snapshot.kdj.type)" size="small" effect="dark">
              {{ snapshot.kdj.signal }}
            </el-tag>
          </div>
          <div class="card-body">
            <div class="val-row">
              <span class="val-item"><b>K:</b> {{ snapshot.kdj.k }}</span>
              <span class="val-item"><b>D:</b> {{ snapshot.kdj.d }}</span>
              <span class="val-item"><b>J:</b> <span class="highlight">{{ snapshot.kdj.j }}</span></span>
            </div>
            <div class="status-desc">
              <span class="badge-dot" :class="snapshot.kdj.type"></span>
              交叉特征：<b>{{ snapshot.kdj.is_golden_cross ? '✨ 低位金叉形成' : snapshot.kdj.is_death_cross ? '⚠️ 高位死叉承压' : '正常运行波动' }}</b>
            </div>
          </div>
        </div>

        <!-- BOLL 布林带卡片 -->
        <div class="indicator-card">
          <div class="card-header">
            <span class="card-title">🌐 BOLL 波动通道</span>
            <el-tag :type="getTagType(snapshot.boll.type)" size="small" effect="dark">
              {{ snapshot.boll.signal }}
            </el-tag>
          </div>
          <div class="card-body">
            <div class="val-row">
              <span class="val-item"><b>上轨:</b> {{ snapshot.boll.upper }}</span>
              <span class="val-item"><b>中轨:</b> {{ snapshot.boll.mid }}</span>
              <span class="val-item"><b>下轨:</b> {{ snapshot.boll.lower }}</span>
            </div>
            <div class="status-desc">
              <span class="badge-dot" :class="snapshot.boll.type"></span>
              通道带宽: <b>{{ snapshot.boll.bandwidth }}%</b> · 价格通道相对位置: <b>{{ snapshot.boll.position_pct }}%</b>
            </div>
          </div>
        </div>

        <!-- 均线系统 MA 卡片 -->
        <div class="indicator-card">
          <div class="card-header">
            <span class="card-title">📊 MA 均线系统</span>
            <el-tag :type="getTagType(snapshot.ma.type)" size="small" effect="dark">
              {{ snapshot.ma.arrangement }}
            </el-tag>
          </div>
          <div class="card-body">
            <div class="val-row">
              <span class="val-item"><span class="ma-dot ma5"></span>MA5: {{ snapshot.ma.ma5 }}</span>
              <span class="val-item"><span class="ma-dot ma10"></span>MA10: {{ snapshot.ma.ma10 }}</span>
              <span class="val-item"><span class="ma-dot ma20"></span>MA20: {{ snapshot.ma.ma20 }}</span>
              <span class="val-item"><span class="ma-dot ma60"></span>MA60: {{ snapshot.ma.ma60 }}</span>
            </div>
            <div class="status-desc" v-if="snapshot.atr">
              <span>ATR真实波幅: <b>{{ snapshot.atr.atr14 }}</b> (日波动率 <b>{{ snapshot.atr.volatility_ratio }}%</b>)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 方案2核心：专业级交互式技术图表 (主图K线+均线/布林带 + 副图MACD/RSI/KDJ/VOL) -->
      <div class="chart-section">
        <div class="chart-toolbar">
          <div class="toolbar-left">
            <span class="section-title">📊 专业技术分析交互图表</span>
            <el-radio-group v-model="period" size="small" @change="fetchData">
              <el-radio-button label="day">日K线</el-radio-button>
              <el-radio-button label="week">周K线</el-radio-button>
            </el-radio-group>
          </div>

          <div class="toolbar-right">
            <div class="ctrl-item">
              <span class="ctrl-label">主图叠加:</span>
              <el-radio-group v-model="mainIndicator" size="small">
                <el-radio-button label="ma">MA 均线组</el-radio-button>
                <el-radio-button label="boll">BOLL 布林带</el-radio-button>
                <el-radio-button label="none">纯K线</el-radio-button>
              </el-radio-group>
            </div>

            <div class="ctrl-item">
              <span class="ctrl-label">副图指标:</span>
              <el-radio-group v-model="subIndicator" size="small">
                <el-radio-button label="macd">MACD</el-radio-button>
                <el-radio-button label="rsi">RSI</el-radio-button>
                <el-radio-button label="kdj">KDJ</el-radio-button>
                <el-radio-button label="vol">成交量 VOL</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>

        <!-- ECharts 容器 -->
        <div class="chart-container">
          <v-chart
            v-if="chartOption"
            class="tech-chart"
            :option="chartOption"
            autoresize
          />
          <el-empty v-else description="暂无图表数据" />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">关闭</el-button>
        <el-button type="primary" :icon="Cpu" @click="goToDeepAnalysis">
          前往智能深度研判
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { stocksApi, type TechnicalSnapshot, type TechnicalIndicatorBar } from '@/api/stocks'

import { use as echartsUse } from 'echarts/core'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
  TitleComponent,
  MarkLineComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import type { EChartsOption } from 'echarts'

echartsUse([
  CandlestickChart,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
  TitleComponent,
  MarkLineComponent,
  CanvasRenderer
])

const router = useRouter()

const visible = ref(false)
const loading = ref(false)
const currentCode = ref('')
const currentName = ref('')
const period = ref<'day' | 'week'>('day')
const mainIndicator = ref<'ma' | 'boll' | 'none'>('ma')
const subIndicator = ref<'macd' | 'rsi' | 'kdj' | 'vol'>('macd')

const snapshot = ref<TechnicalSnapshot | null>(null)
const series = ref<TechnicalIndicatorBar[]>([])

const dialogTitle = computed(() => {
  if (currentName.value) {
    return `技术指标全景诊断与交互行情 - ${currentName.value} (${currentCode.value})`
  }
  return `技术指标全景诊断与交互行情 - ${currentCode.value}`
})

const ratingBadgeClass = computed(() => {
  if (!snapshot.value) return 'neutral'
  const t = snapshot.value.overall.type
  return t === 'bullish' ? 'rating-bullish' : t === 'bearish' ? 'rating-bearish' : 'rating-neutral'
})

function getTagType(type?: string): 'success' | 'warning' | 'danger' | 'info' {
  if (type === 'bullish') return 'danger' // A股红涨/看多
  if (type === 'bearish') return 'success' // A股绿跌/看空
  return 'info'
}

function getRsiColor(val: number): string {
  if (val >= 80) return '#ef4444'
  if (val >= 65) return '#f97316'
  if (val <= 20) return '#10b981'
  if (val <= 35) return '#06b6d4'
  return '#3b82f6'
}

// 供外部打开调用
const open = (code: string, name?: string) => {
  currentCode.value = code
  currentName.value = name || ''
  visible.value = true
  fetchData()
}

defineExpose({ open })

const fetchData = async () => {
  if (!currentCode.value) return
  loading.value = true
  try {
    const res = await stocksApi.getIndicators(currentCode.value, period.value, 120)
    if (res.data) {
      snapshot.value = res.data.snapshot
      series.value = res.data.series || []
      if (!currentName.value && res.data.name) {
        currentName.value = res.data.name
      }
    }
  } catch (err: any) {
    ElMessage.error(err?.message || '获取技术指标数据失败')
  } finally {
    loading.value = false
  }
}

// 监听指标切换重新组装 ECharts Option
const chartOption = computed<EChartsOption | null>(() => {
  if (!series.value || series.value.length === 0) return null

  const s = series.value
  const times = s.map(item => item.time)
  const kData = s.map(item => [item.open, item.close, item.low, item.high])
  const volumes = s.map(item => ({
    value: item.volume,
    itemStyle: {
      color: (item.close ?? 0) >= (item.open ?? 0) ? '#ef4444' : '#16a34a'
    }
  }))

  // 构造主图指标线
  const mainSeries: any[] = [
    {
      type: 'candlestick',
      name: 'K线',
      data: kData,
      itemStyle: {
        color: '#ef4444',
        color0: '#16a34a',
        borderColor: '#ef4444',
        borderColor0: '#16a34a'
      }
    }
  ]

  if (mainIndicator.value === 'ma') {
    mainSeries.push(
      { type: 'line', name: 'MA5', data: s.map(i => i.ma5), itemStyle: { color: '#eab308' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } },
      { type: 'line', name: 'MA10', data: s.map(i => i.ma10), itemStyle: { color: '#3b82f6' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } },
      { type: 'line', name: 'MA20', data: s.map(i => i.ma20), itemStyle: { color: '#a855f7' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } },
      { type: 'line', name: 'MA60', data: s.map(i => i.ma60), itemStyle: { color: '#06b6d4' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } }
    )
  } else if (mainIndicator.value === 'boll') {
    mainSeries.push(
      { type: 'line', name: 'BOLL上轨', data: s.map(i => i.boll_upper), itemStyle: { color: '#ec4899' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5, type: 'dashed' } },
      { type: 'line', name: 'BOLL中轨', data: s.map(i => i.boll_mid), itemStyle: { color: '#3b82f6' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5 } },
      { type: 'line', name: 'BOLL下轨', data: s.map(i => i.boll_lower), itemStyle: { color: '#10b981' }, smooth: true, symbol: 'none', lineStyle: { width: 1.5, type: 'dashed' } }
    )
  }

  // 构造副图指标
  const subSeries: any[] = []
  if (subIndicator.value === 'macd') {
    subSeries.push(
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'bar',
        name: 'MACD柱',
        data: s.map(i => ({
          value: i.macd_hist,
          itemStyle: { color: (i.macd_hist ?? 0) >= 0 ? '#ef4444' : '#16a34a' }
        }))
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'DIF',
        data: s.map(i => i.dif),
        itemStyle: { color: '#3b82f6' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'DEA',
        data: s.map(i => i.dea),
        itemStyle: { color: '#f59e0b' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      }
    )
  } else if (subIndicator.value === 'rsi') {
    subSeries.push(
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI6',
        data: s.map(i => i.rsi6),
        itemStyle: { color: '#ec4899' },
        symbol: 'none',
        lineStyle: { width: 1.5 },
        markLine: {
          symbol: 'none',
          data: [
            { yAxis: 80, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: '80 超买' } },
            { yAxis: 20, lineStyle: { color: '#10b981', type: 'dashed' }, label: { formatter: '20 超卖' } }
          ]
        }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI12',
        data: s.map(i => i.rsi12),
        itemStyle: { color: '#3b82f6' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI24',
        data: s.map(i => i.rsi24),
        itemStyle: { color: '#a855f7' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      }
    )
  } else if (subIndicator.value === 'kdj') {
    subSeries.push(
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'K',
        data: s.map(i => i.kdj_k),
        itemStyle: { color: '#f59e0b' },
        symbol: 'none',
        lineStyle: { width: 1.5 },
        markLine: {
          symbol: 'none',
          data: [
            { yAxis: 80, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: '80' } },
            { yAxis: 20, lineStyle: { color: '#10b981', type: 'dashed' }, label: { formatter: '20' } }
          ]
        }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'D',
        data: s.map(i => i.kdj_d),
        itemStyle: { color: '#3b82f6' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'J',
        data: s.map(i => i.kdj_j),
        itemStyle: { color: '#ec4899' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      }
    )
  } else if (subIndicator.value === 'vol') {
    subSeries.push({
      xAxisIndex: 1,
      yAxisIndex: 1,
      type: 'bar',
      name: '成交量',
      data: volumes
    })
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }]
    },
    legend: {
      top: 5,
      left: 'center',
      textStyle: { fontSize: 12 }
    },
    grid: [
      { left: '4%', right: '3%', top: '10%', height: '52%' },
      { left: '4%', right: '3%', top: '68%', height: '24%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: times,
        gridIndex: 0,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisLabel: { show: false }
      },
      {
        type: 'category',
        data: times,
        gridIndex: 1,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisLabel: { fontSize: 11, color: '#64748b' }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { show: true, lineStyle: { color: '#f1f5f9' } }
      },
      {
        scale: true,
        gridIndex: 1,
        splitLine: { show: true, lineStyle: { color: '#f1f5f9' } }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: 4, height: 18, start: 60, end: 100 }
    ],
    series: [...mainSeries, ...subSeries]
  }
})

const goToDeepAnalysis = () => {
  visible.value = false
  router.push({
    path: '/analysis/single',
    query: {
      code: currentCode.value,
      name: currentName.value,
      market: 'CN'
    }
  })
}
</script>

<style scoped lang="scss">
.tech-indicator-dialog {
  :deep(.el-dialog__body) {
    padding: 14px 20px;
    background: #f8fafc;
  }
}

.summary-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  border-radius: 10px;
  padding: 14px 20px;
  margin-bottom: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  .stock-meta {
    .meta-title {
      display: flex;
      align-items: center;
      gap: 10px;
      .stock-name {
        font-size: 20px;
        font-weight: 700;
        color: #1e293b;
      }
      .stock-code {
        font-size: 15px;
        color: #64748b;
        font-family: monospace;
      }
    }
    .meta-price {
      margin-top: 6px;
      font-size: 13px;
      color: #64748b;
      display: flex;
      align-items: center;
      gap: 12px;
      .price-num {
        font-size: 18px;
        font-weight: 700;
        color: #ef4444;
      }
    }
  }

  .rating-box {
    display: flex;
    align-items: center;
    gap: 16px;

    .rating-badge {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 6px 16px;
      border-radius: 8px;
      min-width: 90px;
      color: #fff;
      font-weight: 700;

      .score {
        font-size: 20px;
      }
      .rating-text {
        font-size: 12px;
      }

      &.rating-bullish {
        background: linear-gradient(135deg, #ef4444, #dc2626);
      }
      &.rating-bearish {
        background: linear-gradient(135deg, #10b981, #059669);
      }
      &.rating-neutral {
        background: linear-gradient(135deg, #64748b, #475569);
      }
    }

    .rating-counts {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
  }
}

.indicator-cards-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 14px;

  @media (max-width: 1200px) {
    grid-template-columns: repeat(3, 1fr);
  }
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }

  .indicator-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      .card-title {
        font-size: 13px;
        font-weight: 600;
        color: #334155;
      }
    }

    .card-body {
      font-size: 12px;

      .val-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        color: #475569;
        margin-bottom: 6px;

        .val-item {
          b {
            color: #1e293b;
          }
          .highlight {
            font-weight: 700;
            color: #2563eb;
          }
        }
      }

      .status-desc {
        font-size: 11px;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 4px;

        .badge-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          &.bullish { background: #ef4444; }
          &.bearish { background: #10b981; }
          &.neutral { background: #94a3b8; }
        }
      }

      .rsi-progress-bar {
        position: relative;
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
        margin-top: 6px;
        .rsi-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.3s;
        }
        .mark {
          position: absolute;
          top: -12px;
          font-size: 9px;
          color: #94a3b8;
          transform: translateX(-50%);
          &.line-20 { left: 20%; }
          &.line-80 { left: 80%; }
        }
      }

      .ma-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 3px;
        &.ma5 { background: #eab308; }
        &.ma10 { background: #3b82f6; }
        &.ma20 { background: #a855f7; }
        &.ma60 { background: #06b6d4; }
      }
    }
  }
}

.chart-section {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;

  .chart-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f1f5f9;

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 14px;
      .section-title {
        font-size: 14px;
        font-weight: 700;
        color: #1e293b;
      }
    }

    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;

      .ctrl-item {
        display: flex;
        align-items: center;
        gap: 6px;
        .ctrl-label {
          font-size: 12px;
          color: #64748b;
        }
      }
    }
  }

  .chart-container {
    height: 440px;
    width: 100%;
    .tech-chart {
      width: 100%;
      height: 100%;
    }
  }
}

.text-up {
  color: #ef4444;
  font-weight: 600;
}
.text-down {
  color: #16a34a;
  font-weight: 600;
}
</style>
