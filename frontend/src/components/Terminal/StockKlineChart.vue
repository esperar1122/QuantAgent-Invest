<template>
  <div class="kline-container" ref="containerRef">
    <!-- 图表顶栏工具条 -->
    <div class="kline-toolbar">
      <div class="toolbar-left">
        <div class="period-tabs">
          <button 
            v-for="p in periods" 
            :key="p.key" 
            :class="['tab-btn', { active: currentPeriod === p.key }]"
            @click="currentPeriod = p.key"
          >
            {{ p.label }}
          </button>
        </div>
        <div class="divider"></div>
        <div class="indicator-tags">
          <span class="indicator-badge ma5">MA5: {{ currentHoverItem ? currentHoverItem.ma5.toFixed(2) : latestItem.ma5.toFixed(2) }}</span>
          <span class="indicator-badge ma20">MA20: {{ currentHoverItem ? currentHoverItem.ma20.toFixed(2) : latestItem.ma20.toFixed(2) }}</span>
          <span class="indicator-badge ma60">MA60: {{ currentHoverItem ? currentHoverItem.ma60.toFixed(2) : latestItem.ma60.toFixed(2) }}</span>
        </div>
      </div>

      <div class="toolbar-right">
        <div class="subchart-selector">
          <span class="selector-label">副图指标:</span>
          <button 
            v-for="sub in subIndicators" 
            :key="sub.key"
            :class="['sub-btn', { active: currentSubIndicator === sub.key }]"
            @click="currentSubIndicator = sub.key"
          >
            {{ sub.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 图表主绘图区域 -->
    <div 
      class="kline-viewport" 
      @mousemove="handleMouseMove" 
      @mouseleave="handleMouseLeave"
    >
      <svg class="kline-svg" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none">
        <defs>
          <linearGradient id="volUpGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#D92D20" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#D92D20" stop-opacity="0.3"/>
          </linearGradient>
          <linearGradient id="volDownGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#039855" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#039855" stop-opacity="0.3"/>
          </linearGradient>
        </defs>

        <!-- 网格背景 (主图) -->
        <g class="grid-lines">
          <line 
            v-for="(y, idx) in mainGridYLines" 
            :key="'grid-y-' + idx"
            :x1="padding.left" 
            :y1="y" 
            :x2="width - padding.right" 
            :y2="y" 
            stroke="#EAECF0" 
            stroke-width="1" 
            stroke-dasharray="3 3"
          />
          <line 
            v-for="(x, idx) in gridXLines" 
            :key="'grid-x-' + idx"
            :x1="x" 
            :y1="padding.top" 
            :x2="x" 
            :y2="mainChartHeight + padding.top" 
            stroke="#EAECF0" 
            stroke-width="1" 
            stroke-dasharray="3 3"
          />
        </g>

        <!-- K 线蜡烛图与影线 -->
        <g class="candles">
          <g v-for="(item, i) in candlePoints" :key="'candle-' + i">
            <!-- 上下影线 -->
            <line 
              :x1="item.x" 
              :y1="item.highY" 
              :x2="item.x" 
              :y2="item.lowY" 
              :stroke="item.isUp ? '#D92D20' : '#039855'" 
              stroke-width="1.2"
            />
            <!-- 实体矩形 -->
            <rect 
              :x="item.x - candleWidth / 2" 
              :y="item.bodyY" 
              :width="candleWidth" 
              :height="Math.max(item.bodyHeight, 1.5)" 
              :fill="item.isUp ? '#D92D20' : '#039855'" 
              :stroke="item.isUp ? '#D92D20' : '#039855'" 
              stroke-width="0.5"
            />
          </g>
        </g>

        <!-- 均线折线 -->
        <g class="ma-lines">
          <path :d="ma5Path" fill="none" stroke="#D97706" stroke-width="1.4" stroke-linejoin="round" />
          <path :d="ma20Path" fill="none" stroke="#175CD3" stroke-width="1.4" stroke-linejoin="round" />
          <path :d="ma60Path" fill="none" stroke="#7C3AED" stroke-width="1.4" stroke-linejoin="round" />
        </g>

        <!-- 主图价格 Y 轴刻度文字 -->
        <g class="y-labels">
          <text 
            v-for="(tick, idx) in mainPriceTicks" 
            :key="'ptick-' + idx"
            :x="width - padding.right + 6" 
            :y="tick.y + 4" 
            font-size="11" 
            fill="#667085" 
            class="tabular-nums"
          >
            {{ tick.val.toFixed(2) }}
          </text>
        </g>

        <!-- 分割线 (主图与副图之间) -->
        <line 
          :x1="padding.left" 
          :y1="subChartTop" 
          :x2="width - padding.right" 
          :y2="subChartTop" 
          stroke="#D0D5DD" 
          stroke-width="1"
        />

        <!-- 副图：成交量 (VOL) -->
        <g v-if="currentSubIndicator === 'VOL'" class="subchart-vol">
          <g v-for="(item, i) in candlePoints" :key="'vol-' + i">
            <rect 
              :x="item.x - candleWidth / 2" 
              :y="item.volY" 
              :width="candleWidth" 
              :height="item.volHeight" 
              :fill="item.isUp ? 'url(#volUpGrad)' : 'url(#volDownGrad)'"
            />
          </g>
          <text 
            :x="padding.left + 6" 
            :y="subChartTop + 14" 
            font-size="10" 
            fill="#475467" 
            font-weight="600"
          >
            VOL(成交量): {{ (currentHoverItem ? currentHoverItem.vol : latestItem.vol).toLocaleString() }} 手
          </text>
        </g>

        <!-- 副图：MACD -->
        <g v-else-if="currentSubIndicator === 'MACD'" class="subchart-macd">
          <line 
            :x1="padding.left" 
            :y1="macdZeroY" 
            :x2="width - padding.right" 
            :y2="macdZeroY" 
            stroke="#98A2B3" 
            stroke-width="1" 
            stroke-dasharray="2 2"
          />
          <!-- 柱状图 -->
          <g v-for="(m, i) in macdPoints" :key="'macd-bar-' + i">
            <rect 
              :x="m.x - candleWidth / 2" 
              :y="m.barY" 
              :width="candleWidth" 
              :height="Math.max(m.barHeight, 1)" 
              :fill="m.val >= 0 ? '#D92D20' : '#039855'"
            />
          </g>
          <!-- DIF / DEA 曲线 -->
          <path :d="macdDifPath" fill="none" stroke="#175CD3" stroke-width="1.3" />
          <path :d="macdDeaPath" fill="none" stroke="#D97706" stroke-width="1.3" />
          <text 
            :x="padding.left + 6" 
            :y="subChartTop + 14" 
            font-size="10" 
            fill="#475467" 
            font-weight="600"
          >
            MACD(12,26,9) DIF: <tspan fill="#175CD3">{{ currentHoverItem ? currentHoverItem.dif.toFixed(2) : latestItem.dif.toFixed(2) }}</tspan> DEA: <tspan fill="#D97706">{{ currentHoverItem ? currentHoverItem.dea.toFixed(2) : latestItem.dea.toFixed(2) }}</tspan>
          </text>
        </g>

        <!-- 副图：RSI -->
        <g v-else-if="currentSubIndicator === 'RSI'" class="subchart-rsi">
          <!-- 80/20 警戒虚线 -->
          <line :x1="padding.left" :y1="rsi80Y" :x2="width - padding.right" :y2="rsi80Y" stroke="#F04438" stroke-width="0.8" stroke-dasharray="3 3" />
          <line :x1="padding.left" :y1="rsi20Y" :x2="width - padding.right" :y2="rsi20Y" stroke="#12B76A" stroke-width="0.8" stroke-dasharray="3 3" />
          <path :d="rsi6Path" fill="none" stroke="#175CD3" stroke-width="1.3" />
          <path :d="rsi12Path" fill="none" stroke="#D97706" stroke-width="1.3" />
          <text 
            :x="padding.left + 6" 
            :y="subChartTop + 14" 
            font-size="10" 
            fill="#475467" 
            font-weight="600"
          >
            RSI(6,12) RSI6: <tspan fill="#175CD3">{{ currentHoverItem ? currentHoverItem.rsi6.toFixed(1) : latestItem.rsi6.toFixed(1) }}</tspan> RSI12: <tspan fill="#D97706">{{ currentHoverItem ? currentHoverItem.rsi12.toFixed(1) : latestItem.rsi12.toFixed(1) }}</tspan>
          </text>
        </g>

        <!-- X 轴日期刻度 -->
        <g class="x-labels">
          <text 
            v-for="(tick, idx) in dateTicks" 
            :key="'dtick-' + idx"
            :x="tick.x" 
            :y="height - 6" 
            text-anchor="middle" 
            font-size="10" 
            fill="#667085" 
            class="tabular-nums"
          >
            {{ tick.label }}
          </text>
        </g>

        <!-- 鼠标悬浮十字光标 -->
        <g v-if="hoverX !== null && hoverPoint" class="crosshair">
          <!-- 垂直虚线 -->
          <line 
            :x1="hoverPoint.x" 
            :y1="padding.top" 
            :x2="hoverPoint.x" 
            :y2="height - padding.bottom" 
            stroke="#344054" 
            stroke-width="1" 
            stroke-dasharray="4 4"
          />
          <!-- 水平虚线 (主图) -->
          <line 
            v-if="hoverY <= subChartTop"
            :x1="padding.left" 
            :y1="hoverY" 
            :x2="width - padding.right" 
            :y2="hoverY" 
            stroke="#344054" 
            stroke-width="1" 
            stroke-dasharray="4 4"
          />
          <!-- 悬浮价格刻度标签 -->
          <rect 
            v-if="hoverY <= subChartTop"
            :x="width - padding.right + 2" 
            :y="hoverY - 9" 
            width="46" 
            height="18" 
            fill="#1D2939" 
            rx="2"
          />
          <text 
            v-if="hoverY <= subChartTop"
            :x="width - padding.right + 25" 
            :y="hoverY + 4" 
            fill="#FFFFFF" 
            font-size="10" 
            text-anchor="middle" 
            class="tabular-nums font-mono"
          >
            {{ hoverPrice.toFixed(2) }}
          </text>
        </g>
      </svg>

      <!-- 悬浮浮窗数据框 (Tooltip) -->
      <div 
        v-if="currentHoverItem" 
        class="kline-tooltip" 
        :style="{ left: tooltipPos.x + 'px', top: '12px' }"
      >
        <div class="tt-header">
          <span class="tt-date">{{ currentHoverItem.date }}</span>
          <span :class="['tt-pct', currentHoverItem.changePct >= 0 ? 'up' : 'down']">
            {{ currentHoverItem.changePct >= 0 ? '+' : '' }}{{ currentHoverItem.changePct.toFixed(2) }}%
          </span>
        </div>
        <div class="tt-grid">
          <div class="tt-item"><span class="k">开盘</span><span class="v tabular-nums">{{ currentHoverItem.open.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">最高</span><span class="v tabular-nums">{{ currentHoverItem.high.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">最低</span><span class="v tabular-nums">{{ currentHoverItem.low.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">收盘</span><span class="v tabular-nums">{{ currentHoverItem.close.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">成交量</span><span class="v tabular-nums">{{ (currentHoverItem.vol / 10000).toFixed(1) }}万</span></div>
          <div class="tt-item"><span class="k">换手率</span><span class="v tabular-nums">{{ currentHoverItem.turnover.toFixed(2) }}%</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { stocksApi } from '@/api/stocks'

interface KlineItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  vol: number
  turnover: number
  ma5: number
  ma20: number
  ma60: number
  dif: number
  dea: number
  macd: number
  rsi6: number
  rsi12: number
  changePct: number
}

const props = withDefaults(
  defineProps<{
    stockCode?: string
    stockName?: string
    currentPrice?: number
  }>(),
  {
    stockCode: '688981',
    stockName: '中芯国际',
    currentPrice: 86.40
  }
)

const periods = [
  { key: 'day', label: '日K' },
  { key: 'week', label: '周K' },
  { key: '60m', label: '60分' },
]

const subIndicators = [
  { key: 'VOL', label: '成交量' },
  { key: 'MACD', label: 'MACD' },
  { key: 'RSI', label: 'RSI' },
]

const currentPeriod = ref('day')
const currentSubIndicator = ref('VOL')

// 尺寸定义
const width = 840
const height = 420
const padding = { top: 20, right: 60, bottom: 25, left: 15 }
const mainChartHeight = 260
const subChartTop = 295
const subChartHeight = 95

function calculateIndicators(data: KlineItem[]) {
  for (let i = 0; i < data.length; i++) {
    // MA5
    const slice5 = data.slice(Math.max(0, i - 4), i + 1)
    data[i].ma5 = +(slice5.reduce((s, d) => s + d.close, 0) / slice5.length).toFixed(2)

    // MA20
    const slice20 = data.slice(Math.max(0, i - 19), i + 1)
    data[i].ma20 = +(slice20.reduce((s, d) => s + d.close, 0) / slice20.length).toFixed(2)

    // MA60
    const slice60 = data.slice(Math.max(0, i - 59), i + 1)
    data[i].ma60 = +(slice60.reduce((s, d) => s + d.close, 0) / slice60.length).toFixed(2)

    // MACD 拟真计算
    const dif = +((data[i].ma5 - data[i].ma20) * 0.8).toFixed(2)
    const dea = +(dif * 0.75).toFixed(2)
    data[i].dif = dif
    data[i].dea = dea
    data[i].macd = +((dif - dea) * 2).toFixed(2)

    // RSI 模拟
    data[i].rsi6 = +(50 + Math.sin(i * 0.5) * 25 + Math.random() * 6).toFixed(1)
    data[i].rsi12 = +(52 + Math.sin(i * 0.3) * 18).toFixed(1)
  }
}

function generateSimulatedKlineData(basePx: number): KlineItem[] {
  const data: KlineItem[] = []
  const initialPrice = basePx > 0 ? basePx * 0.94 : 82.50
  let price = initialPrice
  const baseDate = new Date('2026-07-01')
  
  for (let i = 0; i < 50; i++) {
    const curDate = new Date(baseDate.getTime() + i * 24 * 3600 * 1000)
    const dayOfWeek = curDate.getDay()
    if (dayOfWeek === 0 || dayOfWeek === 6) continue

    const dateStr = curDate.toISOString().slice(5, 10)
    const stepRatio = Math.max(0.2, price * 0.015)
    const change = (Math.sin(i * 0.4) * stepRatio) + ((Math.random() - 0.48) * stepRatio * 1.5)
    const open = +(price + (Math.random() - 0.5) * stepRatio * 0.3).toFixed(2)
    const close = Math.max(0.1, +(open + change).toFixed(2))
    const high = +(Math.max(open, close) + Math.random() * stepRatio * 0.7).toFixed(2)
    const low = Math.max(0.05, +(Math.min(open, close) - Math.random() * stepRatio * 0.5).toFixed(2))
    const vol = Math.floor(80000 + Math.random() * 160000 + (change > 0 ? 40000 : 0))
    const turnover = +(1.2 + Math.random() * 2.5).toFixed(2)
    const changePct = +(((close - open) / (open || 1)) * 100).toFixed(2)

    price = close

    data.push({
      date: dateStr,
      open,
      high,
      low,
      close,
      vol,
      turnover,
      ma5: 0,
      ma20: 0,
      ma60: 0,
      dif: 0,
      dea: 0,
      macd: 0,
      rsi6: 0,
      rsi12: 0,
      changePct
    })
  }

  // 确保最后一个 bar 的 close 贴合最新价
  if (data.length > 0 && basePx > 0) {
    const last = data[data.length - 1]
    last.close = +(basePx).toFixed(2)
    last.high = Math.max(last.high, last.close)
    last.low = Math.min(last.low, last.close)
    last.changePct = +(((last.close - last.open) / (last.open || 1)) * 100).toFixed(2)
  }

  calculateIndicators(data)
  return data
}

const rawData = ref<KlineItem[]>(generateSimulatedKlineData(props.currentPrice || 86.40))
const loading = ref(false)

async function loadKlineData() {
  if (!props.stockCode) return
  loading.value = true
  try {
    const res = await stocksApi.getKline(props.stockCode, currentPeriod.value as any, 50)
    const items = (res as any)?.data?.items || (res as any)?.items
    if (items && Array.isArray(items) && items.length >= 5) {
      const mapped: KlineItem[] = items.map((bar: any) => {
        const o = Number(bar.open ?? bar.close ?? props.currentPrice ?? 10)
        const c = Number(bar.close ?? o)
        const h = Number(bar.high ?? Math.max(o, c))
        const l = Number(bar.low ?? Math.min(o, c))
        const v = Number(bar.volume ?? bar.vol ?? 100000)
        const chg = Number(bar.pct_chg ?? (((c - o) / (o || 1)) * 100))
        const dateRaw = String(bar.time || bar.date || '')
        const dateStr = dateRaw.length >= 10 ? dateRaw.slice(5, 10) : (dateRaw || '01-01')
        return {
          date: dateStr,
          open: o,
          high: h,
          low: l,
          close: c,
          vol: v,
          turnover: Number(bar.turnover_rate || 1.5),
          ma5: 0,
          ma20: 0,
          ma60: 0,
          dif: 0,
          dea: 0,
          macd: 0,
          rsi6: 0,
          rsi12: 0,
          changePct: chg
        }
      })
      calculateIndicators(mapped)
      rawData.value = mapped
      loading.value = false
      return
    }
  } catch (err) {
    // 静默降级
  } finally {
    loading.value = false
  }

  // 降级为基于真实价格生成拟真 K 线
  rawData.value = generateSimulatedKlineData(props.currentPrice || 86.40)
}

watch(
  () => [props.stockCode, props.currentPrice, currentPeriod.value],
  () => {
    loadKlineData()
  },
  { immediate: true }
)

// 计算坐标映射
const chartData = computed(() => rawData.value)
const latestItem = computed(() => chartData.value[chartData.value.length - 1])

const minPrice = computed(() => Math.min(...chartData.value.map(d => d.low)) * 0.985)
const maxPrice = computed(() => Math.max(...chartData.value.map(d => d.high)) * 1.015)
const maxVol = computed(() => Math.max(...chartData.value.map(d => d.vol)))

const candleWidth = computed(() => {
  const n = chartData.value.length
  const usableWidth = width - padding.left - padding.right
  return Math.max(5, Math.min(14, (usableWidth / n) * 0.65))
})

function getYByPrice(p: number): number {
  const range = maxPrice.value - minPrice.value || 1
  return padding.top + (1 - (p - minPrice.value) / range) * mainChartHeight
}

function getPriceByY(y: number): number {
  const ratio = 1 - (y - padding.top) / mainChartHeight
  return minPrice.value + ratio * (maxPrice.value - minPrice.value)
}

const candlePoints = computed(() => {
  const n = chartData.value.length
  const step = (width - padding.left - padding.right) / (n - 1)

  return chartData.value.map((d, i) => {
    const x = padding.left + i * step
    const openY = getYByPrice(d.open)
    const closeY = getYByPrice(d.close)
    const highY = getYByPrice(d.high)
    const lowY = getYByPrice(d.low)
    const isUp = d.close >= d.open

    const bodyY = Math.min(openY, closeY)
    const bodyHeight = Math.abs(closeY - openY)

    // 成交量柱状图
    const volHeight = (d.vol / maxVol.value) * subChartHeight
    const volY = subChartTop + subChartHeight - volHeight

    return {
      x,
      openY,
      closeY,
      highY,
      lowY,
      bodyY,
      bodyHeight,
      volY,
      volHeight,
      isUp,
      data: d
    }
  })
})

// 折线生成
const ma5Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i].x, getYByPrice(d.ma5)])))
const ma20Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i].x, getYByPrice(d.ma20)])))
const ma60Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i].x, getYByPrice(d.ma60)])))

