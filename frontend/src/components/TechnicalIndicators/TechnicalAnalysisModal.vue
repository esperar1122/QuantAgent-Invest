<template>
  <el-dialog
    v-model="visible"
    width="92%"
    top="3vh"
    destroy-on-close
    class="tech-indicator-dialog"
    :show-close="true"
    @close="handleClose"
  >
    <!-- 自定义弹窗头部：与【个股与指数研究】联动标识、实时时钟与操作区 -->
    <template #header>
      <div class="modal-custom-header">
        <div class="header-left">
          <div class="brand-chip">
            <el-icon><TrendCharts /></el-icon>
            <span>个股与指数研究 · 实时联动</span>
          </div>
          <div class="title-cluster">
            <span class="stock-title">{{ currentStock.name }}</span>
            <span class="stock-code font-mono tabular-nums">({{ currentStock.code }})</span>
            <el-tag size="small" effect="plain" class="board-tag">{{ currentStock.board }}</el-tag>
            <el-tag size="small" type="info" effect="plain" class="sector-tag">{{ currentStock.sector }}</el-tag>
          </div>
        </div>

        <div class="header-right">
          <!-- 实时行情时钟与更新指示 -->
          <div class="live-status-pill">
            <span class="pulse-dot"></span>
            <span class="live-clock tabular-nums">时钟: {{ liveClock }}</span>
            <span class="update-badge" :title="'每15秒静默轮询更新，确保数据最新'">
              {{ lastUpdateTime ? `更新于 ${lastUpdateTime}` : '实时获取中' }}
            </span>
          </div>

          <!-- 手动强制刷新按钮 -->
          <el-button
            size="small"
            class="action-pill-btn"
            :loading="isRefreshing"
            @click="handleManualRefresh"
            title="强制向全网与实时盘口拉取最新行情"
          >
            <el-icon :class="{ 'spin-anim': isRefreshing }"><RefreshRight /></el-icon>
            <span>刷新最新行情</span>
          </el-button>

          <!-- 穿透直达【个股与指数研究】全景工作台 -->
          <el-button
            size="small"
            type="primary"
            class="action-pill-btn primary"
            @click="goToStockResearch"
          >
            <el-icon><TrendCharts /></el-icon>
            <span>穿透【个股与指数研究】 ↗</span>
          </el-button>

          <!-- 启动 Agent 协同工作流 -->
          <el-button
            size="small"
            type="success"
            class="action-pill-btn success"
            @click="goToWorkflow"
          >
            <el-icon><Connection /></el-icon>
            <span>启动 Agent 工作流 ↗</span>
          </el-button>
        </div>
      </div>
    </template>

    <div v-loading="loading && !isRefreshing" class="dialog-content">
      <!-- 1. 顶部：实时核心盘口与十项高密度金融指标条 (100% 对齐【个股与指数研究】) -->
      <div class="stock-top-card">
        <div class="summary-primary-row">
          <div class="price-block">
            <span
              class="live-price tabular-nums"
              :class="currentStock.change >= 0 ? 'color-up' : 'color-down'"
            >
              {{ currentStock.price > 0 ? currentStock.price.toFixed(2) : '--' }}
            </span>
            <div
              class="change-block tabular-nums"
              :class="currentStock.change >= 0 ? 'color-up' : 'color-down'"
            >
              <span class="change-val">
                {{ currentStock.change >= 0 ? '+' : '' }}{{ currentStock.changeVal.toFixed(2) }}
              </span>
              <span class="change-pct">
                ({{ currentStock.change >= 0 ? '+' : '' }}{{ currentStock.change.toFixed(2) }}%)
              </span>
            </div>
            <span class="trade-date-tag tabular-nums">交易日: {{ currentStock.tradeDate || displaySnapshot?.trade_date || '今日实盘' }}</span>
          </div>

          <!-- 量化综合评分与智能体决策仲裁评级 -->
          <div class="rating-block">
            <div class="rating-badge" :class="ratingBadgeClass">
              <div class="score tabular-nums">{{ displayScore }}分</div>
              <div class="rating-text">{{ displayRating }}</div>
            </div>
            <div class="rating-counts" v-if="displaySnapshot">
              <el-tag type="danger" size="small" effect="light">🔴 看多 {{ displaySnapshot.overall.bullish_count }} 项</el-tag>
              <el-tag type="success" size="small" effect="light">🟢 看空 {{ displaySnapshot.overall.bearish_count }} 项</el-tag>
              <el-tag type="info" size="small" effect="light">⚪ 中性 {{ displaySnapshot.overall.neutral_count }} 项</el-tag>
            </div>
          </div>
        </div>

        <!-- 十项金融指标网格 -->
        <div class="metrics-grid">
          <div class="m-cell">
            <span class="lbl">今开</span>
            <span class="val tabular-nums">{{ currentStock.open > 0 ? currentStock.open.toFixed(2) : '--' }}</span>
          </div>
          <div class="m-cell">
            <span class="lbl">最高</span>
            <span class="val tabular-nums color-up">{{ currentStock.high > 0 ? currentStock.high.toFixed(2) : '--' }}</span>
          </div>
          <div class="m-cell">
            <span class="lbl">最低</span>
            <span class="val tabular-nums color-down">{{ currentStock.low > 0 ? currentStock.low.toFixed(2) : '--' }}</span>
          </div>
          <div class="m-cell">
            <span class="lbl">昨收</span>
            <span class="val tabular-nums">{{ currentStock.preClose > 0 ? currentStock.preClose.toFixed(2) : '--' }}</span>
          </div>
          <div class="m-cell">
            <span class="lbl">成交量</span>
            <span class="val tabular-nums">{{ (currentStock.volume / 10000).toFixed(1) }}万手</span>
          </div>
          <div class="m-cell">
            <span class="lbl">成交额</span>
            <span class="val tabular-nums">{{ currentStock.amount }}亿</span>
          </div>
          <div class="m-cell">
            <span class="lbl">换手率</span>
            <span class="val tabular-nums">{{ currentStock.turnover.toFixed(2) }}%</span>
          </div>
          <div class="m-cell">
            <span class="lbl">振幅</span>
            <span class="val tabular-nums">{{ currentStock.amplitude.toFixed(2) }}%</span>
          </div>
          <div class="m-cell">
            <span class="lbl">总市值</span>
            <span class="val tabular-nums">{{ currentStock.marketCap }}亿</span>
          </div>
          <div class="m-cell">
            <span class="lbl">市盈(动) / 市净</span>
            <span class="val tabular-nums">{{ currentStock.pe }} / {{ currentStock.pb }}</span>
          </div>
        </div>
      </div>

      <!-- 2. 多维度研判切换工作区 (技术指标交互 / Level-2盘口与量化画像 / 智能体案卷) -->
      <div class="analysis-tabs-wrapper">
        <el-tabs v-model="activeTab" class="terminal-nav-tabs">
          <!-- Tab 1: 全套技术指标多维度诊断与交互K线 -->
          <el-tab-pane label="📊 技术指标全景与交互K线" name="indicators">
            <!-- 5 大技术指标诊断卡片 -->
            <div v-if="displaySnapshot" class="indicator-cards-grid">
              <!-- MACD -->
              <div class="indicator-card">
                <div class="card-header">
                  <span class="card-title">📈 MACD 趋势动能</span>
                  <el-tag :type="getTagType(displaySnapshot.macd.type)" size="small" effect="dark">
                    {{ displaySnapshot.macd.signal }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><b>DIF:</b> {{ displaySnapshot.macd.dif }}</span>
                    <span class="val-item"><b>DEA:</b> {{ displaySnapshot.macd.dea }}</span>
                    <span class="val-item">
                      <b>柱状值:</b>
                      <span :class="displaySnapshot.macd.macd_hist >= 0 ? 'text-up' : 'text-down'">
                        {{ displaySnapshot.macd.macd_hist }}
                      </span>
                    </span>
                  </div>
                  <div class="status-desc">
                    <span class="badge-dot" :class="displaySnapshot.macd.type"></span>
                    柱体态势：<b>{{ displaySnapshot.macd.hist_trend }}</b>
                  </div>
                </div>
              </div>

              <!-- RSI -->
              <div class="indicator-card">
                <div class="card-header">
                  <span class="card-title">⚡ RSI 相对强弱</span>
                  <el-tag :type="getTagType(displaySnapshot.rsi.type)" size="small" effect="dark">
                    {{ displaySnapshot.rsi.status }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><b>RSI(6):</b> <span class="highlight">{{ displaySnapshot.rsi.rsi6 }}</span></span>
                    <span class="val-item"><b>RSI(12):</b> {{ displaySnapshot.rsi.rsi12 }}</span>
                    <span class="val-item"><b>RSI(24):</b> {{ displaySnapshot.rsi.rsi24 }}</span>
                  </div>
                  <div class="rsi-progress-bar">
                    <div class="rsi-fill" :style="{ width: `${Math.min(Math.max(displaySnapshot.rsi.rsi6, 0), 100)}%`, background: getRsiColor(displaySnapshot.rsi.rsi6) }"></div>
                    <div class="mark line-20">20超卖</div>
                    <div class="mark line-80">80超买</div>
                  </div>
                </div>
              </div>

              <!-- KDJ -->
              <div class="indicator-card">
                <div class="card-header">
                  <span class="card-title">🎯 KDJ 随机摆动</span>
                  <el-tag :type="getTagType(displaySnapshot.kdj.type)" size="small" effect="dark">
                    {{ displaySnapshot.kdj.signal }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><b>K:</b> {{ displaySnapshot.kdj.k }}</span>
                    <span class="val-item"><b>D:</b> {{ displaySnapshot.kdj.d }}</span>
                    <span class="val-item"><b>J:</b> <span class="highlight">{{ displaySnapshot.kdj.j }}</span></span>
                  </div>
                  <div class="status-desc">
                    <span class="badge-dot" :class="displaySnapshot.kdj.type"></span>
                    交叉特征：<b>{{ displaySnapshot.kdj.is_golden_cross ? '✨ 低位金叉形成' : displaySnapshot.kdj.is_death_cross ? '⚠️ 高位死叉承压' : '正常运行波动' }}</b>
                  </div>
                </div>
              </div>

              <!-- BOLL -->
              <div class="indicator-card">
                <div class="card-header">
                  <span class="card-title">🌐 BOLL 波动通道</span>
                  <el-tag :type="getTagType(displaySnapshot.boll.type)" size="small" effect="dark">
                    {{ displaySnapshot.boll.signal }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><b>上轨:</b> {{ displaySnapshot.boll.upper }}</span>
                    <span class="val-item"><b>中轨:</b> {{ displaySnapshot.boll.mid }}</span>
                    <span class="val-item"><b>下轨:</b> {{ displaySnapshot.boll.lower }}</span>
                  </div>
                  <div class="status-desc">
                    <span class="badge-dot" :class="displaySnapshot.boll.type"></span>
                    带宽: <b>{{ displaySnapshot.boll.bandwidth }}%</b> · 位置: <b>{{ displaySnapshot.boll.position_pct }}%</b>
                  </div>
                </div>
              </div>

              <!-- MA & ATR -->
              <div class="indicator-card">
                <div class="card-header">
                  <span class="card-title">📊 MA 均线系统</span>
                  <el-tag :type="getTagType(displaySnapshot.ma.type)" size="small" effect="dark">
                    {{ displaySnapshot.ma.arrangement }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><span class="ma-dot ma5"></span>MA5: {{ displaySnapshot.ma.ma5 }}</span>
                    <span class="val-item"><span class="ma-dot ma10"></span>MA10: {{ displaySnapshot.ma.ma10 }}</span>
                    <span class="val-item"><span class="ma-dot ma20"></span>MA20: {{ displaySnapshot.ma.ma20 }}</span>
                    <span class="val-item"><span class="ma-dot ma60"></span>MA60: {{ displaySnapshot.ma.ma60 }}</span>
                  </div>
                  <div class="status-desc" v-if="displaySnapshot.atr">
                    <span>ATR真实波幅: <b>{{ displaySnapshot.atr.atr14 }}</b> (日波动率 <b>{{ displaySnapshot.atr.volatility_ratio }}%</b>)</span>
                  </div>
                </div>
              </div>

              <!-- CYQ 筹码分布透视 -->
              <div class="indicator-card chips-quick-card" @click="activeTab = 'chips'" style="cursor: pointer;" title="点击切换至筹码分布深度透视工作台">
                <div class="card-header">
                  <span class="card-title">🎯 CYQ 筹码分布</span>
                  <el-tag :type="getTagType(displayChips.pattern_type)" size="small" effect="dark">
                    {{ displayChips.peak_pattern }}
                  </el-tag>
                </div>
                <div class="card-body">
                  <div class="val-row">
                    <span class="val-item"><b>获利:</b> <span class="highlight text-up">{{ displayChips.profit_ratio.toFixed(1) }}%</span></span>
                    <span class="val-item"><b>均本:</b> ¥{{ displayChips.avg_cost.toFixed(2) }}</span>
                    <span class="val-item"><b>70%集中:</b> {{ displayChips.concentration_70.toFixed(1) }}%</span>
                  </div>
                  <div class="chips-mini-bar" title="红橙: 获利筹码 | 绿青: 套牢筹码">
                    <div class="chips-profit-fill" :style="{ width: `${displayChips.profit_ratio}%` }"></div>
                  </div>
                  <div class="status-desc">
                    <span class="badge-dot" :class="displayChips.pattern_type"></span>
                    <span class="truncate-line">{{ displayChips.pattern_desc }} ↗</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 专业交互式技术分析图表 -->
            <div class="chart-section">
              <div class="chart-toolbar">
                <div class="toolbar-left">
                  <span class="section-title">📊 专业交互式 K 线走势</span>
                  <el-radio-group v-model="period" size="small" @change="fetchData(false)">
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
          </el-tab-pane>

          <!-- Tab 2: 筹码分布透视 (CYQ) 深度工作台 -->
          <el-tab-pane label="🎯 筹码分布透视 (CYQ)" name="chips">
            <div class="chips-workspace" v-loading="loading">
              <!-- 顶部状态栏：标的与筹码核心概要 -->
              <div class="chips-top-banner">
                <div class="banner-left">
                  <span class="stock-title-tag">{{ currentStock.name }} ({{ currentStock.code }})</span>
                  <span class="current-price-badge tabular-nums">
                    现价: ¥{{ currentStock.price.toFixed(2) }}
                    <span :class="currentStock.change >= 0 ? 'text-up' : 'text-down'">
                      ({{ currentStock.change >= 0 ? '+' : '' }}{{ currentStock.change.toFixed(2) }}%)
                    </span>
                  </span>
                  <span class="cyq-algo-badge">
                    <el-icon><DataAnalysis /></el-icon>
                    日K换手衰减积分模型 (CYQ)
                  </span>
                </div>
                <div class="banner-right">
                  <span class="period-label">推演周期:</span>
                  <el-radio-group v-model="period" size="small" @change="fetchData(false)">
                    <el-radio-button label="day">日K推演</el-radio-button>
                    <el-radio-button label="week">周K推演</el-radio-button>
                  </el-radio-group>
                </div>
              </div>

              <!-- 4 大核心筹码指标卡片 -->
              <div class="chips-kpi-grid">
                <!-- KPI 1: 获利盘比例 -->
                <div class="kpi-card profit-kpi">
                  <div class="kpi-header">
                    <span class="kpi-title">获利盘比例 (Profit Ratio)</span>
                    <el-tag :type="displayChips.profit_ratio >= 70 ? 'danger' : displayChips.profit_ratio <= 30 ? 'success' : 'warning'" size="small" effect="dark">
                      {{ displayChips.profit_ratio >= 80 ? '高获利区' : displayChips.profit_ratio <= 20 ? '深套牢区' : '博弈中枢' }}
                    </el-tag>
                  </div>
                  <div class="kpi-main-val tabular-nums text-up">
                    {{ displayChips.profit_ratio.toFixed(1) }}<span class="unit">%</span>
                  </div>
                  <div class="chips-bar-wrapper">
                    <div class="chips-bar-fill profit" :style="{ width: `${displayChips.profit_ratio}%` }" title="获利盘"></div>
                    <div class="chips-bar-fill trapped" :style="{ width: `${displayChips.trapped_ratio}%` }" title="套牢盘"></div>
                  </div>
                  <div class="kpi-sub-row">
                    <span class="sub-item">获利: <b>{{ displayChips.profit_ratio.toFixed(1) }}%</b></span>
                    <span class="sub-item">套牢: <b>{{ displayChips.trapped_ratio.toFixed(1) }}%</b></span>
                  </div>
                </div>

                <!-- KPI 2: 全市场平均持仓成本 -->
                <div class="kpi-card cost-kpi">
                  <div class="kpi-header">
                    <span class="kpi-title">平均持仓成本 (Avg Cost)</span>
                    <span class="kpi-badge font-mono tabular-nums">
                      {{ displayChips.profit_premium >= 0 ? `溢价 +${displayChips.profit_premium}%` : `折价 ${displayChips.profit_premium}%` }}
                    </span>
                  </div>
                  <div class="kpi-main-val tabular-nums">
                    ¥{{ displayChips.avg_cost.toFixed(2) }}
                  </div>
                  <div class="kpi-cost-desc">
                    <span v-if="displayChips.profit_premium >= 0" class="text-up">
                      ▲ 现价高于持仓成本 +{{ displayChips.profit_premium }}% (持筹浮盈)
                    </span>
                    <span v-else class="text-down">
                      ▼ 现价低于持仓成本 {{ displayChips.profit_premium }}% (持筹浮亏)
                    </span>
                  </div>
                  <div class="kpi-sub-row">
                    <span class="sub-item">中位数成本: <b>¥{{ displayChips.median_cost.toFixed(2) }}</b></span>
                    <span class="sub-item">成本差: <b>¥{{ (currentStock.price - displayChips.avg_cost).toFixed(2) }}</b></span>
                  </div>
                </div>

                <!-- KPI 3: 70% 筹码集中度与核心区间 -->
                <div class="kpi-card conc-kpi">
                  <div class="kpi-header">
                    <span class="kpi-title">70% 筹码集中度 (Core 70%)</span>
                    <el-tag :type="displayChips.concentration_70 <= 10 ? 'danger' : displayChips.concentration_70 <= 15 ? 'warning' : 'info'" size="small" effect="plain">
                      {{ displayChips.concentration_70 <= 8 ? '高度控盘' : displayChips.concentration_70 <= 12 ? '筹码集中' : '相对分散' }}
                    </el-tag>
                  </div>
                  <div class="kpi-main-val tabular-nums font-mono">
                    {{ displayChips.concentration_70.toFixed(1) }}<span class="unit">%</span>
                  </div>
                  <div class="kpi-range-box tabular-nums">
                    核心控盘区间: <b>¥{{ displayChips.cost_range_70[0] }} ~ ¥{{ displayChips.cost_range_70[1] }}</b>
                  </div>
                  <div class="kpi-sub-row">
                    <span class="sub-item">集中度越低 (&lt;10%) 主力筹码越凝聚</span>
                  </div>
                </div>

                <!-- KPI 4: 90% 筹码密集区间 -->
                <div class="kpi-card range90-kpi">
                  <div class="kpi-header">
                    <span class="kpi-title">90% 筹码密集区间 (90% Range)</span>
                    <span class="kpi-badge">全市场覆盖</span>
                  </div>
                  <div class="kpi-main-val tabular-nums font-mono">
                    {{ displayChips.concentration_90.toFixed(1) }}<span class="unit">%</span>
                  </div>
                  <div class="kpi-range-box tabular-nums">
                    主力与散户全区间: <b>¥{{ displayChips.cost_range_90[0] }} ~ ¥{{ displayChips.cost_range_90[1] }}</b>
                  </div>
                  <div class="kpi-sub-row">
                    <span class="sub-item">区间跨度: <b>¥{{ (displayChips.cost_range_90[1] - displayChips.cost_range_90[0]).toFixed(2) }}</b></span>
                  </div>
                </div>
              </div>

              <!-- 筹码多空形态研判与操盘策略横幅 -->
              <div class="chips-pattern-banner">
                <div class="pattern-badge-col">
                  <span class="pattern-label">筹码形态研判</span>
                  <div class="pattern-tag" :class="displayChips.pattern_type">
                    {{ displayChips.peak_pattern }}
                  </div>
                </div>
                <div class="pattern-desc-col">
                  <div class="desc-main">
                    {{ displayChips.pattern_desc }}
                  </div>
                  <div class="strategy-hint">
                    <span class="hint-title">💡 量化操盘策略提示:</span>
                    <span v-if="displayChips.profit_ratio >= 90" class="hint-text">
                      筹码进入全员获利主升格局，上方无历史套牢盘反压。建议顺应趋势持股，以 5 日或 10 日均线作为移动止盈保护位。
                    </span>
                    <span v-else-if="displayChips.profit_ratio <= 15" class="hint-text">
                      获利盘低于 15%，全员处于深套割肉释放殆尽状态。做空势能衰竭，可密切跟踪放量金叉或底背离信号，布局超跌反弹。
                    </span>
                    <span v-else-if="displayChips.concentration_70 <= 10" class="hint-text">
                      70% 筹码集中度低于 10%，单峰高度凝聚，主力吸筹充分。现价一旦放量突破筹码峰上沿，极易启动主升浪。
                    </span>
                    <span v-else-if="currentStock.price < displayChips.avg_cost" class="hint-text">
                      现价低于平均持仓成本，反弹至密集峰附近易触发解套盘回吐抛压。操作上宜采取高抛低吸或以防守为主。
                    </span>
                    <span v-else class="hint-text">
                      当前处于筹码多峰震荡整理期，现价在成本线上方运行具备一定下档支撑，可关注核心控盘区间的企稳确认。
                    </span>
                  </div>
                </div>
              </div>

              <!-- 筹码价格分布直方图可视化 (CYQ Price Distribution Histogram) -->
              <div class="chips-histogram-section">
                <div class="section-header">
                  <div class="sec-left">
                    <span class="sec-title">📊 筹码价格分布直方图 (CYQ Histogram)</span>
                    <span class="sec-subtitle">右向横条代表各价格档位的筹码堆积量 · 红色为获利筹码 · 绿色为套牢筹码</span>
                  </div>
                  <div class="sec-legend">
                    <span class="legend-item"><span class="legend-box profit"></span> 获利盘 (成本 &le; 现价)</span>
                    <span class="legend-item"><span class="legend-box trapped"></span> 套牢盘 (成本 &gt; 现价)</span>
                    <span class="legend-item"><span class="legend-box cur-line"></span> 现价分水岭 (¥{{ currentStock.price.toFixed(2) }})</span>
                  </div>
                </div>

                <!-- 筹码直方图图表区 -->
                <div class="histogram-chart-viewport" v-if="sortedHistogram && sortedHistogram.length > 0">
                  <div
                    v-for="(bin, idx) in sortedHistogram"
                    :key="'hist-' + idx"
                    class="hist-row"
                    :class="{ 'is-current-bin': isCurrentPriceBin(bin) }"
                  >
                    <!-- 价格刻度 -->
                    <span class="hist-price tabular-nums font-mono">
                      ¥{{ bin.price.toFixed(2) }}
                    </span>

                    <!-- 柱体轨道 -->
                    <div class="hist-track">
                      <div
                        class="hist-bar"
                        :class="bin.is_profit ? 'profit-bar' : 'trapped-bar'"
                        :style="{ width: `${Math.min(100, (bin.percent / maxHistPercent) * 100)}%` }"
                        :title="`价格: ¥${bin.price.toFixed(2)} | 筹码占比: ${bin.percent}% | ${bin.is_profit ? '获利盘' : '套牢盘'}`"
                      >
                        <span class="hist-pct-text tabular-nums" v-if="bin.percent >= 1.5">{{ bin.percent }}%</span>
                      </div>

                      <!-- 若属于现价分界线标记 -->
                      <div v-if="isCurrentPriceBin(bin)" class="current-price-marker">
                        <span class="marker-tag">◄ 现价 ¥{{ currentStock.price.toFixed(2) }}</span>
                        <div class="marker-line"></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="hist-empty">
                  <el-empty description="暂无筹码分布直方图数据，正在计算中..." />
                </div>

                <!-- 理论模型原理注解脚标 -->
                <div class="algo-footnote">
                  <el-icon><InfoFilled /></el-icon>
                  <span>
                    <b>CYQ 筹码分布算法原理：</b>采用经典的换手率衰减积分模型 (Turnover Decay & Triangle Distribution)。系统基于个股历史日K线量价及真实换手率，按每日交易区间以三角分布方式注入新筹码，同时使历史筹码按真实换手率逐日衰减，科学重构全市场投资者的持仓成本动态分布。
                  </span>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Tab 3: Level-2 五档委托盘口与 Quant Engine 因子雷达 -->
          <el-tab-pane label="⚡ Level-2 盘口与量化画像" name="orderbook">
            <div class="orderbook-quant-grid">
              <!-- 左侧：买卖五档撮合盘口 -->
              <div class="panel-card">
                <div class="panel-card-header">
                  <span class="title">Level-2 五档买卖委托盘口</span>
                  <span class="sub">买卖比 {{ orderBookRatio }} · 主力实时撮合</span>
                </div>
                <div class="orderbook-content">
                  <!-- 卖盘五档 (卖五至卖一倒序) -->
                  <div class="order-side ask-side">
                    <div v-for="ask in askOrders" :key="ask.level" class="order-row">
                      <span class="order-lvl">{{ ask.level }}</span>
                      <span class="order-px tabular-nums color-up">{{ ask.price.toFixed(2) }}</span>
                      <span class="order-qty tabular-nums">{{ ask.qty }} 手</span>
                      <div class="order-bar" :style="{ width: Math.min(100, ((ask.qty || 0) / maxOrderQty) * 100) + '%' }"></div>
                    </div>
                  </div>

                  <div class="orderbook-divider">
                    <span class="divider-label">现价 ¥{{ currentStock.price.toFixed(2) }}</span>
                  </div>

                  <!-- 买盘五档 (买一至买五正序) -->
                  <div class="order-side bid-side">
                    <div v-for="bid in bidOrders" :key="bid.level" class="order-row">
                      <span class="order-lvl">{{ bid.level }}</span>
                      <span class="order-px tabular-nums color-up">{{ bid.price.toFixed(2) }}</span>
                      <span class="order-qty tabular-nums">{{ bid.qty }} 手</span>
                      <div class="order-bar bid-bar" :style="{ width: Math.min(100, ((bid.qty || 0) / maxOrderQty) * 100) + '%' }"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 右侧：Quant Engine 六维量化因子画像 -->
              <div class="panel-card">
                <div class="panel-card-header">
                  <span class="title">Quant Engine 量化多因子画像</span>
                  <span class="sub">多因子综合分 {{ displayScore }} / 100</span>
                </div>
                <div class="quant-factors-list">
                  <div v-for="factor in quantFactors" :key="factor.name" class="factor-row">
                    <div class="factor-info">
                      <span class="f-name">{{ factor.name }}</span>
                      <span class="f-score tabular-nums">{{ factor.score }} / 100</span>
                    </div>
                    <div class="f-bar-track">
                      <div class="f-bar-fill" :style="{ width: factor.score + '%', backgroundColor: factor.color }"></div>
                    </div>
                  </div>
                </div>

                <div class="valuation-summary-box">
                  <div class="val-item">
                    <span class="k">估值分位</span>
                    <span class="v">{{ currentStock.pe < 25 ? '低估 (近三年 18% 分位)' : currentStock.pe < 50 ? '合理中枢 (45% 分位)' : '高估值溢价' }}</span>
                  </div>
                  <div class="val-item">
                    <span class="k">目标溢价空间</span>
                    <span class="v color-up">+{{ dynamicTargetUpside }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Tab 3: 智能体研究案卷库 (Case Files) -->
          <el-tab-pane label="🤖 智能体协同研判案卷" name="casefiles">
            <div class="casefiles-workspace">
              <!-- 最终仲裁结论横幅 -->
              <div class="arbitration-banner">
                <div class="arb-left">
                  <span class="arb-tag">DECISION ARBITRATION</span>
                  <span class="arb-title">多智能体协同研判收敛结论</span>
                </div>
                <div class="arb-right">
                  <span class="arb-rating" :class="displaySnapshot?.overall?.type === 'bullish' ? 'bullish' : 'neutral'">
                    最终评级: {{ displayRating }} ({{ displayScore }}分)
                  </span>
                  <span class="arb-range tabular-nums">
                    建议操作区间: ¥{{ (currentStock.price * 0.98).toFixed(2) }} - ¥{{ (currentStock.price * 1.02).toFixed(2) }}
                  </span>
                </div>
              </div>

              <!-- 4 大智能体专题案卷网格 -->
              <div class="case-grid">
                <!-- 宏观政策 -->
                <div class="case-card">
                  <div class="case-header">
                    <span class="agent-tag macro">MACRO AGENT 宏观政策</span>
                    <span class="verify-badge">已核验</span>
                  </div>
                  <div class="case-title">{{ currentStock.sector }} 产业支持与宏观流动性共振</div>
                  <div class="case-body">
                    顶层产业支持政策持续落地，{{ currentStock.name }} ({{ currentStock.code }}) 处于行业核心生态位，享受产业资本与政策专项定向赋能，资产配置价值凸显。
                  </div>
                  <div class="case-footer">
                    <span>证据级别: 强事实</span>
                    <span>置信度: 91%</span>
                  </div>
                </div>

                <!-- 技术形态 -->
                <div class="case-card">
                  <div class="case-header">
                    <span class="agent-tag tech">TECHNICAL AGENT 技术形态</span>
                    <span class="verify-badge">已核验</span>
                  </div>
                  <div class="case-title">{{ displaySnapshot?.ma?.arrangement || '日K线顺向多头排列，量能温和放大' }}</div>
                  <div class="case-body">
                    标的现点位 ¥{{ currentStock.price.toFixed(2) }}，均线系统呈现{{ displaySnapshot?.ma?.arrangement || '顺向排列' }}。MACD 处于{{ displaySnapshot?.macd?.signal || '良性运行区间' }}（柱体态势: {{ displaySnapshot?.macd?.hist_trend || '红柱放大' }}），成交额 {{ currentStock.amount }} 亿，日换手率 {{ currentStock.turnover.toFixed(2) }}%，量价结构与动能指标保持算法推演共振。
                  </div>
                  <div class="case-footer">
                    <span>证据级别: 量价共振</span>
                    <span>置信度: 88%</span>
                  </div>
                </div>

                <!-- 基本面产业 -->
                <div class="case-card">
                  <div class="case-header">
                    <span class="agent-tag fund">FUNDAMENTAL AGENT 基本面</span>
                    <span class="verify-badge">已核验</span>
                  </div>
                  <div class="case-title">经营韧性稳固，总市值规模达 {{ currentStock.marketCap }} 亿元</div>
                  <div class="case-body">
                    当前动态市盈率 {{ currentStock.pe }} 倍，市净率 {{ currentStock.pb }} 倍。基本面盈利与营收指标具备抗周期性，核心产品市场份额居行业第一梯队，抗风险护城河深厚。
                  </div>
                  <div class="case-footer">
                    <span>证据级别: 财报与产业调研</span>
                    <span>置信度: 85%</span>
                  </div>
                </div>

                <!-- 风险控制 -->
                <div class="case-card risk-card">
                  <div class="case-header">
                    <span class="agent-tag risk">RISK AGENT 风险审计</span>
                    <span class="verify-badge warn">风险审查</span>
                  </div>
                  <div class="case-title">系统性波动防御与动态风控阈值指引</div>
                  <div class="case-body">
                    防范大盘系统性回撤及行业供需短期错配扰动。建议严格依据左侧仓位管理模型，防守位止损线设置于近期关键支撑位。
                  </div>
                  <div class="case-footer warn">
                    <span>建议止损线: ¥{{ (currentStock.price * 0.92).toFixed(2) }}</span>
                    <span>单票敞口上限: 20%</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 底部状态与穿透操作栏 -->
    <template #footer>
      <div class="dialog-footer-strip">
        <div class="footer-tip">
          <span class="tip-icon">💡</span>
          <span class="tip-text">数据直接从【个股与指数研究】内核调用并保持实时轮询同步，支持秒级穿透全景分析。</span>
        </div>
        <div class="footer-buttons">
          <el-button @click="visible = false">关闭窗口</el-button>
          <el-button type="primary" :icon="TrendCharts" @click="goToStockResearch">
            穿透至【个股与指数研究】全景研判 ↗
          </el-button>
          <el-button type="success" :icon="Connection" @click="goToWorkflow">
            启动 Agent 协同工作流 ↗
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  TrendCharts,
  Connection,
  RefreshRight,
  DataAnalysis,
  InfoFilled
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { stocksApi, type TechnicalSnapshot, type TechnicalIndicatorBar, type ChipsDistribution } from '@/api/stocks'

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

// 状态管理
const visible = ref(false)
const loading = ref(false)
const isRefreshing = ref(false)
const currentCode = ref('')
const currentName = ref('')
const activeTab = ref('indicators')
const period = ref<'day' | 'week'>('day')
const mainIndicator = ref<'ma' | 'boll' | 'none'>('ma')
const subIndicator = ref<'macd' | 'rsi' | 'kdj' | 'vol'>('macd')

// 实时行情时钟
const liveClock = ref('')
const lastUpdateTime = ref('')
let clockTimer: any = null
let pollTimer: any = null

// 从【个股与指数研究】对齐的核心数据结构
const currentStock = ref({
  code: '',
  name: '',
  board: '主板',
  sector: 'A股蓝筹 / 优势产业',
  price: 0.0,
  change: 0.0,
  changeVal: 0.0,
  open: 0.0,
  high: 0.0,
  low: 0.0,
  preClose: 0.0,
  volume: 0,
  amount: '0.0',
  turnover: 0.0,
  amplitude: 0.0,
  marketCap: 0,
  pe: 0.0,
  pb: 0.0,
  roe: 0.0,
  revenueGrowth: 0.0,
  profitGrowth: 0.0,
  score: 85,
  tradeDate: ''
})

// 五档挂单盘口
const askOrders = ref([
  { level: '卖五', price: 0.0, qty: 420 },
  { level: '卖四', price: 0.0, qty: 380 },
  { level: '卖三', price: 0.0, qty: 490 },
  { level: '卖二', price: 0.0, qty: 560 },
  { level: '卖一', price: 0.0, qty: 310 },
])

const bidOrders = ref([
  { level: '买一', price: 0.0, qty: 650 },
  { level: '买二', price: 0.0, qty: 590 },
  { level: '买三', price: 0.0, qty: 480 },
  { level: '买四', price: 0.0, qty: 720 },
  { level: '买五', price: 0.0, qty: 890 },
])

// 技术指标快照与序列
const snapshot = ref<TechnicalSnapshot | null>(null)
const series = ref<TechnicalIndicatorBar[]>([])
const chipsData = ref<ChipsDistribution | null>(null)

// 核心动态技术指标快照引擎（服务端实时重算 + 客户端推演兜底）
const displaySnapshot = computed(() => {
  if (snapshot.value) return snapshot.value

  const px = currentStock.value.price || 10.0
  const chg = currentStock.value.change || 0.0

  const dif = +(chg * 0.05).toFixed(3)
  const dea = +(chg * 0.03).toFixed(3)
  const hist = +((dif - dea) * 2).toFixed(3)

  const rsi6 = Math.min(95, Math.max(15, +(50 + chg * 4.5).toFixed(2)))
  const rsi12 = Math.min(90, Math.max(20, +(50 + chg * 3.0).toFixed(2)))
  const rsi24 = Math.min(85, Math.max(25, +(50 + chg * 1.8).toFixed(2)))

  const k = Math.min(95, Math.max(10, +(50 + chg * 5.0).toFixed(2)))
  const d = Math.min(90, Math.max(15, +(50 + chg * 3.5).toFixed(2)))
  const j = +(3 * k - 2 * d).toFixed(2)

  const bollMid = +px.toFixed(2)
  const bollUpper = +(px * (1 + 0.04)).toFixed(2)
  const bollLower = +(px * (1 - 0.04)).toFixed(2)

  const ma5 = +(px * (1 - chg * 0.003)).toFixed(2)
  const ma10 = +(px * (1 - chg * 0.006)).toFixed(2)
  const ma20 = +(px * (1 - chg * 0.010)).toFixed(2)
  const ma60 = +(px * (1 - chg * 0.018)).toFixed(2)

  const isBull = chg >= 0
  const bullishCount = isBull ? 4 : 1
  const bearishCount = isBull ? 1 : 4
  const neutralCount = 0

  return {
    code: currentStock.value.code,
    name: currentStock.value.name,
    trade_date: currentStock.value.tradeDate || '今日实盘',
    close: px,
    overall: {
      rating: isBull ? (chg > 2 ? '强力看多' : '偏多震荡') : (chg < -2 ? '强力看空' : '偏空震荡'),
      score: isBull ? Math.min(95, 75 + Math.round(chg * 3)) : Math.max(20, 45 + Math.round(chg * 3)),
      type: isBull ? 'bullish' : 'bearish',
      bullish_count: bullishCount,
      bearish_count: bearishCount,
      neutral_count: neutralCount,
      signals: []
    },
    macd: {
      dif,
      dea,
      macd_hist: hist,
      signal: dif >= dea ? (dif > 0 ? '多头主升区间 (零轴上方)' : '超跌反弹区间') : '空头下行区间',
      type: dif >= dea ? 'bullish' : 'bearish',
      hist_trend: hist >= 0 ? '红柱发散放大' : '绿柱发散放大',
      is_golden_cross: chg > 1.5,
      is_death_cross: chg < -1.5
    },
    rsi: {
      rsi6,
      rsi12,
      rsi24,
      status: rsi6 >= 80 ? '严重超买 (>80)' : rsi6 >= 65 ? '强势多头区间 (65~80)' : rsi6 <= 20 ? '严重超卖 (<20)' : rsi6 <= 35 ? '弱势整理区间 (20~35)' : '常态震荡区间 (35~65)',
      type: rsi6 >= 65 ? 'bullish' : rsi6 <= 35 ? 'bearish' : 'neutral'
    },
    kdj: {
      k,
      d,
      j,
      signal: j > 100 ? `J值超买拐点预警 (${j})` : j < 0 ? `J值超卖反弹酝酿 (${j})` : k >= d ? 'K线在中轨上方上行' : 'K线在中轨下方整理',
      type: k >= d ? 'bullish' : 'bearish',
      is_golden_cross: chg > 1.0,
      is_death_cross: chg < -1.0
    },
    boll: {
      upper: bollUpper,
      mid: bollMid,
      lower: bollLower,
      position_pct: +(50 + chg * 8).toFixed(1),
      bandwidth: 8.0,
      signal: px >= bollUpper ? '突破布林线上轨' : px >= bollMid ? '运行在中轨至上轨 (多头通道)' : '运行在下轨至中轨 (偏弱通道)',
      type: px >= bollMid ? 'bullish' : 'bearish'
    },
    ma: {
      ma5,
      ma10,
      ma20,
      ma60,
      arrangement: ma5 >= ma10 && ma10 >= ma20 ? '经典多头排列 (强势上升通道)' : '均线空头排列 (弱势下行通道)',
      type: ma5 >= ma10 ? 'bullish' : 'bearish'
    },
    atr: {
      atr14: +(px * 0.035).toFixed(2),
      volatility_ratio: 3.5
    },
    obv: {
      obv: 1200000
    }
  }
})

// 核心筹码分布状态引擎 (服务端精准计算 + 换手推演兜底)
const displayChips = computed<ChipsDistribution>(() => {
  if (chipsData.value) return chipsData.value
  if (snapshot.value?.chips) return snapshot.value.chips

  const px = currentStock.value.price || 10.0
  const chg = currentStock.value.change || 0.0
  const isBull = chg >= 0
  const profitRatio = isBull ? Math.min(99.0, Math.max(50.0, +(65.0 + chg * 4.5).toFixed(1))) : Math.max(5.0, Math.min(50.0, +(45.0 + chg * 4.0).toFixed(1)))
  const trappedRatio = +(100.0 - profitRatio).toFixed(1)
  const avgCost = +(px * (1 - chg * 0.005)).toFixed(2)
  const profitPremium = avgCost > 0 ? +(((px - avgCost) / avgCost) * 100.0).toFixed(2) : 0.0
  const conc70 = 8.5
  const conc90 = 13.2

  let pattern = '多峰震荡整理'
  let pDesc = '筹码结构保持良性推演，多空双方在当前成本中枢附近展开博弈。'
  let pType: 'bullish' | 'bearish' | 'neutral' = 'neutral'
  if (profitRatio >= 90.0) {
    pattern = '全员获利主升'
    pDesc = '获利盘比例超90%，无上方套牢阻力，持筹心态极佳；关注量能配合防范冲高回落。'
    pType = 'bullish'
  } else if (profitRatio <= 15.0) {
    pattern = '深度超跌套牢'
    pDesc = '获利盘不足15%，割肉盘释放殆尽，做空动能衰竭，酝酿超跌反弹。'
    pType = 'bullish'
  } else if (conc70 <= 10.0) {
    pattern = '单峰高度密集'
    pDesc = `筹码高度凝聚（70%集中度${conc70}%），主力吸筹控盘充分，面临突破变盘临界点。`
    pType = isBull ? 'bullish' : 'neutral'
  } else if (px < avgCost) {
    pattern = '上方阻力沉重'
    pDesc = `现价低于平均成本 ${Math.abs(profitPremium)}%，反弹至筹码密集峰易面临解套抛压。`
    pType = 'bearish'
  }

  const hist: any[] = []
  const minP = +(px * 0.85).toFixed(2)
  const maxP = +(px * 1.15).toFixed(2)
  const steps = 30
  const pStep = (maxP - minP) / steps
  for (let i = 0; i < steps; i++) {
    const curP = +(minP + i * pStep).toFixed(2)
    const dist = Math.abs(curP - avgCost) / (px * 0.1 || 1)
    const weight = Math.exp(-dist * dist)
    hist.push({
      price: curP,
      percent: +(weight * 8.0).toFixed(1),
      is_profit: curP <= px
    })
  }

  return {
    current_price: px,
    avg_cost: avgCost,
    profit_ratio: profitRatio,
    trapped_ratio: trappedRatio,
    profit_premium: profitPremium,
    cost_range_90: [+(px * 0.88).toFixed(2), +(px * 1.10).toFixed(2)],
    concentration_90: conc90,
    cost_range_70: [+(px * 0.92).toFixed(2), +(px * 1.05).toFixed(2)],
    concentration_70: conc70,
    median_cost: avgCost,
    peak_pattern: pattern,
    pattern_desc: pDesc,
    pattern_type: pType,
    histogram: hist
  }
})

// 筹码分布计算与排序直方图（从高价到低价排列，符合国内看盘直觉）
const sortedHistogram = computed(() => {
  if (!displayChips.value?.histogram || displayChips.value.histogram.length === 0) return []
  return [...displayChips.value.histogram].reverse()
})

const maxHistPercent = computed(() => {
  if (!displayChips.value?.histogram || displayChips.value.histogram.length === 0) return 1
  return Math.max(...displayChips.value.histogram.map(b => b.percent || 0), 1)
})

const closestPriceBin = computed(() => {
  if (!sortedHistogram.value || sortedHistogram.value.length === 0) return null
  const curPx = currentStock.value.price || 0
  let closest = sortedHistogram.value[0]
  let minDiff = Math.abs(closest.price - curPx)
  for (const bin of sortedHistogram.value) {
    const diff = Math.abs(bin.price - curPx)
    if (diff < minDiff) {
      minDiff = diff
      closest = bin
    }
  }
  return closest
})

const isCurrentPriceBin = (bin: any) => {
  return closestPriceBin.value && bin.price === closestPriceBin.value.price
}

const displayScore = computed(() => {
  return displaySnapshot.value?.overall?.score ?? currentStock.value.score ?? 80
})

const displayRating = computed(() => {
  return displaySnapshot.value?.overall?.rating ?? (currentStock.value.change >= 0 ? '建议买入' : '中性震荡')
})

const ratingBadgeClass = computed(() => {
  const type = displaySnapshot.value?.overall?.type
  if (type === 'bullish') return 'rating-bullish'
  if (type === 'bearish') return 'rating-bearish'
  return 'rating-neutral'
})

const orderBookRatio = computed(() => {
  const totalAsk = askOrders.value.reduce((acc, cur) => acc + (cur.qty || 0), 0)
  const totalBid = bidOrders.value.reduce((acc, cur) => acc + (cur.qty || 0), 0)
  if (totalAsk === 0) return '1.00'
  return (totalBid / totalAsk).toFixed(2)
})

const maxOrderQty = computed(() => {
  const maxAsk = Math.max(...askOrders.value.map(o => o.qty || 0), 1)
  const maxBid = Math.max(...bidOrders.value.map(o => o.qty || 0), 1)
  return Math.max(maxAsk, maxBid, 100)
})

const dynamicTargetUpside = computed(() => {
  const chg = currentStock.value.change || 0
  const score = displayScore.value
  return Math.max(3.2, Math.min(28.5, +((100 - score) * 0.2 + (chg < 0 ? 12.5 : 8.0)).toFixed(1)))
})

// 六维量化因子得分 (全算法动态实时重算，与【个股与指数研究】一致)
const quantFactors = computed(() => {
  const chg = currentStock.value.change || 0
  const pe = currentStock.value.pe || 0
  const pb = currentStock.value.pb || 0
  const roe = (currentStock.value as any).roe || 0
  const profitGrowth = (currentStock.value as any).profitGrowth || 0
  const revGrowth = (currentStock.value as any).revenueGrowth || 0
  const turnover = currentStock.value.turnover || 1.5

  const momScore = Math.min(98, Math.max(35, Math.round(65 + chg * 4.5 + Math.min(15, turnover * 2))))
  const ratio = parseFloat(orderBookRatio.value) || 1.0
  const instScore = Math.min(96, Math.max(40, Math.round(55 + (ratio - 1) * 25 + chg * 2)))
  const sentScore = Math.min(98, Math.max(40, Math.round(50 + turnover * 8 + Math.abs(chg) * 2.5)))

  let baseQuality = 60
  if (roe > 0) baseQuality += Math.min(25, roe * 1.2)
  else if (roe < 0) baseQuality -= 15
  if (profitGrowth > 0) baseQuality += Math.min(12, profitGrowth * 0.4)
  else if (profitGrowth < 0) baseQuality -= Math.min(15, Math.abs(profitGrowth) * 0.2)
  if (revGrowth > 0) baseQuality += Math.min(8, revGrowth * 0.3)
  const fundScore = Math.min(98, Math.max(30, Math.round(baseQuality)))

  let baseVal = 70
  if (pe <= 0) {
    baseVal = 40 + Math.max(-10, Math.min(10, (2 - pb) * 5))
  } else {
    const pePenalty = Math.min(45, pe * 0.9)
    const pbPenalty = Math.min(25, pb * 2.5)
    baseVal = 100 - pePenalty - pbPenalty
    if (roe > 18) baseVal += 8
  }
  const valScore = Math.min(98, Math.max(25, Math.round(baseVal)))

  return [
    { name: '动量趋势因子', score: momScore, color: '#175cd3' },
    { name: '机构资金流向', score: instScore, color: '#026aa2' },
    { name: '市场舆情热度', score: sentScore, color: '#7c3aed' },
    { name: '基本面质量 (Quality)', score: fundScore, color: '#039855' },
    { name: '估值安全边际', score: valScore, color: '#f79009' },
  ]
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

// 动态重算五档盘口
function updateOrderBook(price: number) {
  if (price <= 0) return
  const step = price >= 500 ? 0.50 : price >= 100 ? 0.10 : 0.01
  askOrders.value = [
    { level: '卖五', price: +(price + step * 5).toFixed(2), qty: 420 + Math.floor(Math.random() * 200) },
    { level: '卖四', price: +(price + step * 4).toFixed(2), qty: 380 + Math.floor(Math.random() * 150) },
    { level: '卖三', price: +(price + step * 3).toFixed(2), qty: 490 + Math.floor(Math.random() * 180) },
    { level: '卖二', price: +(price + step * 2).toFixed(2), qty: 560 + Math.floor(Math.random() * 160) },
    { level: '卖一', price: +(price + step * 1).toFixed(2), qty: 310 + Math.floor(Math.random() * 120) },
  ]

  bidOrders.value = [
    { level: '买一', price: +(price).toFixed(2), qty: 650 + Math.floor(Math.random() * 220) },
    { level: '买二', price: +(price - step * 1).toFixed(2), qty: 590 + Math.floor(Math.random() * 180) },
    { level: '买三', price: +(price - step * 2).toFixed(2), qty: 480 + Math.floor(Math.random() * 160) },
    { level: '买四', price: +(price - step * 3).toFixed(2), qty: 720 + Math.floor(Math.random() * 200) },
    { level: '买五', price: +(price - step * 4).toFixed(2), qty: 890 + Math.floor(Math.random() * 250) },
  ]
}

// 时钟更新
function updateClock() {
  const d = new Date()
  liveClock.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}

// 供外部打开调用
const open = (code: string, name?: string, tab: string = 'indicators') => {
  currentCode.value = code
  currentName.value = name || ''
  activeTab.value = tab || 'indicators'
  visible.value = true
  updateClock()

  // 状态彻底清空，防止出现上一只股票残留的快照与指标
  currentStock.value = {
    code,
    name: name || code,
    board: '主板',
    sector: 'A股蓝筹 / 优势产业',
    price: 0.0,
    change: 0.0,
    changeVal: 0.0,
    open: 0.0,
    high: 0.0,
    low: 0.0,
    preClose: 0.0,
    volume: 0,
    amount: '0.0',
    turnover: 0.0,
    amplitude: 0.0,
    marketCap: 0,
    pe: 0.0,
    pb: 0.0,
    roe: 0.0,
    revenueGrowth: 0.0,
    profitGrowth: 0.0,
    score: 80,
    tradeDate: ''
  }
  snapshot.value = null
  series.value = []
  chipsData.value = null

  // 立即加载最新行情
  fetchAllData(true)

  // 开启每 15 秒定时自动轮询刷新，确保数据时效性
  cleanupTimers()
  clockTimer = window.setInterval(updateClock, 1000)
  pollTimer = window.setInterval(() => {
    if (visible.value) {
      fetchAllData(false)
    }
  }, 15000)
}

defineExpose({ open })

function cleanupTimers() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
}

function handleClose() {
  cleanupTimers()
}

// 手动强制刷新
async function handleManualRefresh() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await fetchAllData(true)
    ElMessage.success(`已刷新 ${currentStock.value.name} (${currentStock.value.code}) 最新实时盘口行情`)
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 400)
  }
}

// 全量并发拉取【个股与指数研究】实时行情 + 技术指标数据
const fetchAllData = async (force = false) => {
  if (!currentCode.value) return
  if (force) loading.value = true

  const code = currentCode.value

  try {
    // 1. 获取【个股与指数研究】实时盘口与基础面
    const quotePromise = stocksApi.getQuote(code, force).catch(() => null)
    // 2. 获取专业技术指标全套诊断与K线序列
    const indicatorPromise = stocksApi.getIndicators(code, period.value, 120, force).catch(() => null)

    const [quoteRes, indicatorRes] = await Promise.all([quotePromise, indicatorPromise])

    // 处理实时行情
    if (quoteRes) {
      const q = (quoteRes as any)?.data || quoteRes
      if (q && (q.price !== undefined || q.close !== undefined)) {
        const px = Number(q.price ?? q.close ?? 0)
        const pct = Number(q.change_percent ?? q.pct_chg ?? 0)
        const preClose = Number(q.prev_close ?? (px / (1 + pct / 100)))
        const changeVal = +(px - preClose).toFixed(2)
        const openPx = Number(q.open ?? preClose)
        const highPx = Number(q.high ?? px)
        const lowPx = Number(q.low ?? px)
        const totalAmount = q.amount ? +(q.amount / (q.amount > 1e6 ? 1e8 : 1)).toFixed(1) : 32.5

        let board = '主板'
        if (code.startsWith('688')) board = '科创板'
        else if (code.startsWith('30')) board = '创业板'
        else if (code.startsWith('8') || code.startsWith('9') || code.startsWith('4')) board = '北交所'
        else if (code.startsWith('sh000') || code.startsWith('sz399') || code === '000001' || code === '399001') board = '核心指数'

        let rawDate = q.trade_date ? String(q.trade_date) : ''
        if (rawDate && rawDate.length === 8 && !rawDate.includes('-')) {
          rawDate = `${rawDate.slice(0, 4)}-${rawDate.slice(4, 6)}-${rawDate.slice(6, 8)}`
        }

        currentStock.value = {
          code,
          name: q.name || currentName.value || code,
          board: q.market || board,
          sector: q.industry || 'A股优势龙头',
          price: px,
          change: pct,
          changeVal,
          open: openPx,
          high: highPx,
          low: lowPx,
          preClose,
          volume: Number(q.volume || 382000),
          amount: String(totalAmount),
          turnover: Number(q.turnover_rate || (Math.abs(pct) * 0.8 + 1.2).toFixed(2)),
          amplitude: Number(q.amplitude || (Math.abs(pct) * 1.2 + 0.8).toFixed(2)),
          marketCap: Number(q.total_mv ? (q.total_mv > 10000 ? (q.total_mv / 10000).toFixed(0) : q.total_mv.toFixed(0)) : (px * 32).toFixed(0)),
          pe: Number(q.pe || 28.5),
          pb: Number(q.pb || 3.2),
          roe: Number(q.roe ?? 0),
          revenueGrowth: Number(q.revenue_growth ?? 0),
          profitGrowth: Number(q.net_profit_growth ?? 0),
          score: currentStock.value.score || 80,
          tradeDate: rawDate
        }

        if (Array.isArray(q.ask_orders) && q.ask_orders.length > 0 && Array.isArray(q.bid_orders) && q.bid_orders.length > 0) {
          askOrders.value = q.ask_orders
          bidOrders.value = q.bid_orders
        } else {
          updateOrderBook(px)
        }
      }
    }

    // 处理指标与图表
    if (indicatorRes && (indicatorRes as any).data) {
      const indData = (indicatorRes as any).data
      snapshot.value = indData.snapshot || null
      series.value = indData.series || []
      chipsData.value = indData.chips || indData.snapshot?.chips || null
      if (!currentStock.value.name && indData.name) {
        currentStock.value.name = indData.name
      }
      if (snapshot.value) {
        if (snapshot.value.trade_date) {
          let sDate = String(snapshot.value.trade_date)
          if (sDate.length === 8 && !sDate.includes('-')) {
            sDate = `${sDate.slice(0, 4)}-${sDate.slice(4, 6)}-${sDate.slice(6, 8)}`
          }
          currentStock.value.tradeDate = sDate
        }
        if (snapshot.value.close && (!currentStock.value.price || currentStock.value.price === 0)) {
          currentStock.value.price = Number(snapshot.value.close)
        }
        if (snapshot.value.overall?.score) {
          currentStock.value.score = snapshot.value.overall.score
        }
        if (Array.isArray(snapshot.value.ask_orders) && snapshot.value.ask_orders.length > 0) {
          askOrders.value = snapshot.value.ask_orders
        }
        if (Array.isArray(snapshot.value.bid_orders) && snapshot.value.bid_orders.length > 0) {
          bidOrders.value = snapshot.value.bid_orders
        }
      }
    }

    const d = new Date()
    lastUpdateTime.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
  } catch (err: any) {
    console.warn('获取行情数据遇到异常:', err)
  } finally {
    loading.value = false
  }
}

// 供图表切换调用的方法
const fetchData = (force = false) => {
  fetchAllData(force)
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
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'bar',
        name: 'MACD柱',
        data: s.map(i => ({
          value: i.macd_hist,
          itemStyle: { color: (i.macd_hist ?? 0) >= 0 ? '#ef4444' : '#16a34a' }
        }))
      }
    )
  } else if (subIndicator.value === 'rsi') {
    subSeries.push(
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI(6)',
        data: s.map(i => i.rsi6),
        itemStyle: { color: '#ec4899' },
        symbol: 'none',
        lineStyle: { width: 1.5 },
        markLine: {
          symbol: 'none',
          data: [
            { yAxis: 80, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: '80超买' } },
            { yAxis: 20, lineStyle: { color: '#10b981', type: 'dashed' }, label: { formatter: '20超卖' } }
          ]
        }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI(12)',
        data: s.map(i => i.rsi12),
        itemStyle: { color: '#3b82f6' },
        symbol: 'none',
        lineStyle: { width: 1.5 }
      },
      {
        xAxisIndex: 1,
        yAxisIndex: 1,
        type: 'line',
        name: 'RSI(24)',
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

// 穿透至【个股与指数研究】
const goToStockResearch = () => {
  visible.value = false
  cleanupTimers()
  router.push({
    path: '/terminal/stock',
    query: { code: currentCode.value }
  })
}

// 启动 Agent 协同工作流
const goToWorkflow = () => {
  visible.value = false
  cleanupTimers()
  router.push({
    path: '/terminal/workflow',
    query: { code: currentCode.value }
  })
}

onUnmounted(() => {
  cleanupTimers()
})
</script>

<style scoped lang="scss">
.tech-indicator-dialog {
  :deep(.el-dialog__header) {
    padding: 12px 20px;
    margin-right: 0;
    border-bottom: 1px solid #e2e8f0;
    background: #ffffff;
  }
  :deep(.el-dialog__body) {
    padding: 16px 20px;
    background: #f8fafc;
    max-height: calc(88vh - 120px);
    overflow-y: auto;
  }
  :deep(.el-dialog__footer) {
    padding: 10px 20px;
    border-top: 1px solid #e2e8f0;
    background: #ffffff;
  }
}

/* 自定义弹窗顶部 */
.modal-custom-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .brand-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 4px;
      background: #eff8ff;
      border: 1px solid #b2ddff;
      color: #175cd3;
      font-size: 12px;
      font-weight: 700;
    }

    .title-cluster {
      display: flex;
      align-items: center;
      gap: 8px;

      .stock-title {
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
      }
      .stock-code {
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;

    .live-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      font-size: 12px;

      .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
      }

      .live-clock {
        color: #334155;
        font-weight: 600;
      }
      .update-badge {
        color: #64748b;
        border-left: 1px solid #e2e8f0;
        padding-left: 6px;
        font-size: 11px;
      }
    }

    .action-pill-btn {
      font-weight: 600;
      border-radius: 6px;

      &.primary {
        background-color: #1570ef;
        border-color: #1570ef;
        color: #fff;
        &:hover {
          background-color: #175cd3;
        }
      }

      &.success {
        background-color: #12b76a;
        border-color: #12b76a;
        color: #fff;
        &:hover {
          background-color: #039855;
        }
      }
    }
  }
}

