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
        <el-button size="small" type="primary" plain @click="loadPreset('000001', 'custom_rule')">
          🌟 平安银行 · 自定义多因子
        </el-button>
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
      <!-- 左栏：回测控制台 (380px) -->
      <aside class="bc-control-col">
        <el-card shadow="never" class="control-card">
          <div class="card-section-title">1. 选择回测策略</div>
          <el-select v-model="form.strategy_name" class="full-width" @change="onStrategyChange">
            <el-option label="🌟 自定义多指标组合策略 (Custom Rule)" value="custom_rule" />
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
            <!-- 自定义多指标组合策略参数 -->
            <template v-if="form.strategy_name === 'custom_rule'">
              <div class="custom-rule-container">
                <el-form-item label="多条件协同逻辑">
                  <el-radio-group v-model="strategyParams.condition_mode" size="small" class="full-width">
                    <el-radio-button value="and" style="width: 50%;">全部满足 (AND)</el-radio-button>
                    <el-radio-button value="or" style="width: 50%;">任一满足 (OR)</el-radio-button>
                  </el-radio-group>
                </el-form-item>

                <!-- 均线形态因子 -->
                <div class="factor-block">
                  <div class="factor-title">① 均线形态过滤</div>
                  <el-select v-model="strategyParams.ma_mode" class="full-width" size="small">
                    <el-option label="✕ 关闭均线过滤" value="none" />
                    <el-option label="✓ 均线金叉 (快线上穿慢线)" value="cross" />
                    <el-option label="✓ 均线多头排列 (快线 > 慢线)" value="bull" />
                    <el-option label="✓ 站上长期均线 (收盘价 > 慢线)" value="above_long" />
                  </el-select>
                  <el-row :gutter="8" v-if="strategyParams.ma_mode !== 'none'" style="margin-top: 6px;">
                    <el-col :span="12">
                      <div class="sub-label">快线 (日)</div>
                      <el-input-number v-model="strategyParams.ma_fast" :min="2" :max="60" size="small" class="full-width" />
                    </el-col>
                    <el-col :span="12">
                      <div class="sub-label">慢线 (日)</div>
                      <el-input-number v-model="strategyParams.ma_slow" :min="5" :max="250" size="small" class="full-width" />
                    </el-col>
                  </el-row>
                </div>

                <!-- 成交量能因子 -->
                <div class="factor-block">
                  <div class="factor-title">② 量能异动过滤</div>
                  <el-select v-model="strategyParams.volume_filter" class="full-width" size="small">
                    <el-option label="✕ 关闭量能过滤" value="none" />
                    <el-option label="✓ 放量异动 (当日量 > 5日均量 × 倍数)" value="vol_surge" />
                    <el-option label="✓ 连续温和放量 (连续2日放量)" value="vol_expand" />
                  </el-select>
                  <div v-if="strategyParams.volume_filter === 'vol_surge'" style="margin-top: 6px;">
                    <div class="sub-label">放量倍数阈值</div>
                    <el-input-number v-model="strategyParams.vol_ratio" :min="1.1" :max="5.0" :step="0.1" size="small" class="full-width" />
                  </div>
                </div>

                <!-- RSI 震荡因子 -->
                <div class="factor-block">
                  <div class="factor-title">③ RSI 动量震荡过滤</div>
                  <el-select v-model="strategyParams.rsi_filter" class="full-width" size="small">
                    <el-option label="✕ 关闭 RSI 过滤" value="none" />
                    <el-option label="✓ 超跌区间入场 (RSI < 阈值)" value="oversold" />
                    <el-option label="✓ 超跌反弹修复 (自超跌拐头向上)" value="rebound" />
                  </el-select>
                  <div v-if="strategyParams.rsi_filter !== 'none'" style="margin-top: 6px;">
                    <div class="sub-label">RSI 超跌阈值</div>
                    <el-input-number v-model="strategyParams.rsi_threshold" :min="15" :max="45" size="small" class="full-width" />
                  </div>
                </div>

                <!-- KDJ 动量因子 -->
                <div class="factor-block">
                  <div class="factor-title">④ KDJ 随机指标过滤</div>
                  <el-select v-model="strategyParams.kdj_filter" class="full-width" size="small">
                    <el-option label="✕ 关闭 KDJ 过滤" value="none" />
                    <el-option label="✓ 低位金叉 (K上穿D且D<40)" value="golden_cross" />
                    <el-option label="✓ J值极度超卖触底 (J < 10)" value="low_j" />
                  </el-select>
                </div>

                <!-- 通道突破因子 -->
                <div class="factor-block">
                  <div class="factor-title">⑤ 通道突破过滤</div>
                  <el-select v-model="strategyParams.breakout_filter" class="full-width" size="small">
                    <el-option label="✕ 关闭突破过滤" value="none" />
                    <el-option label="✓ 阶段新高突破" value="new_high" />
                  </el-select>
                  <div v-if="strategyParams.breakout_filter === 'new_high'" style="margin-top: 6px;">
                    <div class="sub-label">新高周期 (天)</div>
                    <el-input-number v-model="strategyParams.breakout_days" :min="5" :max="120" size="small" class="full-width" />
                  </div>
                </div>
              </div>
            </template>

            <!-- 双均线参数 -->
            <template v-else-if="form.strategy_name === 'dual_ma'">
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

          <!-- 4. 仓位与风控规则 -->
          <div class="card-section-title" style="margin-top: 14px;">4. 仓位与止盈止损风控</div>
          <el-form label-position="top" size="small">
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="硬止损比例 (%)">
                  <el-input-number
                    v-model="riskParams.stop_loss_pct"
                    :min="0"
                    :max="30"
                    :step="1"
                    placeholder="0不设置"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="动态止盈比例 (%)">
                  <el-input-number
                    v-model="riskParams.take_profit_pct"
                    :min="0"
                    :max="100"
                    :step="5"
                    placeholder="0不设置"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="最长持股 (日)">
                  <el-input-number
                    v-model="riskParams.max_holding_days"
                    :min="0"
                    :max="365"
                    :step="5"
                    placeholder="0不限制"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="单次仓位比例 (%)">
                  <el-input-number
                    v-model="riskParams.position_ratio"
                    :min="10"
                    :max="100"
                    :step="5"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <!-- 5. 交易摩擦与滑点深度自定义 -->
          <div class="card-section-title" style="margin-top: 14px;">5. 交易摩擦与滑点深度模型</div>
          <el-form label-position="top" size="small">
            <el-form-item label="费率预设方案">
              <el-radio-group v-model="frictionPreset" size="small" class="full-width" @change="onFrictionPresetChange">
                <el-radio-button value="a_share" style="width: 33.3%;">标准A股</el-radio-button>
                <el-radio-button value="etf" style="width: 33.3%;">场内ETF</el-radio-button>
                <el-radio-button value="custom" style="width: 33.4%;">自定义</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="撮合滑点模型">
              <el-select v-model="frictionParams.slippage_type" class="full-width" size="small" @change="onSlippageTypeChange">
                <el-option label="📊 百分比滑点 (固定比例基准)" value="percent" />
                <el-option label="🎯 固定点数价差 (如 ±0.02元)" value="fixed_points" />
                <el-option label="🌊 成交量冲击成本模型 (平方根动态冲击)" value="volume_impact" />
                <el-option label="⚡ 理论零滑点 (无损耗)" value="none" />
              </el-select>
            </el-form-item>

            <el-row :gutter="10" v-if="frictionParams.slippage_type !== 'none'">
              <el-col :span="24">
                <el-form-item :label="frictionParams.slippage_type === 'fixed_points' ? '每股滑点价差 (元)' : '基准滑点比例 (%)'">
                  <el-input-number
                    v-model="frictionParams.slippage_val"
                    :min="0"
                    :max="frictionParams.slippage_type === 'fixed_points' ? 5 : 5"
                    :step="frictionParams.slippage_type === 'fixed_points' ? 0.01 : 0.05"
                    :precision="3"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="双边佣金率 (‱万分之)">
                  <el-input-number
                    v-model="frictionParams.commission_wan"
                    :min="0"
                    :max="30"
                    :step="0.5"
                    :precision="2"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最低佣金门槛 (元)">
                  <el-input-number
                    v-model="frictionParams.min_commission"
                    :min="0"
                    :max="50"
                    :step="1"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="卖出印花税率 (%)">
                  <el-input-number
                    v-model="frictionParams.stamp_duty_pct"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    :precision="3"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="双边过户费率 (‱万分之)">
                  <el-input-number
                    v-model="frictionParams.transfer_fee_wan"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    :precision="3"
                    class="full-width"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <!-- A股交易摩擦硬性约束说明 -->
          <div class="friction-rules-box">
            <div class="fr-title">⚖️ A 股真实交易制度硬约束:</div>
            <ul class="fr-list">
              <li>严格 T+1 持仓限制（买入当日不可卖出）</li>
              <li>涨跌停板（主板10%/创科20%）封板无法撮合买入/卖出</li>
              <li>遵循 {{ frictionPreset === 'etf' ? 'ETF 基金' : frictionPreset === 'a_share' ? '标准 A 股' : '自定义' }} 摩擦撮合体系</li>
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

          <!-- 1.5 交易摩擦损耗与执行成本审计面板 -->
          <el-card shadow="never" class="friction-card" v-if="result.frictions">
            <div class="fc-header">
              <div class="fc-title-group">
                <span class="fc-title">💸 交易摩擦成本与滑点损耗审计 (Friction & Slippage Audit)</span>
                <el-tag size="small" type="danger" effect="plain" class="fc-badge">
                  总摩擦损耗: ¥{{ result.frictions.total_friction.toFixed(2) }} (占初始本金 {{ result.frictions.friction_ratio_pct }}%)
                </el-tag>
              </div>
              <div class="fc-tags">
                <el-tag size="small" effect="plain" type="info">佣金: {{ result.frictions.commission_desc }}</el-tag>
                <el-tag size="small" effect="plain" type="info">印花税: {{ result.frictions.stamp_duty_desc }}</el-tag>
                <el-tag size="small" effect="plain" type="warning">滑点模型: {{ result.frictions.slippage_model_desc }}</el-tag>
              </div>
            </div>
            <div class="fc-grid">
              <div class="fc-item">
                <span class="fc-label">券商佣金累计 (双边)</span>
                <span class="fc-val font-mono">¥{{ result.frictions.total_commission.toFixed(2) }}</span>
              </div>
              <div class="fc-item">
                <span class="fc-label">证券印花税累计 (单边)</span>
                <span class="fc-val font-mono">¥{{ result.frictions.total_stamp_duty.toFixed(2) }}</span>
              </div>
              <div class="fc-item">
                <span class="fc-label">证券过户费累计</span>
                <span class="fc-val font-mono">¥{{ result.frictions.total_transfer_fee.toFixed(2) }}</span>
              </div>
              <div class="fc-item highlight-slip">
                <span class="fc-label">滑点冲击损耗估算</span>
                <span class="fc-val font-mono text-fee">¥{{ result.frictions.total_slippage_cost.toFixed(2) }}</span>
              </div>
            </div>
          </el-card>

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
              <el-table-column prop="reason" label="触发动因" min-width="140">
                <template #default="{ row }">
                  <el-tag
                    size="small"
                    :type="row.reason?.includes('止损') ? 'danger' : row.reason?.includes('止盈') ? 'success' : row.reason?.includes('超时') ? 'warning' : 'info'"
                    effect="plain"
                  >
                    {{ row.reason || (row.action === 'BUY' ? '策略买入' : '策略卖出') }}
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

