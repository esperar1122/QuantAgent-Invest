<template>
  <div class="market-trend-container" ref="containerRef">
    <!-- 头部：标题与指数快速切换 -->
    <div class="trend-header">
      <div class="trend-title-area">
        <div class="title-row">
          <h4 class="box-title">主要指数分时走势</h4>
          <span class="pulse-tag" :class="tradingState.class">
            <span class="dot"></span>
            {{ tradingState.text }}
          </span>
        </div>
        <span class="sub-label">全天 240 分钟真实交易脉络 · 分时均线 · 实时量柱</span>
      </div>

      <!-- 切换查看指数 -->
      <div class="index-switcher">
        <button
          v-for="item in indexOptions"
          :key="item.key"
          class="switch-btn"
          :class="{ active: currentIndex === item.key }"
          @click="selectIndex(item.key)"
        >
          <span class="btn-name">{{ item.name }}</span>
          <span class="btn-val" :class="item.change >= 0 ? 'up' : 'down'">
            {{ item.change >= 0 ? '+' : '' }}{{ item.change.toFixed(2) }}%
          </span>
        </button>
      </div>
    </div>

    <!-- 顶部行情/悬浮信息条 (HUD) -->
    <div class="trend-hud">
      <template v-if="hoverPoint">
        <div class="hud-item time-badge">
          <span class="label">时间:</span>
          <span class="val font-mono">{{ hoverPoint.time }}</span>
        </div>
        <div class="hud-item">
          <span class="label">分时价:</span>
          <span class="val font-mono" :class="hoverPoint.change >= 0 ? 'up' : 'down'">
            {{ hoverPoint.price.toFixed(2) }}
          </span>
        </div>
        <div class="hud-item">
          <span class="label">涨跌:</span>
          <span class="val font-mono" :class="hoverPoint.change >= 0 ? 'up' : 'down'">
            {{ hoverPoint.change >= 0 ? '+' : '' }}{{ hoverPoint.change.toFixed(2) }} ({{ hoverPoint.pct_chg >= 0 ? '+' : '' }}{{ hoverPoint.pct_chg.toFixed(2) }}%)
          </span>
        </div>
        <div class="hud-item">
          <span class="label">均价(黄线):</span>
          <span class="val font-mono text-warning">
            {{ hoverPoint.avg_price.toFixed(2) }}
          </span>
        </div>
        <div class="hud-item" v-if="hoverPoint.volume">
          <span class="label">分量:</span>
          <span class="val font-mono">
            {{ formatVolume(hoverPoint.volume) }}
          </span>
        </div>
      </template>
      <template v-else>
        <div class="hud-item">
          <span class="label">{{ currentMeta.name }}</span>
          <span class="val font-mono text-lg" :class="currentMeta.change >= 0 ? 'up' : 'down'">
            {{ currentMeta.currentPrice.toFixed(2) }}
          </span>
        </div>
        <div class="hud-item">
          <span class="label">涨跌:</span>
          <span class="val font-mono" :class="currentMeta.change >= 0 ? 'up' : 'down'">
            {{ currentMeta.change >= 0 ? '+' : '' }}{{ currentMeta.change.toFixed(2) }} ({{ currentMeta.changePercent >= 0 ? '+' : '' }}{{ currentMeta.changePercent.toFixed(2) }}%)
          </span>
        </div>
        <div class="hud-item">
          <span class="label">最高:</span>
          <span class="val font-mono up">{{ currentMeta.high.toFixed(2) }}</span>
        </div>
        <div class="hud-item">
          <span class="label">最低:</span>
          <span class="val font-mono down">{{ currentMeta.low.toFixed(2) }}</span>
        </div>
        <div class="hud-item">
          <span class="label">昨收基准:</span>
          <span class="val font-mono text-muted">{{ currentMeta.prevClose.toFixed(2) }}</span>
        </div>
        <div class="hud-item" v-if="currentMeta.totalAmount">
          <span class="label">成交额:</span>
          <span class="val font-mono">{{ formatAmount(currentMeta.totalAmount) }}</span>
        </div>
      </template>
    </div>

    <!-- SVG 绘制高保真分时走势图与量柱副图 -->
    <div
      class="svg-chart-wrapper"
      ref="wrapperRef"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onMouseLeave"
    >
      <svg
        class="trend-svg"
        viewBox="0 0 720 278"
        preserveAspectRatio="none"
      >
        <defs>
          <!-- 渐变填充 (多头红 / 科技蓝) -->
          <linearGradient id="areaGradientBlue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1570EF" stop-opacity="0.22" />
            <stop offset="60%" stop-color="#1570EF" stop-opacity="0.08" />
            <stop offset="100%" stop-color="#1570EF" stop-opacity="0.0" />
          </linearGradient>

          <!-- 呼吸发光滤镜 -->
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <!-- ================= 主图网格系统 (Y: 20 ~ 190) ================= -->
        <!-- 上界线 (+Max) -->
        <line x1="10" y1="20" x2="710" y2="20" stroke="#FEE4E2" stroke-width="1" stroke-dasharray="2 2" />
        <!-- 上四分之一线 -->
        <line x1="10" y1="62.5" x2="710" y2="62.5" stroke="#F2F4F7" stroke-width="1" />
        <!-- 零轴昨收基准线 (0.00%) -->
        <line x1="10" y1="105" x2="710" y2="105" stroke="#D0D5DD" stroke-width="1.2" stroke-dasharray="4 3" />
        <!-- 下四分之一线 -->
        <line x1="10" y1="147.5" x2="710" y2="147.5" stroke="#F2F4F7" stroke-width="1" />
        <!-- 下界线 (-Max) -->
        <line x1="10" y1="190" x2="710" y2="190" stroke="#D1FADF" stroke-width="1" stroke-dasharray="2 2" />

        <!-- 垂直时间分割线 (09:30, 10:30, 11:30/13:00午休, 14:00, 15:00) -->
        <line x1="10" y1="20" x2="10" y2="190" stroke="#EAECF0" stroke-width="1" />
        <line x1="185" y1="20" x2="185" y2="190" stroke="#F2F4F7" stroke-width="1" stroke-dasharray="2 2" />
        <line x1="360" y1="20" x2="360" y2="190" stroke="#D0D5DD" stroke-width="1.2" />
        <line x1="535" y1="20" x2="535" y2="190" stroke="#F2F4F7" stroke-width="1" stroke-dasharray="2 2" />
        <line x1="710" y1="20" x2="710" y2="190" stroke="#EAECF0" stroke-width="1" />

        <!-- 主图左侧点位标签 -->
        <text x="14" y="32" font-size="10" fill="#D92D20" font-weight="600" font-family="'JetBrains Mono', monospace">
          {{ scalePrices.top.toFixed(2) }}
        </text>
        <text x="14" y="101" font-size="10" fill="#667085" font-family="'JetBrains Mono', monospace">
          昨收 {{ currentMeta.prevClose.toFixed(2) }}
        </text>
        <text x="14" y="186" font-size="10" fill="#039855" font-weight="600" font-family="'JetBrains Mono', monospace">
          {{ scalePrices.bottom.toFixed(2) }}
        </text>

        <!-- 主图右侧涨跌幅标签 -->
        <text x="706" y="32" font-size="10" fill="#D92D20" font-weight="600" text-anchor="end" font-family="'JetBrains Mono', monospace">
          +{{ (currentMeta.maxRatio * 100).toFixed(2) }}%
        </text>
        <text x="706" y="101" font-size="10" fill="#667085" text-anchor="end" font-family="'JetBrains Mono', monospace">
          0.00%
        </text>
        <text x="706" y="186" font-size="10" fill="#039855" font-weight="600" text-anchor="end" font-family="'JetBrains Mono', monospace">
          -{{ (currentMeta.maxRatio * 100).toFixed(2) }}%
        </text>

        <!-- 分时走势面积填充 -->
        <path :d="areaPath" fill="url(#areaGradientBlue)" />

        <!-- 分时走势白线/蓝线 (价格曲线) -->
        <path
          :d="pricePath"
          fill="none"
          stroke="#1570EF"
          stroke-width="1.8"
          stroke-linejoin="round"
          stroke-linecap="round"
        />

        <!-- 分时均价线 (黄色均线) -->
        <path
          v-if="avgPath"
          :d="avgPath"
          fill="none"
          stroke="#F79009"
          stroke-width="1.3"
          stroke-linejoin="round"
          stroke-linecap="round"
          stroke-dasharray="none"
        />

        <!-- 最新成交价动态呼吸光点 -->
        <g v-if="latestActivePoint" class="pulsing-group">
          <!-- 扩散波纹 -->
          <circle
            :cx="latestActivePoint.x"
            :cy="latestActivePoint.y"
            r="7"
            fill="#1570EF"
            opacity="0.3"
            :class="{ 'wave-circle': isTradingNow }"
          />
          <!-- 实体中心点 -->
          <circle
            :cx="latestActivePoint.x"
            :cy="latestActivePoint.y"
            r="3"
            fill="#1570EF"
            stroke="#ffffff"
            stroke-width="2"
          />
        </g>

        <!-- ================= 副图：分时成交量 (Y: 202 ~ 248) ================= -->
        <!-- 副图分割线 -->
        <line x1="10" y1="202" x2="710" y2="202" stroke="#EAECF0" stroke-width="1" />
        <line x1="360" y1="202" x2="360" y2="248" stroke="#D0D5DD" stroke-width="1" />
        <line x1="10" y1="248" x2="710" y2="248" stroke="#EAECF0" stroke-width="1" />

        <!-- 副图标签 -->
        <text x="14" y="214" font-size="9" fill="#98A2B3" font-family="'JetBrains Mono', monospace">
          成交量 (手)
        </text>
        <text x="706" y="214" font-size="9" fill="#98A2B3" text-anchor="end" font-family="'JetBrains Mono', monospace">
          峰值: {{ formatVolume(maxVolume) }}
        </text>

        <!-- 每分钟成交量柱条 -->
        <g class="volume-bars">
          <line
            v-for="(pt, idx) in processedDataSeries"
            :key="idx"
            :x1="pt.x"
            :y1="248"
            :x2="pt.x"
            :y2="getVolumeY(pt.volume)"
            :stroke="pt.is_up ? '#D92D20' : '#039855'"
            stroke-width="1.8"
            stroke-linecap="butt"
          />
        </g>

        <!-- ================= 交互十字光标标线 ================= -->
        <g v-if="hoverPoint" class="crosshair-layer">
          <!-- 垂直虚线 (贯穿主图与副图) -->
          <line
            :x1="hoverPoint.x"
            y1="20"
            :x2="hoverPoint.x"
            y2="248"
            stroke="#175CD3"
            stroke-width="1"
            stroke-dasharray="3 2"
          />
          <!-- 水平价格指示线 -->
          <line
            x1="10"
            :y1="hoverPoint.y"
            x2="710"
            :y2="hoverPoint.y"
            stroke="#175CD3"
            stroke-width="1"
            stroke-dasharray="3 2"
          />
          <!-- 价格线吸附亮点 -->
          <circle
            :cx="hoverPoint.x"
            :cy="hoverPoint.y"
            r="4"
            fill="#1570EF"
            stroke="#ffffff"
            stroke-width="2"
          />
          <!-- 均线吸附亮点 -->
          <circle
            v-if="hoverPoint.avg_y"
            :cx="hoverPoint.x"
            :cy="hoverPoint.avg_y"
            r="3"
            fill="#F79009"
            stroke="#ffffff"
            stroke-width="1.5"
          />

          <!-- 坐标轴浮动标记气泡 -->
          <!-- 左侧价格标记 -->
          <rect
            :x="2"
            :y="hoverPoint.y - 8"
            width="46"
            height="16"
            rx="2"
            fill="#175CD3"
          />
          <text
            :x="25"
            :y="hoverPoint.y + 4"
            fill="#ffffff"
            font-size="9"
            font-family="'JetBrains Mono', monospace"
            text-anchor="middle"
          >
            {{ hoverPoint.price.toFixed(2) }}
          </text>

          <!-- 右侧百分比标记 -->
          <rect
            :x="666"
            :y="hoverPoint.y - 8"
            width="50"
            height="16"
            rx="2"
            fill="#175CD3"
          />
          <text
            :x="691"
            :y="hoverPoint.y + 4"
            fill="#ffffff"
            font-size="9"
            font-family="'JetBrains Mono', monospace"
            text-anchor="middle"
          >
            {{ hoverPoint.pct_chg >= 0 ? '+' : '' }}{{ hoverPoint.pct_chg.toFixed(2) }}%
          </text>

          <!-- 底部时间轴吸附标记 (高保真吸附) -->
          <rect
            :x="Math.max(4, Math.min(668, hoverPoint.x - 24))"
            y="253"
            width="48"
            height="16"
            rx="2"
            fill="#175CD3"
          />
          <text
            :x="Math.max(28, Math.min(692, hoverPoint.x))"
            y="265"
            fill="#ffffff"
            font-size="9.5"
            font-weight="600"
            font-family="'JetBrains Mono', monospace"
            text-anchor="middle"
          >
            {{ hoverPoint.time }}
          </text>
        </g>

        <!-- ================= X 轴时间刻度 (集成在 SVG 底部，永不偏移) ================= -->
        <g class="time-axis-labels">
          <text x="10" y="265" font-size="10" fill="#98A2B3" font-family="'JetBrains Mono', monospace">09:30</text>
          <text x="185" y="265" font-size="10" fill="#98A2B3" text-anchor="middle" font-family="'JetBrains Mono', monospace">10:30</text>
          <text x="360" y="265" font-size="10" fill="#64748B" font-weight="600" text-anchor="middle" font-family="'JetBrains Mono', monospace">11:30 / 13:00</text>
          <text x="535" y="265" font-size="10" fill="#98A2B3" text-anchor="middle" font-family="'JetBrains Mono', monospace">14:00</text>
          <text x="710" y="265" font-size="10" fill="#98A2B3" text-anchor="end" font-family="'JetBrains Mono', monospace">15:00</text>
        </g>
      </svg>

      <!-- 悬浮吸附详细提示卡 (Tooltip) -->
      <div
        v-if="hoverPoint"
        class="chart-tooltip"
        :style="{ left: hoverTooltipLeft + 'px', top: '24px' }"
      >
        <div class="tt-header">
          <span class="tt-time">{{ hoverPoint.time }}</span>
          <span class="tt-tag" :class="hoverPoint.change >= 0 ? 'up' : 'down'">
            {{ hoverPoint.pct_chg >= 0 ? '+' : '' }}{{ hoverPoint.pct_chg.toFixed(2) }}%
          </span>
        </div>
        <div class="tt-body">
          <div class="tt-row">
            <span class="label">分时价格</span>
            <span class="val font-mono" :class="hoverPoint.change >= 0 ? 'up' : 'down'">
              {{ hoverPoint.price.toFixed(2) }}
            </span>
          </div>
          <div class="tt-row">
            <span class="label">均价(黄线)</span>
            <span class="val font-mono text-warning">
              {{ hoverPoint.avg_price.toFixed(2) }}
            </span>
          </div>
          <div class="tt-row" v-if="hoverPoint.volume">
            <span class="label">分钟成交</span>
            <span class="val font-mono">
              {{ formatVolume(hoverPoint.volume) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { stocksApi } from '@/api/stocks'

interface IndexMeta {
  key: string
  code: string
  name: string
  change: number
  changePercent: number
  currentPrice: number
  prevClose: number
  high: number
  low: number
  maxRatio: number
  totalAmount: number
  items: any[]
}

const indexOptions = ref<IndexMeta[]>([
  {
    key: 'sh',
    code: 'sh000001',
    name: '上证指数',
    change: -12.80,
    changePercent: -0.33,
    currentPrice: 3923.72,
    prevClose: 3936.52,
    high: 3929.53,
    low: 3921.49,
    maxRatio: 0.008,
    totalAmount: 182500000000,
    items: []
  },
  {
    key: 'sz',
    code: 'sz399001',
    name: '深证成指',
    change: -113.57,
    changePercent: -0.83,
    currentPrice: 13522.50,
    prevClose: 13636.07,
    high: 13575.15,
    low: 13521.73,
    maxRatio: 0.012,
    totalAmount: 215000000000,
    items: []
  },
  {
    key: 'cyb',
    code: 'sz399006',
    name: '创业板指',
    change: -31.35,
    changePercent: -0.93,
    currentPrice: 3348.26,
    prevClose: 3379.61,
    high: 3368.66,
    low: 3348.08,
    maxRatio: 0.015,
    totalAmount: 98000000000,
    items: []
  },
  {
    key: 'kcb',
    code: 'sh000688',
    name: '科创50',
    change: -20.33,
    changePercent: -1.22,
    currentPrice: 1640.52,
    prevClose: 1660.85,
    high: 1650.98,
    low: 1640.12,
    maxRatio: 0.018,
    totalAmount: 43000000000,
    items: []
  }
])

const currentIndex = ref('sh')

const currentMeta = computed(() => {
  return indexOptions.value.find(i => i.key === currentIndex.value) || indexOptions.value[0]
})

// 判断当前处于A股的哪种交易状态
const tradingState = computed(() => {
  const now = new Date()
  const day = now.getDay()
  if (day === 0 || day === 6) return { text: '休市(周末)', class: 'closed' }
  const mins = now.getHours() * 60 + now.getMinutes()
  if (mins < 9 * 60 + 15) return { text: '未开盘', class: 'closed' }
  if (mins >= 9 * 60 + 15 && mins <= 11 * 60 + 30) return { text: '盘中实时', class: 'live' }
  if (mins > 11 * 60 + 30 && mins < 13 * 60) return { text: '午间休市', class: 'break' }
  if (mins >= 13 * 60 && mins <= 15 * 60 + 2) return { text: '盘中实时', class: 'live' }
  return { text: '已收盘', class: 'closed' }
})

const isTradingNow = computed(() => tradingState.value.class === 'live')

// 时间转为 X 坐标索引 (0 ~ 240)
function timeToMinuteIndex(timeStr: string): number {
  if (!timeStr) return 0
  const parts = timeStr.split(':')
  if (parts.length < 2) return 0
  const h = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10)

  if (h === 9 && m >= 30) {
    return m - 30
  } else if (h === 10) {
    return 30 + m
  } else if (h === 11 && m <= 30) {
    return 90 + m
  } else if (h === 13) {
    return 120 + m
  } else if (h === 14) {
    return 180 + m
  } else if (h === 15 && m === 0) {
    return 240
  } else if (h < 9 || (h === 9 && m < 30)) {
    return 0
  } else if (h >= 15) {
    return 240
  }
  return 0
}

// 格式化辅助
function formatVolume(vol: number): string {
  if (!vol || isNaN(vol)) return '0'
  if (vol >= 100000000) return (vol / 100000000).toFixed(2) + '亿'
  if (vol >= 10000) return (vol / 10000).toFixed(1) + '万'
  return vol.toFixed(0)
}

function formatAmount(amt: number): string {
  if (!amt || isNaN(amt)) return '0'
  if (amt >= 100000000) return (amt / 100000000).toFixed(1) + ' 亿元'
  if (amt >= 10000) return (amt / 10000).toFixed(1) + ' 万元'
  return amt.toFixed(0) + ' 元'
}

// 主图刻度价格
const scalePrices = computed(() => {
  const base = currentMeta.value.prevClose
  const ratio = currentMeta.value.maxRatio
  return {
    top: base * (1 + ratio),
    bottom: base * (1 - ratio)
  }
})

// 获取真实分时数据
async function loadTimelineData(item: IndexMeta) {
  try {
    const res = await (stocksApi as any).getTimeline(item.code)
    const d = (res as any)?.data || res
    if (d && Array.isArray(d.items) && d.items.length > 0) {
      item.prevClose = d.prev_close || item.prevClose
      item.currentPrice = d.current_price || item.currentPrice
      item.change = d.change || item.change
      item.changePercent = d.change_percent || item.changePercent
      item.high = d.high || item.high
      item.low = d.low || item.low
      item.maxRatio = Math.max(d.max_ratio || 0.005, 0.005)
      item.totalAmount = d.total_amount || item.totalAmount
      item.items = d.items
    }
  } catch (e) {
    // 若网络暂时波动，保持原数据
  }
}

// 处理好的分时坐标点 (X: 10 ~ 710, Y: 20 ~ 190, 基准 105)
const processedDataSeries = computed(() => {
  const meta = currentMeta.value
  const raw = meta.items
  const base = meta.prevClose || meta.currentPrice
  const ratio = meta.maxRatio || 0.008

  // 若暂无真实数据，提供平滑基准点
  const list = raw.length > 0 ? raw : [
    { time: '09:30', price: base, avg_price: base, volume: 0, change: 0, pct_chg: 0, is_up: true }
  ]

  const mapped = list.map((pt: any) => {
    const minIdx = timeToMinuteIndex(pt.time)
    // X 坐标：0 ~ 240 映射到 10 ~ 710
    const x = 10 + (minIdx / 240) * 700

    // Y 坐标：昨收位于 y=105，±ratio 映射到 ±85px (即 20 ~ 190)
    const priceDiff = pt.price - base
    const pricePctRatio = base > 0 ? (priceDiff / base) / ratio : 0
    const y = Math.max(20, Math.min(190, 105 - pricePctRatio * 85))

    const avgDiff = pt.avg_price - base
    const avgPctRatio = base > 0 ? (avgDiff / base) / ratio : 0
    const avg_y = Math.max(20, Math.min(190, 105 - avgPctRatio * 85))

    return {
      x,
      y,
      avg_y,
      time: pt.time,
      price: pt.price,
      avg_price: pt.avg_price,
      volume: pt.volume || 0,
      change: pt.change !== undefined ? pt.change : (pt.price - base),
      pct_chg: pt.pct_chg !== undefined ? pt.pct_chg : ((pt.price - base) / base * 100),
      is_up: pt.is_up !== undefined ? pt.is_up : (pt.price >= base)
    }
  })

  return mapped
})

// 最大成交量
const maxVolume = computed(() => {
  const pts = processedDataSeries.value
  if (!pts.length) return 1000
  let maxV = 1000
  for (const p of pts) {
    if (p.volume > maxV) maxV = p.volume
  }
  return maxV
})

// 计算副图成交量 Y 轴坐标
function getVolumeY(vol: number): number {
  if (!vol || vol <= 0) return 247
  const maxV = maxVolume.value
  const h = Math.min(44, Math.max(2, (vol / maxV) * 44))
  return 248 - h
}

// 价格线 Path
const pricePath = computed(() => {
  const pts = processedDataSeries.value
  if (!pts.length) return ''
  return pts.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`
  }, '')
})

// 均价线 Path
const avgPath = computed(() => {
  const pts = processedDataSeries.value
  if (!pts.length) return ''
  return pts.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.avg_y.toFixed(1)}`
  }, '')
})

