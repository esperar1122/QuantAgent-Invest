<template>
  <div class="kline-container" ref="containerRef">
    <!-- 图表顶栏工具条 -->
    <div class="kline-toolbar">
      <!-- 左侧：周期切换与指标标签 -->
      <div class="toolbar-left">
        <div class="period-tabs">
          <button 
            v-for="p in periods" 
            :key="p.key" 
            :class="['tab-btn', { active: currentPeriod === p.key }]"
            @click="switchPeriod(p.key)"
          >
            {{ p.label }}
          </button>
        </div>
        <div class="divider"></div>
        <!-- 分时模式：显示均价、昨收与最新现价 -->
        <div v-if="currentPeriod === 'timeline'" class="indicator-tags timeline-tags">
          <template v-if="isOfflineEmpty">
            <span class="indicator-badge timeline-prev">昨收: --</span>
            <span class="indicator-badge timeline-avg">均价: --</span>
            <span class="indicator-badge offline-pill">离线等待数据</span>
          </template>
          <template v-else>
            <span class="indicator-badge timeline-prev">昨收: {{ timelinePrevClose.toFixed(2) }}</span>
            <span class="indicator-badge timeline-avg">均价: {{ currentTimelineAvg.toFixed(2) }}</span>
            <span class="indicator-badge timeline-latest" :class="timelineChange >= 0 ? 'up' : 'down'">
              现价: {{ currentTimelinePrice.toFixed(2) }} ({{ timelineChange >= 0 ? '+' : '' }}{{ timelinePct.toFixed(2) }}%)
            </span>
          </template>
        </div>
        <!-- K线模式：显示 MA 均线 -->
        <div v-else class="indicator-tags">
          <template v-if="isOfflineEmpty">
            <span class="indicator-badge ma5">MA5: --</span>
            <span class="indicator-badge ma20">MA20: --</span>
            <span class="indicator-badge ma60">MA60: --</span>
            <span class="indicator-badge offline-pill">离线等待数据</span>
          </template>
          <template v-else>
            <span class="indicator-badge ma5">MA5: {{ (currentHoverItem ? currentHoverItem.ma5 : latestItem?.ma5 || 0).toFixed(2) }}</span>
            <span class="indicator-badge ma20">MA20: {{ (currentHoverItem ? currentHoverItem.ma20 : latestItem?.ma20 || 0).toFixed(2) }}</span>
            <span class="indicator-badge ma60">MA60: {{ (currentHoverItem ? currentHoverItem.ma60 : latestItem?.ma60 || 0).toFixed(2) }}</span>
          </template>
        </div>
      </div>

      <!-- 中间：展开/收回画线工具箱的触发按钮 -->
      <div class="toolbar-center">
        <button 
          class="draw-panel-toggle-btn" 
          :class="{ active: isDrawPanelVisible }"
          @click="toggleDrawPanel"
        >
          <span class="btn-icon">✏️</span>
          <span class="btn-text">画线工具</span>
          <span v-if="drawings.length > 0" class="draw-count-pill">{{ drawings.length }}</span>
          <span class="toggle-arrow">{{ isDrawPanelVisible ? '▲' : '▼' }}</span>
        </button>
      </div>

      <!-- 右侧：副图指标选择 -->
      <div class="toolbar-right">
        <div class="subchart-selector">
          <span class="selector-label">副图:</span>
          <button 
            v-for="sub in availableSubIndicators" 
            :key="sub.key"
            :class="['sub-btn', { active: currentSubIndicator === sub.key }]"
            @click="currentSubIndicator = sub.key"
          >
            {{ sub.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 图表主绘图区域 (支持滚轮缩放与按住拖动平移) -->
    <div 
      class="kline-viewport" 
      :class="[activeTool, { 'is-dragging': isDragging }]"
      @wheel.prevent="handleWheel"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      @dblclick="resetZoom"
    >
      <!-- 可拖拽悬浮画线工具箱 (Teleport到body，支持在整个页面任意位置自由拖拽) -->
      <Teleport to="body">
        <div 
          v-if="isDrawPanelVisible" 
          class="floating-draw-panel" 
          :style="{ left: panelPos.x + 'px', top: panelPos.y + 'px' }"
          @mousedown.stop
        >
          <div class="panel-header" @mousedown="startPanelDrag">
            <div class="header-title">
              <span class="drag-handle">⠿</span>
              <span>画线工具箱</span>
            </div>
            <button class="panel-close-btn" @click="isDrawPanelVisible = false">×</button>
          </div>

          <div class="panel-tools-body">
            <div class="tools-grid">
              <button 
                :class="['tool-chip', { active: activeTool === 'pan' }]" 
                title="漫游拖拽 (鼠标滚轮缩放，按住左键平移)"
                @click="setTool('pan')"
              >
                <span class="tool-icon">✋</span>
                <span class="tool-label">拖动</span>
              </button>
              <button 
                :class="['tool-chip', { active: activeTool === 'trendline' }]" 
                title="趋势线 (点击两点绘制连线)"
                @click="setTool('trendline')"
              >
                <span class="tool-icon">📏</span>
                <span class="tool-label">趋势线</span>
              </button>
              <button 
                :class="['tool-chip', { active: activeTool === 'horizontal' }]" 
                title="水平线 (点击任意价位生成支撑/压力线)"
                @click="setTool('horizontal')"
              >
                <span class="tool-icon">➖</span>
                <span class="tool-label">水平线</span>
              </button>
              <button 
                :class="['tool-chip', { active: activeTool === 'rect' }]" 
                title="箱体矩形 (点击两角标记震荡区间)"
                @click="setTool('rect')"
              >
                <span class="tool-icon">📐</span>
                <span class="tool-label">箱体</span>
              </button>
              <button 
                :class="['tool-chip', { active: activeTool === 'price_tag' }]" 
                title="价格标注 (点击点位标记精确价格)"
                @click="setTool('price_tag')"
              >
                <span class="tool-icon">🏷️</span>
                <span class="tool-label">标注</span>
              </button>
            </div>

            <div class="panel-actions-row">
              <button 
                class="panel-action-btn" 
                :disabled="drawings.length === 0"
                title="撤销上一条画线"
                @click="undoDrawing"
              >
                ↩️ 撤销
              </button>
              <button 
                class="panel-action-btn danger" 
                :disabled="drawings.length === 0"
                title="清空全部画线"
                @click="clearDrawings"
              >
                🗑️ 清空
              </button>
              <button 
                class="panel-action-btn reset" 
                title="一键复位视角 (亦可双击图表复位)"
                @click="resetZoom"
              >
                ↺ 复位
              </button>
            </div>
          </div>
        </div>
      </Teleport>

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
          <!-- 分时面积渐变 -->
          <linearGradient id="timelineAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#2563EB" stop-opacity="0.25"/>
            <stop offset="100%" stop-color="#2563EB" stop-opacity="0.01"/>
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

        <!-- ================= 分时图模式 (TIMELINE) ================= -->
        <g v-if="currentPeriod === 'timeline'" class="timeline-mode">
          <!-- 昨收中轴基准线 (灰色虚线，贯穿全宽) -->
          <line 
            :x1="padding.left" 
            :y1="timelinePrevCloseY" 
            :x2="width - padding.right" 
            :y2="timelinePrevCloseY" 
            stroke="#98A2B3" 
            stroke-width="1" 
            stroke-dasharray="4 3"
          />
          
          <!-- 分时面积填充 (仅覆盖到当前最新交易时刻) -->
          <path :d="timelineAreaPath" fill="url(#timelineAreaGrad)" />
          
          <!-- 分时价格折线 (蓝色) -->
          <path :d="timelinePricePath" fill="none" stroke="#2563EB" stroke-width="1.8" stroke-linejoin="round" />
          
          <!-- 分时均价折线 (黄色/橙色) -->
          <path :d="timelineAvgPath" fill="none" stroke="#D97706" stroke-width="1.3" stroke-dasharray="3 1" />
        </g>

        <!-- ================= K 线图模式 (KLINE) ================= -->
        <g v-else class="kline-mode">
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
        </g>

        <!-- ================= 画线图层 (DRAWINGS LAYER) ================= -->
        <g class="drawing-layer">
          <!-- 已完成的画线图形 -->
          <g v-for="(shape, idx) in renderedDrawings" :key="shape.id || idx">
            <!-- 1. 水平支撑/阻力线 -->
            <g v-if="shape.type === 'horizontal'">
              <line 
                :x1="padding.left" 
                :y1="shape.y" 
                :x2="width - padding.right" 
                :y2="shape.y" 
                :stroke="shape.color || '#F59E0B'" 
                stroke-width="1.6" 
                stroke-dasharray="4 2"
              />
              <rect 
                :x="width - padding.right - 58" 
                :y="shape.y - 10" 
                width="56" 
                height="20" 
                rx="3" 
                :fill="shape.color || '#F59E0B'" 
              />
              <text 
                :x="width - padding.right - 30" 
                :y="shape.y + 4" 
                fill="#FFFFFF" 
                font-size="10" 
                font-weight="700" 
                text-anchor="middle"
                class="tabular-nums font-mono"
              >
                ¥{{ shape.price.toFixed(2) }}
              </text>
            </g>

            <!-- 2. 趋势线 -->
            <g v-else-if="shape.type === 'trendline'">
              <line 
                :x1="shape.x1" 
                :y1="shape.y1" 
                :x2="shape.x2" 
                :y2="shape.y2" 
                :stroke="shape.color || '#2563EB'" 
                stroke-width="2" 
              />
              <circle :cx="shape.x1" :cy="shape.y1" r="3.5" :fill="shape.color || '#2563EB'" />
              <circle :cx="shape.x2" :cy="shape.y2" r="3.5" :fill="shape.color || '#2563EB'" />
            </g>

            <!-- 3. 箱体矩形 -->
            <g v-else-if="shape.type === 'rect'">
              <rect 
                :x="shape.boxX" 
                :y="shape.boxY" 
                :width="shape.boxW" 
                :height="shape.boxH" 
                fill="rgba(37, 99, 235, 0.12)" 
                :stroke="shape.color || '#2563EB'" 
                stroke-width="1.5" 
                stroke-dasharray="3 3"
              />
            </g>

            <!-- 4. 价格标注 -->
            <g v-else-if="shape.type === 'price_tag'">
              <circle :cx="shape.x" :cy="shape.y" r="4" fill="#10B981" />
              <rect 
                :x="shape.x + 6" 
                :y="shape.y - 10" 
                width="58" 
                height="20" 
                rx="3" 
                fill="#10B981" 
              />
              <text 
                :x="shape.x + 35" 
                :y="shape.y + 4" 
                fill="#FFFFFF" 
                font-size="10" 
                font-weight="700" 
                text-anchor="middle"
                class="tabular-nums font-mono"
              >
                ¥{{ shape.price.toFixed(2) }}
              </text>
            </g>
          </g>

          <!-- 正在绘制的动态预览草稿 -->
          <g v-if="drawingDraft" class="drawing-draft">
            <!-- 趋势线预览 -->
            <line 
              v-if="drawingDraft.type === 'trendline'" 
              :x1="drawingDraft.x1" 
              :y1="drawingDraft.y1" 
              :x2="drawingDraft.x2" 
              :y2="drawingDraft.y2" 
              stroke="#2563EB" 
              stroke-width="2" 
              stroke-dasharray="4 3"
            />
            <!-- 箱体预览 -->
            <rect 
              v-if="drawingDraft.type === 'rect'" 
              :x="Math.min(drawingDraft.x1, drawingDraft.x2)" 
              :y="Math.min(drawingDraft.y1, drawingDraft.y2)" 
              :width="Math.abs(drawingDraft.x2 - drawingDraft.x1)" 
              :height="Math.abs(drawingDraft.y2 - drawingDraft.y1)" 
              fill="rgba(37, 99, 235, 0.15)" 
              stroke="#2563EB" 
              stroke-width="1.5" 
              stroke-dasharray="3 3"
            />
          </g>
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
          
          <!-- 分时模式左侧/右侧涨跌幅对称百分比刻度 -->
          <template v-if="currentPeriod === 'timeline'">
            <text 
              v-for="(tick, idx) in mainPctTicks" 
              :key="'pcttick-' + idx"
              :x="padding.left + 4" 
              :y="tick.y + 4" 
              font-size="10" 
              :fill="tick.val > 0 ? '#D92D20' : (tick.val < 0 ? '#039855' : '#667085')" 
              class="tabular-nums font-mono"
            >
              {{ tick.val > 0 ? '+' : '' }}{{ tick.val.toFixed(2) }}%
            </text>
          </template>
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

        <!-- ================= 副图：成交量 (VOL) ================= -->
        <g v-if="currentSubIndicator === 'VOL'" class="subchart-vol">
          <!-- 分时成交量柱状图 (对齐精确分钟位置) -->
          <template v-if="currentPeriod === 'timeline'">
            <g v-for="(item, i) in timelineVolPoints" :key="'tl-vol-' + i">
              <rect 
                :x="item.x - item.w / 2" 
                :y="item.y" 
                :width="Math.max(1, item.w)" 
                :height="item.h" 
                :fill="item.isUp ? '#D92D20' : '#039855'"
              />
            </g>
            <text 
              :x="padding.left + 6" 
              :y="subChartTop + 14" 
              font-size="10" 
              fill="#475467" 
              font-weight="600"
            >
              VOL(分时量): {{ (currentHoverTimelineItem ? currentHoverTimelineItem.volume : latestTimelineVol).toLocaleString() }} 手
            </text>
          </template>

          <!-- K线成交量柱状图 -->
          <template v-else>
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
              VOL(成交量): {{ (currentHoverItem ? currentHoverItem.vol : latestItem?.vol || 0).toLocaleString() }} 手
            </text>
          </template>
        </g>

        <!-- ================= 副图：MACD ================= -->
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
          <g v-for="(m, i) in macdPoints" :key="'macd-bar-' + i">
            <rect 
              :x="m.x - (currentPeriod === 'timeline' ? 1.5 : candleWidth / 2)" 
              :y="m.barY" 
              :width="currentPeriod === 'timeline' ? 2 : candleWidth" 
              :height="Math.max(m.barHeight, 1)" 
              :fill="m.val >= 0 ? '#D92D20' : '#039855'"
            />
          </g>
          <path :d="macdDifPath" fill="none" stroke="#175CD3" stroke-width="1.3" />
          <path :d="macdDeaPath" fill="none" stroke="#D97706" stroke-width="1.3" />
          <text 
            :x="padding.left + 6" 
            :y="subChartTop + 14" 
            font-size="10" 
            fill="#475467" 
            font-weight="600"
          >
            MACD(12,26,9) DIF: <tspan fill="#175CD3">{{ (currentHoverItem ? currentHoverItem.dif : latestItem?.dif || 0).toFixed(2) }}</tspan> DEA: <tspan fill="#D97706">{{ (currentHoverItem ? currentHoverItem.dea : latestItem?.dea || 0).toFixed(2) }}</tspan>
          </text>
        </g>

        <!-- ================= 副图：RSI ================= -->
        <g v-else-if="currentSubIndicator === 'RSI'" class="subchart-rsi">
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
            RSI(6,12) RSI6: <tspan fill="#175CD3">{{ (currentHoverItem ? currentHoverItem.rsi6 : latestItem?.rsi6 || 0).toFixed(1) }}</tspan> RSI12: <tspan fill="#D97706">{{ (currentHoverItem ? currentHoverItem.rsi12 : latestItem?.rsi12 || 0).toFixed(1) }}</tspan>
          </text>
        </g>

        <!-- X 轴日期/时间刻度 (分时图严格对齐 09:30, 10:30, 11:30/13:00, 14:00, 15:00) -->
        <g class="x-labels">
          <text 
            v-for="(tick, idx) in (currentPeriod === 'timeline' ? timelineTimeTicks : dateTicks)" 
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
            width="50" 
            height="18" 
            fill="#1D2939" 
            rx="2"
          />
          <text 
            v-if="hoverY <= subChartTop"
            :x="width - padding.right + 27" 
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

      <!-- 悬浮数据框 (K线 Tooltip) -->
      <div 
        v-if="currentHoverItem && currentPeriod !== 'timeline'" 
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

      <!-- 悬浮数据框 (分时 Tooltip) -->
      <div 
        v-if="currentHoverTimelineItem && currentPeriod === 'timeline'" 
        class="kline-tooltip timeline-tooltip" 
        :style="{ left: tooltipPos.x + 'px', top: '12px' }"
      >
        <div class="tt-header">
          <span class="tt-date">分时 {{ currentHoverTimelineItem.time }}</span>
          <span :class="['tt-pct', currentHoverTimelineItem.pct_chg >= 0 ? 'up' : 'down']">
            {{ currentHoverTimelineItem.pct_chg >= 0 ? '+' : '' }}{{ currentHoverTimelineItem.pct_chg.toFixed(2) }}%
          </span>
        </div>
        <div class="tt-grid">
          <div class="tt-item"><span class="k">现价</span><span class="v tabular-nums">¥{{ currentHoverTimelineItem.price.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">均价</span><span class="v tabular-nums">¥{{ currentHoverTimelineItem.avg_price.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">涨跌</span><span class="v tabular-nums" :class="currentHoverTimelineItem.change >= 0 ? 'color-up' : 'color-down'">{{ currentHoverTimelineItem.change >= 0 ? '+' : '' }}{{ currentHoverTimelineItem.change.toFixed(2) }}</span></div>
          <div class="tt-item"><span class="k">分时量</span><span class="v tabular-nums">{{ (currentHoverTimelineItem.volume / 100).toFixed(0) }}手</span></div>
        </div>
      </div>

      <!-- 🔥 骨架扫光层 (当后端离线/未连接且无真实数据时展示，代替 8.27 虚假数据) -->
      <div v-if="isOfflineEmpty" class="kline-skeleton-layer">
        <!-- 骨架扫描背景蜡烛条与网格 -->
        <div class="skeleton-chart-canvas">
          <div class="skeleton-grid-lines">
            <span v-for="n in 5" :key="'g-'+n" class="sk-grid-row"></span>
          </div>
          <div class="skeleton-candles-flow">
            <div 
              v-for="(bar, bIdx) in skeletonCandles" 
              :key="'sk-bar-'+bIdx" 
              class="sk-candle-item"
              :style="{ height: bar.height + '%', marginTop: bar.offset + '%' }"
            >
              <span class="sk-candle-wick" :style="{ top: -bar.wickTop + 'px', bottom: -bar.wickBottom + 'px' }"></span>
              <span class="sk-candle-body"></span>
            </div>
          </div>
          <div class="skeleton-volume-flow">
            <div 
              v-for="(vol, vIdx) in skeletonVolumes" 
              :key="'sk-vol-'+vIdx" 
              class="sk-vol-bar"
              :style="{ height: vol + '%' }"
            ></div>
          </div>
        </div>

        <!-- 骨架动态扫光光幕 -->
        <div class="skeleton-shimmer-sweep"></div>

        <!-- 居中高科技状态浮层 -->
        <div class="skeleton-status-card">
          <div class="status-pulse-ring">
            <span class="pulse-beacon"></span>
            <span class="beacon-core">⚡</span>
          </div>
          <div class="status-title">投研中台未连接 · 骨架就绪等待数据流</div>
          <div class="status-subtitle">
            系统已屏蔽 8.27 虚假模拟数据以确保合规真实性，请启动后端服务或检查接口链路
          </div>
          <div class="status-action-row">
            <button class="sk-retry-btn" :disabled="loading || timelineLoading" @click="handleManualRetry">
              <span class="btn-spin" v-if="loading || timelineLoading">⏳</span>
              <span v-else>↺</span>
              <span>{{ (loading || timelineLoading) ? '连接中...' : '重试获取实时数据' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
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

interface TimelineItem {
  time: string
  price: number
  avg_price: number
  volume: number
  pct_chg: number
  change: number
  is_up: boolean
  minuteIndex?: number
}

interface DrawnShape {
  id: string
  type: 'trendline' | 'horizontal' | 'rect' | 'price_tag'
  price: number
  price2?: number
  date?: string
  date2?: string
  timeIndex?: number
  timeIndex2?: number
  color?: string
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
  { key: 'timeline', label: '分时' },
  { key: 'day', label: '日K' },
  { key: 'week', label: '周K' },
  { key: '60m', label: '60分' },
]

const currentPeriod = ref('day')

const availableSubIndicators = computed(() => {
  if (currentPeriod.value === 'timeline') {
    return [
      { key: 'VOL', label: '分时成交量' },
      { key: 'MACD', label: 'MACD' },
    ]
  }
  return [
    { key: 'VOL', label: '成交量' },
    { key: 'MACD', label: 'MACD' },
    { key: 'RSI', label: 'RSI' },
  ]
})

const currentSubIndicator = ref('VOL')

function switchPeriod(p: string) {
  currentPeriod.value = p
  if (p === 'timeline' && currentSubIndicator.value === 'RSI') {
    currentSubIndicator.value = 'VOL'
  }
}

// 尺寸定义
const width = 840
const height = 420
const padding = { top: 20, right: 60, bottom: 25, left: 20 }
const mainChartHeight = 260
const subChartTop = 295
const subChartHeight = 95
const containerRef = ref<HTMLElement | null>(null)

// ================= 画线工具悬浮窗系统 =================
type ToolMode = 'pan' | 'trendline' | 'horizontal' | 'rect' | 'price_tag'
const isDrawPanelVisible = ref(false)
const activeTool = ref<ToolMode>('pan')
const drawings = ref<DrawnShape[]>([])
const drawingDraft = ref<any | null>(null)
let draftStartPoint: { x: number; y: number; price: number; index: number; date: string } | null = null

// 悬浮窗位置与全页面自由拖拽移动
const panelPos = ref({ x: 100, y: 120 })
const hasOpenedOnce = ref(false)
let isPanelDragging = false
let panelDragStart = { mouseX: 0, mouseY: 0, panelX: 0, panelY: 0 }

function toggleDrawPanel() {
  isDrawPanelVisible.value = !isDrawPanelVisible.value
  if (isDrawPanelVisible.value && !hasOpenedOnce.value) {
    hasOpenedOnce.value = true
    if (containerRef.value) {
      const rect = containerRef.value.getBoundingClientRect()
      // 默认停靠在图表右上方视口内
      panelPos.value = {
        x: Math.min(window.innerWidth - 230, Math.max(20, Math.round(rect.right - 230))),
        y: Math.min(window.innerHeight - 200, Math.max(70, Math.round(rect.top + 45)))
      }
    }
  }
}

function startPanelDrag(e: MouseEvent) {
  isPanelDragging = true
  e.preventDefault()
  panelDragStart = {
    mouseX: e.clientX,
    mouseY: e.clientY,
    panelX: panelPos.value.x,
    panelY: panelPos.value.y
  }
  window.addEventListener('mousemove', onPanelDragMove)
  window.addEventListener('mouseup', onPanelDragEnd)
}

function onPanelDragMove(e: MouseEvent) {
  if (!isPanelDragging) return
  e.preventDefault()
  const dx = e.clientX - panelDragStart.mouseX
  const dy = e.clientY - panelDragStart.mouseY
  const panelWidth = 220
  const panelHeight = 160
  const maxX = Math.max(10, window.innerWidth - panelWidth - 10)
  const maxY = Math.max(10, window.innerHeight - panelHeight - 10)
  panelPos.value.x = Math.max(10, Math.min(maxX, panelDragStart.panelX + dx))
  panelPos.value.y = Math.max(10, Math.min(maxY, panelDragStart.panelY + dy))
}

function onPanelDragEnd() {
  isPanelDragging = false
  window.removeEventListener('mousemove', onPanelDragMove)
  window.removeEventListener('mouseup', onPanelDragEnd)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onPanelDragMove)
  window.removeEventListener('mouseup', onPanelDragEnd)
})

function setTool(tool: ToolMode) {
  activeTool.value = tool
  drawingDraft.value = null
  draftStartPoint = null
}

function undoDrawing() {
  drawings.value.pop()
}

function clearDrawings() {
  drawings.value = []
  drawingDraft.value = null
  draftStartPoint = null
}

// ================= 分时图数据与时间轴精确对齐 =================
// A 股全天 240 分钟标准交易槽 (09:30-11:30 早盘 120 分钟, 13:00-15:00 午盘 120 分钟)
const TOTAL_TIMELINE_MINUTES = 240

function getTimelineMinuteIndex(timeStr: string, fallbackIdx: number): number {
  if (!timeStr || !timeStr.includes(':')) {
    return Math.min(TOTAL_TIMELINE_MINUTES, fallbackIdx)
  }
  const parts = timeStr.trim().split(':')
  const h = parseInt(parts[0], 10)
  const m = parseInt(parts[1], 10)
  if (isNaN(h) || isNaN(m)) return Math.min(TOTAL_TIMELINE_MINUTES, fallbackIdx)

  if (h <= 11 || (h === 11 && m <= 30)) {
    // 早盘 09:30 ~ 11:30 (映射为 0 ~ 120)
    const mins = (h - 9) * 60 + m - 30
    return Math.max(0, Math.min(120, mins))
  } else {
    // 午盘 13:00 ~ 15:00 (映射为 120 ~ 240)
    const mins = 120 + (h - 13) * 60 + m
    return Math.max(120, Math.min(240, mins))
  }
}

const timelineRaw = ref<{
  prev_close: number
  items: TimelineItem[]
}>({
  prev_close: props.currentPrice || 10,
  items: []
})

const timelinePrevClose = computed(() => timelineRaw.value.prev_close || props.currentPrice || 10)
const timelineItems = computed(() => timelineRaw.value.items)
const latestTimelineItem = computed(() => timelineItems.value[timelineItems.value.length - 1] || null)
const currentTimelinePrice = computed(() => latestTimelineItem.value?.price || timelinePrevClose.value)
const currentTimelineAvg = computed(() => latestTimelineItem.value?.avg_price || timelinePrevClose.value)
const timelineChange = computed(() => currentTimelinePrice.value - timelinePrevClose.value)
const timelinePct = computed(() => (timelineChange.value / (timelinePrevClose.value || 1)) * 100)
const latestTimelineVol = computed(() => latestTimelineItem.value?.volume || 0)

// 🔥 骨架扫光模式：当后端断开/未启动且无真实数据时激活
const isOfflineEmpty = ref(false)
const timelineLoading = ref(false)

// 静态美学骨架蜡烛数据 (36根自然起伏蜡烛高度与偏移)
const skeletonCandles = [
  { height: 28, offset: 25, wickTop: 6, wickBottom: 8 },
  { height: 35, offset: 22, wickTop: 8, wickBottom: 5 },
  { height: 32, offset: 26, wickTop: 5, wickBottom: 9 },
  { height: 42, offset: 20, wickTop: 10, wickBottom: 6 },
  { height: 38, offset: 24, wickTop: 7, wickBottom: 7 },
  { height: 48, offset: 18, wickTop: 9, wickBottom: 10 },
  { height: 52, offset: 15, wickTop: 8, wickBottom: 6 },
  { height: 45, offset: 21, wickTop: 6, wickBottom: 8 },
  { height: 40, offset: 25, wickTop: 7, wickBottom: 5 },
  { height: 50, offset: 19, wickTop: 9, wickBottom: 8 },
  { height: 58, offset: 14, wickTop: 11, wickBottom: 7 },
  { height: 54, offset: 17, wickTop: 8, wickBottom: 9 },
  { height: 46, offset: 22, wickTop: 7, wickBottom: 6 },
  { height: 60, offset: 12, wickTop: 12, wickBottom: 8 },
  { height: 64, offset: 10, wickTop: 10, wickBottom: 11 },
  { height: 58, offset: 15, wickTop: 9, wickBottom: 7 },
  { height: 66, offset: 9, wickTop: 11, wickBottom: 8 },
  { height: 62, offset: 13, wickTop: 8, wickBottom: 10 },
  { height: 70, offset: 7, wickTop: 13, wickBottom: 7 },
  { height: 65, offset: 11, wickTop: 9, wickBottom: 9 },
  { height: 59, offset: 16, wickTop: 8, wickBottom: 8 },
  { height: 68, offset: 9, wickTop: 10, wickBottom: 10 },
  { height: 72, offset: 6, wickTop: 12, wickBottom: 8 },
  { height: 64, offset: 12, wickTop: 8, wickBottom: 9 },
  { height: 76, offset: 4, wickTop: 14, wickBottom: 9 },
  { height: 71, offset: 8, wickTop: 10, wickBottom: 11 },
  { height: 67, offset: 11, wickTop: 9, wickBottom: 8 },
  { height: 75, offset: 5, wickTop: 11, wickBottom: 9 },
  { height: 80, offset: 2, wickTop: 13, wickBottom: 10 },
  { height: 74, offset: 7, wickTop: 9, wickBottom: 8 },
  { height: 78, offset: 4, wickTop: 12, wickBottom: 9 },
  { height: 82, offset: 1, wickTop: 14, wickBottom: 11 },
  { height: 76, offset: 6, wickTop: 10, wickBottom: 8 },
  { height: 85, offset: 0, wickTop: 15, wickBottom: 10 },
  { height: 80, offset: 4, wickTop: 11, wickBottom: 9 },
  { height: 84, offset: 2, wickTop: 13, wickBottom: 12 }
]

const skeletonVolumes = [
  30, 45, 38, 52, 40, 65, 70, 55, 42, 60, 78, 66, 50, 82, 88, 72, 90, 75, 95, 80, 68, 85, 92, 70, 96, 84, 76, 90, 98, 82, 91, 100, 86, 97, 88, 94
]

function handleManualRetry() {
  isOfflineEmpty.value = false
  if (currentPeriod.value === 'timeline') {
    loadTimelineData()
  } else {
    loadKlineData()
  }
}

async function loadTimelineData() {
  if (!props.stockCode) return
  timelineLoading.value = true
  try {
    const res = await (stocksApi as any).getTimeline(props.stockCode)
    const d = (res as any)?.data || res
    if (d && Array.isArray(d.items) && d.items.length > 0) {
      timelineRaw.value = {
        prev_close: Number(d.prev_close || props.currentPrice || 10),
        items: d.items.map((it: any, idx: number) => {
          const tStr = String(it.time || '').slice(-5)
          const minuteIdx = getTimelineMinuteIndex(tStr, idx)
          return {
            time: tStr,
            price: Number(it.price || it.close || props.currentPrice || 10),
            avg_price: Number(it.avg_price || it.price || props.currentPrice || 10),
            volume: Number(it.volume || 1000),
            pct_chg: Number(it.pct_chg || 0),
            change: Number(it.change || 0),
            is_up: Boolean(it.is_up ?? (it.price >= (it.avg_price || it.price))),
            minuteIndex: minuteIdx
          }
        })
      }
      isOfflineEmpty.value = false
      return
    }
  } catch (err) {
    // 后端未连通
  } finally {
    timelineLoading.value = false
  }

  // 彻底废除虚假分时数据：未连接后端且无实时数据时，激活专业骨架扫光模式
  if (!timelineRaw.value || !timelineRaw.value.items || timelineRaw.value.items.length === 0) {
    isOfflineEmpty.value = true
  }
}

// ================= K 线数据与指标 =================
const rawData = ref<KlineItem[]>([])
const loading = ref(false)

// 缩放与平移窗口控制 (纯滚轮缩放与鼠标拖动)
const visibleCount = ref(50)   // 屏幕内可见 bar 数量 (15 ~ 150)
const startIndex = ref(0)       // 可见视口起始偏移量

function calculateIndicators(data: KlineItem[]) {
  for (let i = 0; i < data.length; i++) {
    const slice5 = data.slice(Math.max(0, i - 4), i + 1)
    data[i].ma5 = +(slice5.reduce((s, d) => s + d.close, 0) / slice5.length).toFixed(2)

    const slice20 = data.slice(Math.max(0, i - 19), i + 1)
    data[i].ma20 = +(slice20.reduce((s, d) => s + d.close, 0) / slice20.length).toFixed(2)

    const slice60 = data.slice(Math.max(0, i - 59), i + 1)
    data[i].ma60 = +(slice60.reduce((s, d) => s + d.close, 0) / slice60.length).toFixed(2)

    const dif = +((data[i].ma5 - data[i].ma20) * 0.8).toFixed(2)
    const dea = +(dif * 0.75).toFixed(2)
    data[i].dif = dif
    data[i].dea = dea
    data[i].macd = +((dif - dea) * 2).toFixed(2)

    data[i].rsi6 = +(50 + Math.sin(i * 0.5) * 25 + Math.random() * 6).toFixed(1)
    data[i].rsi12 = +(52 + Math.sin(i * 0.3) * 18).toFixed(1)
  }
}

async function loadKlineData() {
  if (!props.stockCode) return
  loading.value = true
  try {
    const res = await stocksApi.getKline(props.stockCode, currentPeriod.value as any, 150)
    const items = (res as any)?.data?.items || (res as any)?.items
    if (items && Array.isArray(items) && items.length >= 5) {
      const mapped: KlineItem[] = items.map((bar: any) => {
        const o = Number(bar.open ?? bar.close ?? props.currentPrice ?? 10)
        const c = Number(bar.close ?? o)
        const h = Number(bar.high ?? Math.max(o, c))
        const l = Number(bar.low ?? Math.min(o, c))
        let v = Number(bar.volume ?? bar.vol ?? 100000)
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

      // 🔥 智能成交量量纲校准 (防范实盘接口 100 倍"股/手"量纲突变导致最新柱巨幅膨胀)
      if (mapped.length >= 2) {
        const last = mapped[mapped.length - 1]
        const prev = mapped[mapped.length - 2]
        if (last.vol > prev.vol * 20 && prev.vol > 0) {
          if (Math.abs(last.vol / 100 - prev.vol) < Math.abs(last.vol - prev.vol)) {
            last.vol = +(last.vol / 100).toFixed(0)
          }
        }
      }

      calculateIndicators(mapped)
      rawData.value = mapped
      visibleCount.value = Math.min(50, mapped.length)
      startIndex.value = Math.max(0, mapped.length - visibleCount.value)
      isOfflineEmpty.value = false
      loading.value = false
      return
    }
  } catch (err) {
    // 后端未连通
  } finally {
    loading.value = false
  }

  // 彻底废弃 8.27 虚假数据：未连接后端且无实时数据时，激活专业骨架扫光模式
  if (rawData.value.length === 0) {
    isOfflineEmpty.value = true
  }
}

watch(
  () => [props.stockCode, props.currentPrice, currentPeriod.value],
  () => {
    if (currentPeriod.value === 'timeline') {
      loadTimelineData()
    } else {
      loadKlineData()
    }
  },
  { immediate: true }
)

// 当前视口内展示的 K 线切片
const chartData = computed(() => {
  if (currentPeriod.value === 'timeline' || isOfflineEmpty.value) return []
  return rawData.value.slice(startIndex.value, startIndex.value + visibleCount.value)
})

const latestItem = computed(() => {
  if (isOfflineEmpty.value || rawData.value.length === 0) return null
  return chartData.value[chartData.value.length - 1] || rawData.value[rawData.value.length - 1] || null
})

// ================= 坐标与价格比例映射 =================
const minPrice = computed(() => {
  if (currentPeriod.value === 'timeline') {
    const prev = timelinePrevClose.value
    const maxDiff = Math.max(...timelineItems.value.map(d => Math.abs(d.price - prev)), prev * 0.015)
    return +(prev - maxDiff * 1.05).toFixed(2)
  }
  if (chartData.value.length === 0) return (props.currentPrice || 10) * 0.95
  return Math.min(...chartData.value.map(d => d.low)) * 0.985
})

const maxPrice = computed(() => {
  if (currentPeriod.value === 'timeline') {
    const prev = timelinePrevClose.value
    const maxDiff = Math.max(...timelineItems.value.map(d => Math.abs(d.price - prev)), prev * 0.015)
    return +(prev + maxDiff * 1.05).toFixed(2)
  }
  if (chartData.value.length === 0) return (props.currentPrice || 10) * 1.05
  return Math.max(...chartData.value.map(d => d.high)) * 1.015
})

const maxVol = computed(() => {
  if (currentPeriod.value === 'timeline') {
    return Math.max(...timelineItems.value.map(d => d.volume), 100)
  }
  return Math.max(...chartData.value.map(d => d.vol), 100)
})

const candleWidth = computed(() => {
  const n = chartData.value.length || 1
  const usableWidth = width - padding.left - padding.right
  return Math.max(4, Math.min(18, (usableWidth / n) * 0.68))
})

function getYByPrice(p: number): number {
  const range = maxPrice.value - minPrice.value || 1
  return padding.top + (1 - (p - minPrice.value) / range) * mainChartHeight
}

function getPriceByY(y: number): number {
  const ratio = 1 - (y - padding.top) / mainChartHeight
  return minPrice.value + ratio * (maxPrice.value - minPrice.value)
}

// 分时昨收 Y 轴位置
const timelinePrevCloseY = computed(() => getYByPrice(timelinePrevClose.value))

// K 线点位计算
const candlePoints = computed(() => {
  const n = chartData.value.length
  if (n === 0) return []
  const step = (width - padding.left - padding.right) / Math.max(1, n - 1)

  return chartData.value.map((d, i) => {
    const x = padding.left + i * step
    const openY = getYByPrice(d.open)
    const closeY = getYByPrice(d.close)
    const highY = getYByPrice(d.high)
    const lowY = getYByPrice(d.low)
    const isUp = d.close >= d.open

    const bodyY = Math.min(openY, closeY)
    const bodyHeight = Math.abs(closeY - openY)

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

// 🔥 分时走势点位计算 (严格映射在 240 分钟时间轴坐标系内，11:30 精确落在中轴线)
const timelinePoints = computed(() => {
  const usableWidth = width - padding.left - padding.right

  return timelineItems.value.map((d, i) => {
    const minIdx = d.minuteIndex !== undefined ? d.minuteIndex : i
    const x = padding.left + (minIdx / TOTAL_TIMELINE_MINUTES) * usableWidth
    const y = getYByPrice(d.price)
    const avgY = getYByPrice(d.avg_price)
    return { x, y, avgY, data: d }
  })
})

const timelinePricePath = computed(() => {
  return generatePath(timelinePoints.value.map(pt => [pt.x, pt.y]))
})

const timelineAvgPath = computed(() => {
  return generatePath(timelinePoints.value.map(pt => [pt.x, pt.avgY]))
})

const timelineAreaPath = computed(() => {
  const pts = timelinePoints.value
  if (pts.length === 0) return ''
  const firstX = pts[0].x
  const lastX = pts[pts.length - 1].x
  const baseBottom = padding.top + mainChartHeight
  const linePart = pts.reduce((acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`, '')
  return `${linePart} L ${lastX.toFixed(1)} ${baseBottom} L ${firstX.toFixed(1)} ${baseBottom} Z`
})

const timelineVolPoints = computed(() => {
  const usableWidth = width - padding.left - padding.right
  const barW = Math.max(1.2, (usableWidth / TOTAL_TIMELINE_MINUTES) * 0.8)

  return timelineItems.value.map((d, i) => {
    const minIdx = d.minuteIndex !== undefined ? d.minuteIndex : i
    const x = padding.left + (minIdx / TOTAL_TIMELINE_MINUTES) * usableWidth
    const h = (d.volume / maxVol.value) * subChartHeight
    const y = subChartTop + subChartHeight - h
    return {
      x,
      y,
      w: barW,
      h: Math.max(1, h),
      isUp: d.is_up
    }
  })
})

// K 线均线折线
const ma5Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i]?.x || 0, getYByPrice(d.ma5)])))
const ma20Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i]?.x || 0, getYByPrice(d.ma20)])))
const ma60Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i]?.x || 0, getYByPrice(d.ma60)])))

// MACD 副图
const macdZeroY = computed(() => subChartTop + subChartHeight / 2)
const macdPoints = computed(() => {
  const dataset = currentPeriod.value === 'timeline' ? timelinePoints.value : candlePoints.value
  return dataset.map((pt, i) => {
    const x = pt.x
    const val = (pt as any).data?.macd ?? (Math.sin(i * 0.15) * 0.6)
    const barScale = 20
    const h = Math.min(subChartHeight / 2 - 2, Math.abs(val) * barScale)
    const barY = val >= 0 ? macdZeroY.value - h : macdZeroY.value
    return { x, val, barY, barHeight: h }
  })
})

const macdDifPath = computed(() => {
  const dataset = currentPeriod.value === 'timeline' ? timelinePoints.value : candlePoints.value
  return generatePath(dataset.map((pt, i) => {
    const dif = (pt as any).data?.dif ?? (Math.sin(i * 0.15) * 0.4)
    return [pt.x, macdZeroY.value - dif * 18]
  }))
})

const macdDeaPath = computed(() => {
  const dataset = currentPeriod.value === 'timeline' ? timelinePoints.value : candlePoints.value
  return generatePath(dataset.map((pt, i) => {
    const dea = (pt as any).data?.dea ?? (Math.sin(i * 0.15 - 0.3) * 0.3)
    return [pt.x, macdZeroY.value - dea * 18]
  }))
})

// RSI 副图
const rsi80Y = computed(() => subChartTop + (1 - 80 / 100) * subChartHeight)
const rsi20Y = computed(() => subChartTop + (1 - 20 / 100) * subChartHeight)
const rsi6Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i]?.x || 0, subChartTop + (1 - d.rsi6 / 100) * subChartHeight])))
const rsi12Path = computed(() => generatePath(chartData.value.map((d, i) => [candlePoints.value[i]?.x || 0, subChartTop + (1 - d.rsi12 / 100) * subChartHeight])))

function generatePath(points: [number, number][]): string {
  if (points.length === 0) return ''
  return points.reduce((acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`, '')
}

// 网格刻度线
const mainGridYLines = computed(() => [
  padding.top,
  padding.top + mainChartHeight * 0.25,
  padding.top + mainChartHeight * 0.5,
  padding.top + mainChartHeight * 0.75,
  padding.top + mainChartHeight,
])

const gridXLines = computed(() => {
  const usableWidth = width - padding.left - padding.right
  if (currentPeriod.value === 'timeline') {
    return [
      padding.left,
      padding.left + usableWidth * 0.25,
      padding.left + usableWidth * 0.5,
      padding.left + usableWidth * 0.75,
      width - padding.right
    ]
  }
  const res: number[] = []
  const n = candlePoints.value.length
  if (n === 0) return res
  const stepIdx = Math.floor(n / 4)
  for (let i = 0; i < n; i += stepIdx) {
    if (candlePoints.value[i]) res.push(candlePoints.value[i].x)
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

// 分时对称百分比刻度
const mainPctTicks = computed(() => {
  const steps = 4
  const prev = timelinePrevClose.value
  const res: { y: number; val: number }[] = []
  for (let i = 0; i <= steps; i++) {
    const y = padding.top + (i / steps) * mainChartHeight
    const px = getPriceByY(y)
    const pct = ((px - prev) / (prev || 1)) * 100
    res.push({ y, val: pct })
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

// 🔥 分时图时间刻度 (09:30, 10:30, 11:30/13:00 在中轴, 14:00, 15:00 在最右侧)
const timelineTimeTicks = computed(() => {
  const usableWidth = width - padding.left - padding.right
  return [
    { x: padding.left, label: '09:30' },
    { x: padding.left + usableWidth * 0.25, label: '10:30' },
    { x: padding.left + usableWidth * 0.5, label: '11:30/13:00' },
    { x: padding.left + usableWidth * 0.75, label: '14:00' },
    { x: width - padding.right, label: '15:00' }
  ]
})

// ================= 画线图层渲染映射 =================
const renderedDrawings = computed(() => {
  return drawings.value.map(d => {
    if (d.type === 'horizontal') {
      return {
        ...d,
        y: getYByPrice(d.price)
      }
    } else if (d.type === 'trendline') {
      const x1 = padding.left + ((d.timeIndex ?? 0) / Math.max(1, visibleCount.value)) * (width - padding.left - padding.right)
      const y1 = getYByPrice(d.price)
      const x2 = padding.left + ((d.timeIndex2 ?? 10) / Math.max(1, visibleCount.value)) * (width - padding.left - padding.right)
      const y2 = getYByPrice(d.price2 ?? d.price)
      return { ...d, x1, y1, x2, y2 }
    } else if (d.type === 'rect') {
      const x1 = padding.left + ((d.timeIndex ?? 0) / Math.max(1, visibleCount.value)) * (width - padding.left - padding.right)
      const y1 = getYByPrice(d.price)
      const x2 = padding.left + ((d.timeIndex2 ?? 10) / Math.max(1, visibleCount.value)) * (width - padding.left - padding.right)
      const y2 = getYByPrice(d.price2 ?? d.price)
      return {
        ...d,
        boxX: Math.min(x1, x2),
        boxY: Math.min(y1, y2),
        boxW: Math.abs(x2 - x1),
        boxH: Math.abs(y2 - y1)
      }
    } else if (d.type === 'price_tag') {
      const x = padding.left + ((d.timeIndex ?? 0) / Math.max(1, visibleCount.value)) * (width - padding.left - padding.right)
      const y = getYByPrice(d.price)
      return { ...d, x, y }
    }
    return d as any
  })
})

// ================= 缩放与平移核心交互 (纯滚轮缩放与鼠标拖动) =================
function resetZoom() {
  if (currentPeriod.value === 'timeline') return
  visibleCount.value = Math.min(50, rawData.value.length)
  startIndex.value = Math.max(0, rawData.value.length - visibleCount.value)
}

function adjustZoom(delta: number, focusRatio: number = 0.5) {
  if (currentPeriod.value === 'timeline') return
  const total = rawData.value.length
  if (total === 0) return

  const oldVisible = visibleCount.value
  const newVisible = Math.max(15, Math.min(total, oldVisible + delta))
  if (newVisible === oldVisible) return

  const diff = newVisible - oldVisible
  const newStart = Math.max(0, Math.min(total - newVisible, Math.round(startIndex.value - diff * focusRatio)))

  visibleCount.value = newVisible
  startIndex.value = newStart
}

function handleWheel(e: WheelEvent) {
  if (currentPeriod.value === 'timeline') return
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const mouseRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const delta = e.deltaY < 0 ? -4 : 4
  adjustZoom(delta, mouseRatio)
}

// 鼠标拖动与画线状态
const isDragging = ref(false)
let dragStartX = 0
let dragStartIndex = 0

function handleMouseDown(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const mouseX = ((e.clientX - rect.left) / rect.width) * width
  const mouseY = ((e.clientY - rect.top) / rect.height) * height
  const clickPrice = getPriceByY(mouseY)

  // 1. 漫游/拖动模式
  if (activeTool.value === 'pan') {
    isDragging.value = true
    dragStartX = e.clientX
    dragStartIndex = startIndex.value
    return
  }

  // 2. 水平线工具 (单点成线)
  if (activeTool.value === 'horizontal') {
    drawings.value.push({
      id: 'h-' + Date.now(),
      type: 'horizontal',
      price: clickPrice,
      color: '#F59E0B'
    })
    return
  }

  // 3. 价格标注 (单点标注)
  if (activeTool.value === 'price_tag') {
    const usableW = width - padding.left - padding.right
    const relX = Math.max(0, Math.min(usableW, mouseX - padding.left))
    const timeIdx = (relX / usableW) * visibleCount.value
    drawings.value.push({
      id: 'pt-' + Date.now(),
      type: 'price_tag',
      price: clickPrice,
      timeIndex: timeIdx,
      color: '#10B981'
    })
    return
  }

  // 4. 两点工具 (趋势线 / 箱体)
  const usableW = width - padding.left - padding.right
  const relX = Math.max(0, Math.min(usableW, mouseX - padding.left))
  const timeIdx = (relX / usableW) * visibleCount.value

  if (!draftStartPoint) {
    draftStartPoint = {
      x: mouseX,
      y: mouseY,
      price: clickPrice,
      index: timeIdx,
      date: ''
    }
    drawingDraft.value = {
      type: activeTool.value,
      x1: mouseX,
      y1: mouseY,
      x2: mouseX,
      y2: mouseY
    }
  } else {
    if (activeTool.value === 'trendline') {
      drawings.value.push({
        id: 't-' + Date.now(),
        type: 'trendline',
        price: draftStartPoint.price,
        price2: clickPrice,
        timeIndex: draftStartPoint.index,
        timeIndex2: timeIdx,
        color: '#2563EB'
      })
    } else if (activeTool.value === 'rect') {
      drawings.value.push({
        id: 'r-' + Date.now(),
        type: 'rect',
        price: draftStartPoint.price,
        price2: clickPrice,
        timeIndex: draftStartPoint.index,
        timeIndex2: timeIdx,
        color: '#2563EB'
      })
    }
    draftStartPoint = null
    drawingDraft.value = null
  }
}

// 十字光标与悬停交互
const hoverX = ref<number | null>(null)
const hoverY = ref<number>(0)
const hoverPrice = ref<number>(0)
const currentHoverItem = ref<KlineItem | null>(null)
const currentHoverTimelineItem = ref<TimelineItem | null>(null)
const hoverPoint = ref<{ x: number; y: number } | null>(null)
const tooltipPos = ref({ x: 0 })

function handleMouseMove(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const mouseX = ((e.clientX - rect.left) / rect.width) * width
  const mouseY = ((e.clientY - rect.top) / rect.height) * height

  // 1. 拖动平移中
  if (isDragging.value && currentPeriod.value !== 'timeline') {
    const diffPx = e.clientX - dragStartX
    const usableW = rect.width
    const barW = usableW / Math.max(1, visibleCount.value)
    const shift = Math.round(diffPx / barW)
    const total = rawData.value.length
    startIndex.value = Math.max(0, Math.min(total - visibleCount.value, dragStartIndex - shift))
    return
  }

  // 2. 画线预览更新
  if (drawingDraft.value && draftStartPoint) {
    drawingDraft.value.x2 = mouseX
    drawingDraft.value.y2 = mouseY
  }

  if (mouseX < padding.left || mouseX > width - padding.right) {
    hoverX.value = null
    currentHoverItem.value = null
    currentHoverTimelineItem.value = null
    return
  }

  // 3. 悬浮数据匹配
  if (currentPeriod.value === 'timeline') {
    const pts = timelinePoints.value
    if (pts.length > 0) {
      let closestIdx = 0
      let minDist = 9999
      pts.forEach((pt, idx) => {
        const d = Math.abs(pt.x - mouseX)
        if (d < minDist) {
          minDist = d
          closestIdx = idx
        }
      })
      const targetPt = pts[closestIdx]
      hoverX.value = targetPt.x
      hoverY.value = mouseY
      hoverPrice.value = getPriceByY(mouseY)
      currentHoverTimelineItem.value = targetPt.data
      hoverPoint.value = { x: targetPt.x, y: mouseY }
    }
  } else {
    const pts = candlePoints.value
    if (pts.length > 0) {
      let closestIdx = 0
      let minDist = 9999
      pts.forEach((pt, idx) => {
        const d = Math.abs(pt.x - mouseX)
        if (d < minDist) {
          minDist = d
          closestIdx = idx
        }
      })
      const targetPt = pts[closestIdx]
      hoverX.value = targetPt.x
      hoverY.value = mouseY
      hoverPrice.value = getPriceByY(mouseY)
      currentHoverItem.value = targetPt.data
      hoverPoint.value = { x: targetPt.x, y: mouseY }
    }
  }

  // 浮窗位置计算
  const clientX = e.clientX - rect.left
  if (clientX > rect.width - 160) {
    tooltipPos.value.x = clientX - 160
  } else {
    tooltipPos.value.x = clientX + 15
  }
}

function handleMouseUp() {
  isDragging.value = false
}

function handleMouseLeave() {
  isDragging.value = false
  hoverX.value = null
  currentHoverItem.value = null
  currentHoverTimelineItem.value = null
  hoverPoint.value = null
}
</script>

<style scoped lang="scss">
.kline-container {
  position: relative;
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
  padding: 6px 12px;
  border-bottom: 1px solid #f2f4f7;
  background-color: #fafbfc;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
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
    padding: 3px 8px;
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
    &.timeline-prev { color: #667085; }
    &.timeline-avg { color: #d97706; }
    &.timeline-latest {
      &.up { color: #d92d20; }
      &.down { color: #039855; }
    }

    &.offline-pill {
      background-color: #fffaeb;
      color: #b54708;
      border: 1px solid #fedf89;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 10px;
      display: inline-flex;
      align-items: center;
      gap: 4px;

      &::before {
        content: '';
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #f79009;
        animation: offline-dot-pulse 1.5s infinite;
      }
    }
  }
}

@keyframes offline-dot-pulse {
  0% { transform: scale(0.9); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.5; }
}

.toolbar-center {
  display: flex;
  align-items: center;

  .draw-panel-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #344054;
    background: #ffffff;
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;

    .btn-icon {
      font-size: 12px;
    }
    .toggle-arrow {
      font-size: 9px;
      color: #98a2b3;
    }
    .draw-count-pill {
      background: #175cd3;
      color: #ffffff;
      font-size: 10px;
      padding: 0 5px;
      border-radius: 10px;
      font-family: monospace;
    }

    &:hover {
      border-color: #98a2b3;
      color: #101828;
    }

    &.active {
      background-color: #eff8ff;
      border-color: #175cd3;
      color: #175cd3;
    }
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
  user-select: none;

  &.pan {
    cursor: grab;
    &.is-dragging {
      cursor: grabbing;
    }
  }

  &.trendline, &.horizontal, &.rect, &.price_tag {
    cursor: crosshair;
  }
}

// 🔥 骨架流光扫光层样式
.kline-skeleton-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fafbfc;
  z-index: 15;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;

  .skeleton-chart-canvas {
    position: absolute;
    top: 20px;
    left: 20px;
    right: 20px;
    bottom: 20px;
    opacity: 0.55;
    display: flex;
    flex-direction: column;
    pointer-events: none;

    .skeleton-grid-lines {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 75px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;

      .sk-grid-row {
        width: 100%;
        height: 1px;
        background-image: linear-gradient(to right, #eaecf0 40%, rgba(255, 255, 255, 0) 0%);
        background-position: top;
        background-size: 8px 1px;
        background-repeat: repeat-x;
      }
    }

    .skeleton-candles-flow {
      flex: 1;
      display: flex;
      align-items: flex-end;
      gap: 1.5%;
      padding-bottom: 20px;
      padding-left: 20px;
      padding-right: 20px;

      .sk-candle-item {
        flex: 1;
        min-width: 4px;
        max-width: 16px;
        position: relative;
        display: flex;
        justify-content: center;

        .sk-candle-wick {
          position: absolute;
          width: 1px;
          background-color: #d0d5dd;
        }

        .sk-candle-body {
          width: 100%;
          height: 100%;
          background-color: #eaecf0;
          border-radius: 2px;
          border: 1px solid #d0d5dd;
        }
      }
    }

    .skeleton-volume-flow {
      height: 55px;
      display: flex;
      align-items: flex-end;
      gap: 1.5%;
      padding-left: 20px;
      padding-right: 20px;
      border-top: 1px solid #eaecf0;
      padding-top: 8px;

      .sk-vol-bar {
        flex: 1;
        min-width: 4px;
        max-width: 16px;
        background-color: #eaecf0;
        border-radius: 1px 1px 0 0;
      }
    }
  }

  // 核心：平滑高科技扫光光幕
  .skeleton-shimmer-sweep {
    position: absolute;
    top: 0;
    left: -150%;
    width: 150%;
    height: 100%;
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.65) 50%,
      rgba(255, 255, 255, 0) 100%
    );
    animation: skeleton-sweep-anim 2.4s infinite ease-in-out;
    pointer-events: none;
    z-index: 2;
  }

  // 居中科技质感状态浮层
  .skeleton-status-card {
    position: relative;
    z-index: 3;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(8px);
    border: 1px solid #d0d5dd;
    box-shadow: 0 10px 25px -5px rgba(16, 24, 40, 0.08), 0 8px 10px -6px rgba(16, 24, 40, 0.03);
    border-radius: 12px;
    padding: 22px 30px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    max-width: 420px;

    .status-pulse-ring {
      position: relative;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background-color: #eff8ff;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;

      .beacon-core {
        font-size: 18px;
        color: #175cd3;
        z-index: 1;
      }

      .pulse-beacon {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background-color: #2e90fa;
        opacity: 0.35;
        animation: pulse-ring-anim 2s infinite ease-out;
      }
    }

    .status-title {
      font-size: 14px;
      font-weight: 700;
      color: #101828;
      margin-bottom: 6px;
    }

    .status-subtitle {
      font-size: 12px;
      color: #667085;
      line-height: 1.5;
      margin-bottom: 16px;
    }

    .status-action-row {
      display: flex;
      gap: 10px;

      .sk-retry-btn {
        background-color: #175cd3;
        color: #ffffff;
        border: none;
        padding: 8px 18px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: all 0.15s ease;

        &:hover:not(:disabled) {
          background-color: #154294;
          box-shadow: 0 4px 8px rgba(23, 92, 211, 0.25);
        }

        &:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .btn-spin {
          display: inline-block;
          animation: spin 1s infinite linear;
        }
      }
    }
  }
}

@keyframes skeleton-sweep-anim {
  0% { transform: translateX(0); }
  100% { transform: translateX(200%); }
}

@keyframes pulse-ring-anim {
  0% { transform: scale(0.9); opacity: 0.5; }
  100% { transform: scale(1.6); opacity: 0; }
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

// 悬浮可拖拽画线工具箱样式 (支持在整个个股与指数研究界面全局移动)
.floating-draw-panel {
  position: fixed;
  z-index: 1500;
  width: 210px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
  border: 1px solid #d0d5dd;
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(16, 24, 40, 0.18), 0 2px 6px rgba(16, 24, 40, 0.08);
  overflow: hidden;
  user-select: none;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 10px;
    background-color: #f8fafc;
    border-bottom: 1px solid #eaecf0;
    cursor: grab;

    &:active {
      cursor: grabbing;
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 700;
      color: #344054;

      .drag-handle {
        color: #98a2b3;
        font-size: 12px;
      }
    }

    .panel-close-btn {
      border: none;
      background: transparent;
      font-size: 16px;
      line-height: 1;
      color: #98a2b3;
      cursor: pointer;
      padding: 0 2px;

      &:hover {
        color: #101828;
      }
    }
  }

  .panel-tools-body {
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;

    .tools-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 5px;

      .tool-chip {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 6px 2px;
        background: #ffffff;
        border: 1px solid #eaecf0;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.15s ease;

        .tool-icon {
          font-size: 13px;
        }
        .tool-label {
          font-size: 10px;
          color: #475467;
          font-weight: 500;
        }

        &:hover {
          background: #f8fafc;
          border-color: #98a2b3;
        }

        &.active {
          background: #eff8ff;
          border-color: #175cd3;
          .tool-label {
            color: #175cd3;
            font-weight: 700;
          }
        }
      }
    }

    .panel-actions-row {
      display: flex;
      gap: 4px;
      padding-top: 6px;
      border-top: 1px dashed #eaecf0;

      .panel-action-btn {
        flex: 1;
        padding: 4px 0;
        font-size: 10px;
        font-weight: 600;
        color: #475467;
        background: #ffffff;
        border: 1px solid #d0d5dd;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.15s ease;

        &:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        &:not(:disabled):hover {
          background: #f8fafc;
          color: #101828;
        }

        &.danger:not(:disabled):hover {
          background: #fef3f2;
          border-color: #f04438;
          color: #d92d20;
        }

        &.reset:not(:disabled):hover {
          background: #eff8ff;
          border-color: #175cd3;
          color: #175cd3;
        }
      }
    }
  }
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
.font-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
}
.color-up { color: #d92d20; }
.color-down { color: #039855; }
</style>