const riskParams = ref({
  stop_loss_pct: 8, // 8% 硬止损
  take_profit_pct: 20, // 20% 动态止盈
  max_holding_days: 0, // 0 不限制
  position_ratio: 95 // 95% 仓位
})

// 5. 交易摩擦与滑点深度参数
const frictionPreset = ref<'a_share' | 'etf' | 'custom'>('a_share')
const frictionParams = ref({
  slippage_type: 'percent',
  slippage_val: 0.1, // 0.1% 或 0.02元
  commission_wan: 2.5, // 万2.5
  min_commission: 5.0, // 5元起征
  stamp_duty_pct: 0.05, // 印花税0.05%
  transfer_fee_wan: 0.1 // 过户费万0.1
})

function onFrictionPresetChange() {
  if (frictionPreset.value === 'a_share') {
    frictionParams.value.slippage_type = 'percent'
    frictionParams.value.slippage_val = 0.1
    frictionParams.value.commission_wan = 2.5
    frictionParams.value.min_commission = 5.0
    frictionParams.value.stamp_duty_pct = 0.05
    frictionParams.value.transfer_fee_wan = 0.1
  } else if (frictionPreset.value === 'etf') {
    frictionParams.value.slippage_type = 'percent'
    frictionParams.value.slippage_val = 0.05
    frictionParams.value.commission_wan = 1.0
    frictionParams.value.min_commission = 0.0
    frictionParams.value.stamp_duty_pct = 0.0
    frictionParams.value.transfer_fee_wan = 0.0
  }
}