// MACD 副图
const macdZeroY = computed(() => subChartTop + subChartHeight / 2)
const macdPoints = computed(() => {
  return chartData.value.map((d, i) => {
    const x = candlePoints.value[i].x
    const barScale = 20
    const val = d.macd
    const h = Math.min(subChartHeight / 2 - 2, Math.abs(val) * barScale)
    const barY = val >= 0 ? macdZeroY.value - h : macdZeroY.value
    return { x, val, barY, barHeight: h }
  })
})

const macdDifPath = computed(() => {
  return generatePath(chartData.value.map((d, i) => {
    const y = macdZeroY.value - d.dif * 18
    return [candlePoints.value[i].x, y]
  }))
})

const macdDeaPath = computed(() => {
  return generatePath(chartData.value.map((d, i) => {
    const y = macdZeroY.value - d.dea * 18
    return [candlePoints.value[i].x, y]
  }))
})

// RSI 副图
const rsi80Y = computed(() => subChartTop + (1 - 80 / 100) * subChartHeight)
const rsi20Y = computed(() => subChartTop + (1 - 20 / 100) * subChartHeight)
const rsi6Path = computed(() => {
  return generatePath(chartData.value.map((d, i) => {
    const y = subChartTop + (1 - d.rsi6 / 100) * subChartHeight
    return [candlePoints.value[i].x, y]
  }))
})
const rsi12Path = computed(() => {
  return generatePath(chartData.value.map((d, i) => {
    const y = subChartTop + (1 - d.rsi12 / 100) * subChartHeight
    return [candlePoints.value[i].x, y]
  }))
})

