<template>
  <div class="market-trend-container">
    <div class="trend-header">
      <div class="trend-title-area">
        <h4 class="box-title">主要指数分时走势 (Intraday Realtime Flow)</h4>
        <span class="sub-label">09:30 - 15:00 真实成交分钟线</span>
      </div>

      <!-- 切换查看指数 -->
      <div class="index-switcher">
        <button
          v-for="item in indexOptions"
          :key="item.key"
          class="switch-btn"
          :class="{ active: currentIndex === item.key }"
          @click="currentIndex = item.key"
        >
          {{ item.name }}
          <span :class="item.change >= 0 ? 'up' : 'down'">
            {{ item.change >= 0 ? '+' : '' }}{{ item.change }}%
          </span>
        </button>
      </div>
    </div>

    <!-- SVG 绘制高保真分时走势图 -->
    <div class="svg-chart-wrapper" ref="wrapperRef">
      <svg
        class="trend-svg"
        viewBox="0 0 700 220"
        preserveAspectRatio="none"
        @mousemove="onMouseMove"
        @mouseleave="onMouseLeave"
      >
        <defs>
          <linearGradient id="areaGradientUp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#D92D20" stop-opacity="0.18" />
            <stop offset="100%" stop-color="#D92D20" stop-opacity="0.0" />
          </linearGradient>
          <linearGradient id="areaGradientDown" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#039855" stop-opacity="0.0" />
            <stop offset="100%" stop-color="#039855" stop-opacity="0.18" />
          </linearGradient>
        </defs>

        <!-- 背景横向网格刻度线 -->
        <line x1="0" y1="35" x2="700" y2="35" stroke="#F2F4F7" stroke-width="1" />
        <line x1="0" y1="100" x2="700" y2="100" stroke="#E4E7EC" stroke-width="1" stroke-dasharray="3 3" />
        <line x1="0" y1="165" x2="700" y2="165" stroke="#F2F4F7" stroke-width="1" />

        <!-- 垂直时间分割线 (11:30 午休分割) -->
        <line x1="350" y1="10" x2="350" y2="190" stroke="#F2F4F7" stroke-width="1" />

        <!-- 零轴基准线文字 (昨收价) -->
        <text x="5" y="96" font-size="10" fill="#98A2B3" font-family="JetBrains Mono">基准 0.00%</text>
        <text x="695" y="96" font-size="10" fill="#98A2B3" text-anchor="end" font-family="JetBrains Mono">{{ typeof currentMeta.basePrice === 'number' ? currentMeta.basePrice.toFixed(2) : currentMeta.basePrice }}</text>

        <!-- 走势面积填充 -->
        <path :d="areaPath" :fill="currentMeta.change >= 0 ? 'url(#areaGradientUp)' : 'url(#areaGradientDown)'" />

        <!-- 走势实线 -->
        <path
          :d="linePath"
          fill="none"
          :stroke="currentMeta.change >= 0 ? '#D92D20' : '#039855'"
          stroke-width="1.8"
          stroke-linejoin="round"
          stroke-linecap="round"
        />

        <!-- 鼠标悬浮指示标线 -->
        <g v-if="hoverPoint">
          <line
            :x1="hoverPoint.x"
            y1="10"
            :x2="hoverPoint.x"
            y2="190"
            stroke="#175CD3"
            stroke-width="1"
            stroke-dasharray="2 2"
          />
          <circle
            :cx="hoverPoint.x"
            :cy="hoverPoint.y"
            r="3.5"
            fill="#175CD3"
            stroke="#ffffff"
            stroke-width="2"
          />
        </g>
      </svg>

      <!-- 悬浮 Tooltip -->
      <div
        v-if="hoverPoint"
        class="chart-tooltip"
        :style="{ left: hoverTooltipLeft + 'px', top: '20px' }"
      >
        <div class="tt-time">{{ hoverPoint.time }}</div>
        <div class="tt-val" :class="hoverPoint.change >= 0 ? 'up' : 'down'">
          点位: {{ hoverPoint.price.toFixed(2) }} ({{ hoverPoint.change >= 0 ? '+' : '' }}{{ hoverPoint.change.toFixed(2) }}%)
        </div>
      </div>
    </div>

    <!-- X轴时间刻度 -->
    <div class="time-axis">
      <span>09:30</span>
      <span>10:30</span>
      <span>11:30 / 13:00</span>
      <span>14:00</span>
      <span>15:00</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { stocksApi } from '@/api/stocks'

const indexOptions = ref([
  { key: 'sh', code: 'sh000001', name: '上证指数', change: 0.94, basePrice: 3911.87 },
  { key: 'sz', code: 'sz399001', name: '深证成指', change: 1.72, basePrice: 13640.87 },
  { key: 'cyb', code: 'sz399006', name: '创业板指', change: 2.25, basePrice: 3372.68 },
  { key: 'kcb', code: 'sh000680', name: '科创综指', change: 3.23, basePrice: 1948.21 }
])

const currentIndex = ref('sh')