function onSlippageTypeChange() {
  if (frictionParams.value.slippage_type === 'fixed_points') {
    frictionParams.value.slippage_val = 0.02
  } else if (frictionParams.value.slippage_type === 'none') {
    frictionParams.value.slippage_val = 0.0
  } else {
    frictionParams.value.slippage_val = 0.1
  }
}

const strategyParams = ref<Record<string, any>>({
  // 双均线
  fast_period: 5,
  slow_period: 20,
  // MACD
  fast: 12,
  slow: 26,
  signal: 9,
  // 布林带
  window: 20,
  num_std: 2.0,
  // 自定义多指标组合
  condition_mode: 'and',
  ma_mode: 'cross',
  ma_fast: 5,
  ma_slow: 20,
  volume_filter: 'vol_surge',
  vol_ratio: 1.5,
  rsi_filter: 'none',
  rsi_threshold: 30,
  kdj_filter: 'none',
  breakout_filter: 'none',
  breakout_days: 20
})

const currentStrategyDesc = computed(() => {
  switch (form.value.strategy_name) {
    case 'custom_rule':
      return '自主搭积木式组合策略：自由组合均线形态、成交量倍增、RSI超跌反转、KDJ低位金叉及通道新高突破，支持全满足(AND)或任一满足(OR)多因子入场，配合严格止损止盈风控。'
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
    const combinedParams = {
      ...strategyParams.value,
      stop_loss_pct: riskParams.value.stop_loss_pct > 0 ? riskParams.value.stop_loss_pct / 100 : 0,
      take_profit_pct: riskParams.value.take_profit_pct > 0 ? riskParams.value.take_profit_pct / 100 : 0,
      max_holding_days: riskParams.value.max_holding_days || 0,
      position_ratio: (riskParams.value.position_ratio || 95) / 100
    }

    const slippageReal = frictionParams.value.slippage_type === 'fixed_points'
      ? frictionParams.value.slippage_val
      : (frictionParams.value.slippage_val / 100)

    const res = await quantApi.runBacktest({
      symbol: form.value.symbol,
      strategy_name: form.value.strategy_name,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      initial_capital: form.value.initial_capital,
      commission_rate: frictionParams.value.commission_wan / 10000,
      min_commission: frictionParams.value.min_commission,
      stamp_duty_rate: frictionParams.value.stamp_duty_pct / 100,
      transfer_fee_rate: frictionParams.value.transfer_fee_wan / 10000,
      slippage: slippageReal,
      slippage_type: frictionParams.value.slippage_type,
      position_ratio: (riskParams.value.position_ratio || 95) / 100,
      strategy_params: combinedParams
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

  const navList = result.value.daily_nav || (result.value as any).equity_curve || []
  const dates = navList.map((d: any) => d.date)
  const navs = navList.map((d: any) => +(d.nav || 1.0).toFixed(3))
  const benchmarks = navList.map((d: any) => +(d.benchmark_nav || 1.0).toFixed(3))
  const drawdowns = navList.map((d: any) => -(d.drawdown_pct || 0).toFixed(2))

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
  grid-template-columns: 380px 1fr;
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

  .custom-rule-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }

  .factor-block {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 10px;

    .factor-title {
      font-size: 11px;
      font-weight: 700;
      color: #334155;
      margin-bottom: 6px;
    }

    .sub-label {
      font-size: 10px;
      color: #64748b;
      margin-bottom: 2px;
    }
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

.friction-card {
  background: #ffffff;
  border: 1px solid #fed7aa;
  background: linear-gradient(180deg, #fffaf5 0%, #ffffff 100%);

  .fc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;

    .fc-title-group {
      display: flex;
      align-items: center;
      gap: 10px;

      .fc-title {
        font-size: 13px;
        font-weight: 700;
        color: #9a3412;
      }
      .fc-badge {
        font-weight: 700;
      }
    }

    .fc-tags {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
  }

  .fc-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;

    .fc-item {
      background: #ffffff;
      border: 1px solid #fed7aa;
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .fc-label {
        font-size: 11px;
        color: #78716c;
      }
      .fc-val {
        font-size: 16px;
        font-weight: 700;
        color: #1c1917;
      }

      &.highlight-slip {
        border-color: #fca5a5;
        background: #fef2f2;
        .fc-val {
          color: #dc2626;
        }
      }
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