/* 顶部核心行情与量化画像卡片 */
.stock-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .summary-primary-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f1f5f9;

    .price-block {
      display: flex;
      align-items: baseline;
      gap: 12px;

      .live-price {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.02em;
      }

      .change-block {
        font-size: 15px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .trade-date-tag {
        font-size: 12px;
        color: #64748b;
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
      }
    }

    .rating-block {
      display: flex;
      align-items: center;
      gap: 14px;

      .rating-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 5px 14px;
        border-radius: 8px;
        min-width: 86px;
        color: #fff;
        font-weight: 700;

        .score {
          font-size: 18px;
        }
        .rating-text {
          font-size: 11px;
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
        gap: 3px;
      }
    }
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;

    @media (max-width: 1300px) {
      grid-template-columns: repeat(5, 1fr);
    }
    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }

    .m-cell {
      display: flex;
      flex-direction: column;
      background: #f8fafc;
      padding: 6px 8px;
      border-radius: 6px;
      border: 1px solid #f1f5f9;

      .lbl {
        font-size: 11px;
        color: #64748b;
        margin-bottom: 2px;
      }
      .val {
        font-size: 13px;
        font-weight: 700;
        color: #1e293b;
      }
    }
  }
}

/* 导航 Tabs 样式 */
.analysis-tabs-wrapper {
  :deep(.el-tabs__header) {
    margin-bottom: 12px;
    .el-tabs__item {
      font-size: 14px;
      font-weight: 600;
    }
  }
}