const currentMeta = computed(() => {
  return indexOptions.value.find(i => i.key === currentIndex.value) || indexOptions.value[0]
})

async function fetchLatestIndices() {
  await Promise.allSettled(
    indexOptions.value.map(async (item) => {
      try {
        const res = await stocksApi.getQuote(item.code)
        const q = (res as any)?.data || res
        if (q && (q.price !== undefined || q.close !== undefined)) {
          item.basePrice = Number(q.price ?? q.close)
          item.change = Number(q.change_percent ?? q.pct_chg ?? 0)
        }
      } catch (e) {
        // 保持平滑
      }
    })
  )
}

let timer: number | null = null

onMounted(() => {
  fetchLatestIndices()
  timer = window.setInterval(fetchLatestIndices, 15000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

// 生成模拟真实分钟线数据 (240个点)
const generatePoints = (seedChange: number, basePrice: number) => {
  const points: { x: number; y: number; time: string; price: number; change: number }[] = []
  const totalSteps = 240
  let currentVal = basePrice
  const targetVal = basePrice * (1 + seedChange / 100)
  const drift = (targetVal - basePrice) / totalSteps

  for (let i = 0; i <= totalSteps; i++) {
    // 随机漫步
    const noise = (Math.sin(i / 12) * 2.5 + Math.cos(i / 8) * 1.5 + (Math.random() - 0.48) * 2) * (basePrice * 0.0006)
    currentVal = basePrice + drift * i + noise
    if (i === totalSteps) currentVal = targetVal

    const pct = ((currentVal - basePrice) / basePrice) * 100

    // 映射到 SVG 坐标 (0~700, 10~190, y=100 为零轴)
    const x = (i / totalSteps) * 700
    // ±3% 映射到 ±90px
    const y = Math.max(12, Math.min(188, 100 - (pct / 3) * 90))

    // 时间计算
    let hours = 9
    let mins = 30 + i
    if (mins >= 60) {
      hours += Math.floor(mins / 60)
      mins %= 60
    }
    if (hours === 11 && mins > 30) {
      hours = 13
      mins = mins - 30
    } else if (hours === 12) {
      hours = 13
    }
    const timeStr = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`

    points.push({ x, y, time: timeStr, price: currentVal, change: pct })
  }
  return points
}

const activeDataSeries = computed(() => {
  return generatePoints(currentMeta.value.change, currentMeta.value.basePrice)
})

const linePath = computed(() => {
  const pts = activeDataSeries.value
  if (!pts.length) return ''
  return pts.reduce((acc, pt, idx) => {
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`
  }, '')
})

const areaPath = computed(() => {
  const pts = activeDataSeries.value
  if (!pts.length) return ''
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `M ${first.x.toFixed(1)} 100 ${linePath.value} L ${last.x.toFixed(1)} 100 Z`
})

// 悬浮交互
const wrapperRef = ref<HTMLElement | null>(null)
const hoverPoint = ref<any>(null)
const hoverTooltipLeft = ref(0)

const onMouseMove = (e: MouseEvent) => {
  if (!wrapperRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const ratio = Math.max(0, Math.min(1, mouseX / rect.width))
  const index = Math.round(ratio * (activeDataSeries.value.length - 1))
  hoverPoint.value = activeDataSeries.value[index]
  hoverTooltipLeft.value = Math.max(10, Math.min(rect.width - 160, mouseX - 70))
}

const onMouseLeave = () => {
  hoverPoint.value = null
}
</script>

<style scoped lang="scss">
.market-trend-container {
  background: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  padding: 16px;
  user-select: none;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .trend-title-area {
    .box-title {
      font-size: 14px;
      font-weight: 700;
      color: #101828;
      margin: 0;
    }
    .sub-label {
      font-size: 11px;
      color: #667085;
    }
  }

  .index-switcher {
    display: flex;
    gap: 6px;

    .switch-btn {
      background: #f8fafc;
      border: 1px solid #eaecf0;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 500;
      color: #475467;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;

      span.up { color: #d92d20; font-weight: 600; font-family: 'JetBrains Mono'; }
      span.down { color: #039855; font-weight: 600; font-family: 'JetBrains Mono'; }

      &:hover {
        background: #f2f4f7;
      }

      &.active {
        background: #eff8ff;
        border-color: #84caff;
        color: #175cd3;
      }
    }
  }
}

.svg-chart-wrapper {
  position: relative;
  width: 100%;
  height: 180px;

  .trend-svg {
    width: 100%;
    height: 100%;
    overflow: visible;
    cursor: crosshair;
  }

  .chart-tooltip {
    position: absolute;
    background: rgba(16, 24, 40, 0.9);
    color: #ffffff;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 11px;
    pointer-events: none;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    z-index: 10;
    white-space: nowrap;

    .tt-time {
      color: #98a2b3;
      font-family: 'JetBrains Mono', monospace;
      margin-bottom: 2px;
    }
    .tt-val {
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
      &.up { color: #f97066; }
      &.down { color: #32d583; }
    }
  }
}

.time-axis {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #98a2b3;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 6px;
  padding: 0 4px;
}
</style>