// 渐变面积填充 Path (从价格线封闭至 y=190 基准线)
const areaPath = computed(() => {
  const pts = processedDataSeries.value
  if (!pts.length) return ''
  const first = pts[0]
  const last = pts[pts.length - 1]
  const linePoints = pts.map(p => `L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  return `M ${first.x.toFixed(1)} 190 ${linePoints} L ${last.x.toFixed(1)} 190 Z`
})

// 最新的活跃交易点
const latestActivePoint = computed(() => {
  const pts = processedDataSeries.value
  if (!pts.length) return null
  return pts[pts.length - 1]
})

// 悬浮交互
const wrapperRef = ref<HTMLElement | null>(null)
const hoverPoint = ref<any>(null)
const hoverTooltipLeft = ref(0)

function updateHoverByClientX(clientX: number) {
  if (!wrapperRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  const mouseX = clientX - rect.left
  const ratio = Math.max(0, Math.min(1, mouseX / rect.width))

  const pts = processedDataSeries.value
  if (!pts.length) return

  // 沿时间轴精准吸附最近的分钟点 (X 范围 10 ~ 710)
  const targetX = 10 + ratio * 700
  let closest = pts[0]
  let minDist = 999999

  for (const p of pts) {
    const dist = Math.abs(p.x - targetX)
    if (dist < minDist) {
      minDist = dist
      closest = p
    }
  }

  hoverPoint.value = closest
  hoverTooltipLeft.value = Math.max(12, Math.min(rect.width - 180, mouseX - 75))
}

const onMouseMove = (e: MouseEvent) => {
  updateHoverByClientX(e.clientX)
}

const onTouchStart = (e: TouchEvent) => {
  if (e.touches && e.touches.length > 0) {
    updateHoverByClientX(e.touches[0].clientX)
  }
}

const onTouchMove = (e: TouchEvent) => {
  if (e.touches && e.touches.length > 0) {
    updateHoverByClientX(e.touches[0].clientX)
  }
}

const onMouseLeave = () => {
  hoverPoint.value = null
}

function selectIndex(key: string) {
  currentIndex.value = key
  const target = indexOptions.value.find(i => i.key === key)
  if (target) {
    loadTimelineData(target)
  }
}

let timer: number | null = null

onMounted(async () => {
  // 首次拉取当前指数与所有指数数据
  await Promise.allSettled(indexOptions.value.map(item => loadTimelineData(item)))
  // 定时刷新 (10秒轮询)
  timer = window.setInterval(async () => {
    const active = currentMeta.value
    if (active) {
      await loadTimelineData(active)
    }
  }, 10000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.market-trend-container {
  background: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  padding: 14px 16px 12px;
  user-select: none;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .trend-title-area {
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;

      .box-title {
        font-size: 14px;
        font-weight: 700;
        color: #101828;
        margin: 0;
      }

      .pulse-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        padding: 1px 8px;
        border-radius: 12px;
        font-weight: 500;

        &.live {
          background: #ecfdf3;
          color: #027a48;
          border: 1px solid #a6f4c5;

          .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #12b76a;
            animation: pulse-dot 1.5s infinite;
          }
        }

        &.break {
          background: #fffaeb;
          color: #b54708;
          border: 1px solid #fedf89;

          .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #f79009;
          }
        }

        &.closed {
          background: #f8fafc;
          color: #64748b;
          border: 1px solid #e2e8f0;

          .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #94a3b8;
          }
        }
      }
    }

    .sub-label {
      font-size: 11px;
      color: #667085;
      margin-top: 2px;
      display: block;
    }
  }

  .index-switcher {
    display: flex;
    gap: 6px;

    .switch-btn {
      background: #f8fafc;
      border: 1px solid #eaecf0;
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 500;
      color: #475467;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;

      .btn-name {
        font-weight: 600;
      }

      .btn-val {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 11px;

        &.up { color: #d92d20; }
        &.down { color: #039855; }
      }

      &:hover {
        background: #f2f4f7;
        border-color: #d0d5dd;
      }

      &.active {
        background: #eff8ff;
        border-color: #84caff;
        color: #175cd3;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
      }
    }
  }
}

.trend-hud {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  background: #f8fafc;
  border: 1px solid #eaecf0;
  border-radius: 6px;
  padding: 6px 12px;
  margin-bottom: 8px;
  font-size: 11px;

  .hud-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;

    .label {
      color: #667085;
      font-weight: 500;
    }

    .val {
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;

      &.up { color: #d92d20; }
      &.down { color: #039855; }
      &.text-warning { color: #b54708; }
      &.text-muted { color: #475467; }
      &.text-lg { font-size: 13px; }
    }

    &.time-badge {
      background: #eff8ff;
      border: 1px solid #b2ddff;
      padding: 1px 6px;
      border-radius: 4px;
      color: #175cd3;
      font-weight: 600;
    }
  }
}

.svg-chart-wrapper {
  position: relative;
  width: 100%;
  height: 236px;

  .trend-svg {
    width: 100%;
    height: 100%;
    overflow: visible;
    cursor: crosshair;
  }

  .chart-tooltip {
    position: absolute;
    background: rgba(16, 24, 40, 0.94);
    backdrop-filter: blur(4px);
    color: #ffffff;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 11px;
    pointer-events: none;
    box-shadow: 0 4px 12px rgba(16, 24, 40, 0.25);
    z-index: 20;
    white-space: nowrap;
    border: 1px solid rgba(255, 255, 255, 0.15);

    .tt-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.15);
      padding-bottom: 4px;
      margin-bottom: 6px;

      .tt-time {
        font-family: 'JetBrains Mono', monospace;
        color: #cbd5e1;
        font-weight: 600;
      }
      .tt-tag {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 3px;

        &.up { background: rgba(240, 68, 56, 0.25); color: #fda29b; }
        &.down { background: rgba(18, 183, 106, 0.25); color: #6ce9a6; }
      }
    }

    .tt-body {
      display: flex;
      flex-direction: column;
      gap: 3px;

      .tt-row {
        display: flex;
        justify-content: space-between;
        gap: 14px;

        .label {
          color: #94a3b8;
        }

        .val {
          font-family: 'JetBrains Mono', monospace;
          font-weight: 600;

          &.up { color: #f97066; }
          &.down { color: #32d583; }
          &.text-warning { color: #fdb022; }
        }
      }
    }
  }
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.8; }
}

.wave-circle {
  animation: pulse-ring 2s infinite ease-out;
}

@keyframes pulse-ring {
  0% { r: 3; opacity: 0.8; }
  100% { r: 10; opacity: 0; }
}
</style>