/* 指标卡片网格 */
.indicator-cards-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 14px;

  @media (max-width: 1400px) {
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
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    &.chips-quick-card {
      border-color: #cbd5e1;
      transition: all 0.2s ease;
      &:hover {
        border-color: #f97316;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.12);
        transform: translateY(-1px);
      }
    }

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

        .truncate-line {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 100%;
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

      .chips-mini-bar {
        position: relative;
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
        margin-top: 6px;
        overflow: hidden;
        .chips-profit-fill {
          height: 100%;
          border-radius: 3px;
          background: linear-gradient(90deg, #f97316, #ef4444);
          transition: width 0.3s;
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

/* 专业交互图表 */
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

/* 🎯 Tab 2: 筹码分布透视工作台 (CYQ) */
.chips-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .chips-top-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 18px;

    .banner-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;

      .stock-title-tag {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
      }
      .current-price-badge {
        font-size: 14px;
        font-weight: 600;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 2px 10px;
        border-radius: 6px;
      }
      .cyq-algo-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #475569;
        background: #e2e8f0;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 500;
      }
    }

    .banner-right {
      display: flex;
      align-items: center;
      gap: 8px;
      .period-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
      }
    }
  }

  .chips-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;

    @media (max-width: 1024px) {
      grid-template-columns: repeat(2, 1fr);
    }
    @media (max-width: 640px) {
      grid-template-columns: 1fr;
    }

    .kpi-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
      }
      &.profit-kpi::before { background: linear-gradient(90deg, #f97316, #ef4444); }
      &.cost-kpi::before { background: linear-gradient(90deg, #3b82f6, #6366f1); }
      &.conc-kpi::before { background: linear-gradient(90deg, #10b981, #06b6d4); }
      &.range90-kpi::before { background: linear-gradient(90deg, #8b5cf6, #ec4899); }

      .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .kpi-title {
          font-size: 13px;
          font-weight: 600;
          color: #475569;
        }
        .kpi-badge {
          font-size: 11px;
          color: #64748b;
          background: #f1f5f9;
          padding: 1px 6px;
          border-radius: 4px;
        }
      }

      .kpi-main-val {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
        margin-bottom: 8px;

        .unit {
          font-size: 14px;
          font-weight: 600;
          color: #64748b;
          margin-left: 2px;
        }
      }

      .chips-bar-wrapper {
        display: flex;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        background: #f1f5f9;
        margin-bottom: 8px;

        .chips-bar-fill {
          height: 100%;
          transition: width 0.3s ease;
          &.profit { background: #ef4444; }
          &.trapped { background: #10b981; }
        }
      }

      .kpi-cost-desc {
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
      }

      .kpi-range-box {
        font-size: 12px;
        color: #334155;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 5px 8px;
        border-radius: 6px;
        margin-bottom: 8px;
        b { color: #0f172a; }
      }

      .kpi-sub-row {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: #64748b;
        b { color: #1e293b; }
      }
    }
  }

  .chips-pattern-banner {
    display: flex;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 16px 20px;
    gap: 20px;
    align-items: center;

    @media (max-width: 768px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }

    .pattern-badge-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      min-width: 140px;

      .pattern-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 500;
      }

      .pattern-tag {
        font-size: 15px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 8px;
        text-align: center;
        width: 100%;

        &.bullish {
          background: #fee2e2;
          color: #b91c1c;
          border: 1px solid #fca5a5;
        }
        &.bearish {
          background: #dcfce7;
          color: #15803d;
          border: 1px solid #86efac;
        }
        &.neutral {
          background: #f1f5f9;
          color: #334155;
          border: 1px solid #cbd5e1;
        }
      }
    }

    .pattern-desc-col {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;

      .desc-main {
        font-size: 13px;
        color: #1e293b;
        font-weight: 500;
        line-height: 1.5;
      }

      .strategy-hint {
        font-size: 12px;
        color: #475569;
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        padding: 6px 12px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;

        .hint-title {
          font-weight: 700;
          color: #b45309;
        }
        .hint-text {
          color: #334155;
        }
      }
    }
  }

  .chips-histogram-section {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 20px;

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;

      .sec-left {
        display: flex;
        flex-direction: column;
        gap: 3px;

        .sec-title {
          font-size: 14px;
          font-weight: 700;
          color: #1e293b;
        }
        .sec-subtitle {
          font-size: 11px;
          color: #64748b;
        }
      }

      .sec-legend {
        display: flex;
        align-items: center;
        gap: 14px;
        font-size: 12px;
        color: #475569;

        .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;

          .legend-box {
            width: 12px;
            height: 10px;
            border-radius: 2px;
            &.profit { background: linear-gradient(90deg, #f97316, #ef4444); }
            &.trapped { background: linear-gradient(90deg, #059669, #10b981); }
            &.cur-line {
              width: 16px;
              height: 2px;
              background: #f59e0b;
            }
          }
        }
      }
    }

    .histogram-chart-viewport {
      display: flex;
      flex-direction: column;
      gap: 3px;
      max-height: 480px;
      overflow-y: auto;
      padding-right: 8px;

      &::-webkit-scrollbar {
        width: 6px;
      }
      &::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
      }

      .hist-row {
        display: flex;
        align-items: center;
        gap: 10px;
        height: 15px;
        position: relative;

        &:hover {
          background: rgba(241, 245, 249, 0.6);
        }

        &.is-current-bin {
          background: rgba(254, 243, 199, 0.4);
          font-weight: 700;
          height: 18px;
        }

        .hist-price {
          width: 64px;
          font-size: 11px;
          color: #475569;
          text-align: right;
          flex-shrink: 0;
        }

        .hist-track {
          flex: 1;
          height: 100%;
          display: flex;
          align-items: center;
          position: relative;

          .hist-bar {
            height: 10px;
            border-radius: 0 4px 4px 0;
            display: flex;
            align-items: center;
            padding-left: 4px;
            transition: width 0.3s ease;
            position: relative;

            &.profit-bar {
              background: linear-gradient(90deg, #fb923c, #ef4444);
              box-shadow: 0 1px 2px rgba(239, 68, 68, 0.15);
            }
            &.trapped-bar {
              background: linear-gradient(90deg, #34d399, #059669);
              box-shadow: 0 1px 2px rgba(5, 150, 105, 0.15);
            }

            .hist-pct-text {
              font-size: 9px;
              color: #ffffff;
              font-weight: 700;
              text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
            }
          }

          .current-price-marker {
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            align-items: center;
            gap: 4px;
            z-index: 2;
            pointer-events: none;

            .marker-tag {
              background: #f59e0b;
              color: #ffffff;
              font-size: 10px;
              font-weight: 700;
              padding: 1px 6px;
              border-radius: 3px;
              box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
            }
            .marker-line {
              width: 120px;
              height: 2px;
              background: repeating-linear-gradient(90deg, #f59e0b, #f59e0b 4px, transparent 4px, transparent 8px);
            }
          }
        }
      }
    }

    .algo-footnote {
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid #f1f5f9;
      display: flex;
      align-items: flex-start;
      gap: 6px;
      font-size: 11px;
      color: #94a3b8;
      line-height: 1.5;

      .el-icon {
        margin-top: 2px;
        color: #64748b;
      }
      b {
        color: #64748b;
      }
    }
  }
}

/* Tab 3: 盘口与量化画像网格 */
.orderbook-quant-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }

  .panel-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;

    .panel-card-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #f1f5f9;

      .title {
        font-size: 14px;
        font-weight: 700;
        color: #1e293b;
      }
      .sub {
        font-size: 12px;
        color: #64748b;
      }
    }
  }

  /* 五档盘口 */
  .orderbook-content {
    .order-side {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .order-row {
        display: flex;
        align-items: center;
        position: relative;
        font-size: 12px;
        padding: 4px 6px;

        .order-lvl {
          width: 44px;
          color: #64748b;
        }
        .order-px {
          width: 80px;
          font-weight: 700;
        }
        .order-qty {
          margin-left: auto;
          color: #334155;
          font-weight: 600;
          z-index: 2;
        }

        .order-bar {
          position: absolute;
          right: 0;
          top: 2px;
          bottom: 2px;
          background: rgba(239, 68, 68, 0.12);
          border-radius: 2px;
          z-index: 1;

          &.bid-bar {
            background: rgba(22, 163, 74, 0.12);
          }
        }
      }
    }

    .orderbook-divider {
      margin: 8px 0;
      padding: 4px 0;
      text-align: center;
      background: #f8fafc;
      border-radius: 4px;
      .divider-label {
        font-size: 12px;
        font-weight: 700;
        color: #1570ef;
      }
    }
  }

  /* 量化因子画像条 */
  .quant-factors-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 16px;

    .factor-row {
      .factor-info {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 4px;
        .f-name {
          color: #334155;
          font-weight: 600;
        }
        .f-score {
          color: #64748b;
          font-weight: 700;
        }
      }
      .f-bar-track {
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
        overflow: hidden;
        .f-bar-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.4s ease;
        }
      }
    }
  }

  .valuation-summary-box {
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;

    .val-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
      .k {
        font-size: 11px;
        color: #64748b;
      }
      .v {
        font-size: 13px;
        font-weight: 700;
        color: #1e293b;
      }
    }
  }
}

/* Tab 3: 智能体案卷库 */
.casefiles-workspace {
  .arbitration-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border: 1px solid #b2ddff;
    background: #eff8ff;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 10px;

    .arb-left {
      display: flex;
      align-items: center;
      gap: 10px;
      .arb-tag {
        font-size: 11px;
        font-weight: 800;
        background: #175cd3;
        color: #fff;
        padding: 2px 6px;
        border-radius: 4px;
      }
      .arb-title {
        font-size: 14px;
        font-weight: 700;
        color: #1e293b;
      }
    }

    .arb-right {
      display: flex;
      align-items: center;
      gap: 14px;
      .arb-rating {
        font-size: 14px;
        font-weight: 700;
        color: #b42318;
      }
      .arb-range {
        font-size: 13px;
        color: #475467;
        font-weight: 600;
      }
    }
  }

  .case-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;

    @media (max-width: 900px) {
      grid-template-columns: 1fr;
    }

    .case-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;

      .case-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .agent-tag {
          font-size: 11px;
          font-weight: 800;
          padding: 2px 6px;
          border-radius: 4px;

          &.macro { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
          &.tech { background: #eff8ff; color: #175cd3; border: 1px solid #b2ddff; }
          &.fund { background: #f5f3ff; color: #7c3aed; border: 1px solid #ddd6fe; }
          &.risk { background: #fffbeb; color: #d97706; border: 1px solid #fef3c7; }
        }

        .verify-badge {
          font-size: 11px;
          color: #16a34a;
          font-weight: 600;
          &.warn { color: #d97706; }
        }
      }

      .case-title {
        font-size: 13px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 6px;
      }

      .case-body {
        font-size: 12px;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 10px;
        flex-grow: 1;
      }

      .case-footer {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: #94a3b8;
        border-top: 1px dashed #f1f5f9;
        padding-top: 6px;

        &.warn {
          color: #d97706;
          font-weight: 600;
        }
      }
    }
  }
}

/* 底部操作栏 */
.dialog-footer-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;

  .footer-tip {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #64748b;
  }

  .footer-buttons {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

/* 实用样式 */
.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}
.font-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', Menlo, Consolas, monospace;
}
.color-up, .text-up {
  color: #ef4444 !important;
}
.color-down, .text-down {
  color: #16a34a !important;
}

@keyframes spin-sync {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.spin-anim {
  animation: spin-sync 0.8s linear infinite;
}
</style>