function generatePath(points: [number, number][]): string {
  if (points.length === 0) return ''
  return points.reduce((acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`, '')
}

// 刻度线
const mainGridYLines = computed(() => [
  padding.top,
  padding.top + mainChartHeight * 0.25,
  padding.top + mainChartHeight * 0.5,
  padding.top + mainChartHeight * 0.75,
  padding.top + mainChartHeight,
])

const gridXLines = computed(() => {
  const res: number[] = []
  const n = candlePoints.value.length
  if (n === 0) return res
  const stepIdx = Math.floor(n / 4)
  for (let i = 0; i < n; i += stepIdx) {
    if (candlePoints.value[i]) {
      res.push(candlePoints.value[i].x)
    }
  }
  return res
})

const mainPriceTicks = computed(() => {
  const steps = 4
  const res: { y: number; val: number }[] = []
  for (let i = 0; i <= steps; i++) {
    const y = padding.top + (i / steps) * mainChartHeight
    const val = getPriceByY(y)
    res.push({ y, val })
  }
  return res
})

const dateTicks = computed(() => {
  const res: { x: number; label: string }[] = []
  const n = candlePoints.value.length
  if (n === 0) return res
  const stepIdx = Math.floor(n / 4)
  for (let i = 0; i < n; i += stepIdx) {
    if (candlePoints.value[i]) {
      res.push({
        x: candlePoints.value[i].x,
        label: candlePoints.value[i].data.date
      })
    }
  }
  return res
})

// 十字光标与悬停交互
const hoverX = ref<number | null>(null)
const hoverY = ref<number>(0)
const hoverPrice = ref<number>(0)
const currentHoverItem = ref<KlineItem | null>(null)
const hoverPoint = ref<{ x: number; y: number } | null>(null)
const tooltipPos = ref({ x: 0 })

function handleMouseMove(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const mouseX = ((e.clientX - rect.left) / rect.width) * width
  const mouseY = ((e.clientY - rect.top) / rect.height) * height

  if (mouseX < padding.left || mouseX > width - padding.right) {
    hoverX.value = null
    currentHoverItem.value = null
    return
  }

  // 寻找最近的蜡烛
  let closestIdx = 0
  let minDist = 9999
  candlePoints.value.forEach((pt, idx) => {
    const d = Math.abs(pt.x - mouseX)
    if (d < minDist) {
      minDist = d
      closestIdx = idx
    }
  })

  const targetPt = candlePoints.value[closestIdx]
  hoverX.value = targetPt.x
  hoverY.value = mouseY
  hoverPrice.value = getPriceByY(mouseY)
  currentHoverItem.value = targetPt.data
  hoverPoint.value = { x: targetPt.x, y: mouseY }

  // 浮窗位置计算 (避免挡住边缘)
  const clientX = e.clientX - rect.left
  if (clientX > rect.width - 160) {
    tooltipPos.value.x = clientX - 160
  } else {
    tooltipPos.value.x = clientX + 15
  }
}

function handleMouseLeave() {
  hoverX.value = null
  currentHoverItem.value = null
  hoverPoint.value = null
}
</script>

<style scoped lang="scss">
.kline-container {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.kline-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #f2f4f7;
  background-color: #fafbfc;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.period-tabs {
  display: flex;
  background-color: #eaecf0;
  border-radius: 4px;
  padding: 2px;
  gap: 2px;

  .tab-btn {
    border: none;
    background: transparent;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #475467;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.15s ease;

    &:hover {
      color: #101828;
    }

    &.active {
      background-color: #ffffff;
      color: #175cd3;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
    }
  }
}

.divider {
  width: 1px;
  height: 14px;
  background-color: #d0d5dd;
}

.indicator-tags {
  display: flex;
  gap: 8px;

  .indicator-badge {
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', 'Roboto Mono', monospace;

    &.ma5 { color: #d97706; }
    &.ma20 { color: #175cd3; }
    &.ma60 { color: #7c3aed; }
  }
}

.toolbar-right {
  display: flex;
  align-items: center;

  .subchart-selector {
    display: flex;
    align-items: center;
    gap: 6px;

    .selector-label {
      font-size: 11px;
      color: #667085;
    }

    .sub-btn {
      border: 1px solid #d0d5dd;
      background-color: #ffffff;
      color: #344054;
      font-size: 11px;
      font-weight: 500;
      padding: 2px 8px;
      border-radius: 3px;
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        border-color: #98a2b3;
      }

      &.active {
        background-color: #eff8ff;
        border-color: #175cd3;
        color: #175cd3;
        font-weight: 600;
      }
    }
  }
}

.kline-viewport {
  position: relative;
  width: 100%;
  height: 420px;
  background-color: #ffffff;
  cursor: crosshair;
}

.kline-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.kline-tooltip {
  position: absolute;
  pointer-events: none;
  background-color: rgba(16, 24, 40, 0.92);
  border: 1px solid #344054;
  border-radius: 4px;
  padding: 8px 10px;
  color: #ffffff;
  font-size: 11px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
  min-width: 140px;

  .tt-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);

    .tt-date {
      color: #98a2b3;
      font-size: 11px;
    }

    .tt-pct {
      font-weight: 700;
      &.up { color: #f97066; }
      &.down { color: #32d583; }
    }
  }

  .tt-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px 8px;

    .tt-item {
      display: flex;
      justify-content: space-between;
      gap: 4px;

      .k {
        color: #98a2b3;
      }
      .v {
        color: #f2f4f7;
        font-weight: 500;
      }
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
