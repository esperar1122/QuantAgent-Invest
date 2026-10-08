<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? `修改回测策略：${form.name || ''}` : '新建自定义回测策略'"
    width="820px"
    destroy-on-close
    class="backtest-strategy-edit-dialog"
    append-to-body
  >
    <div class="dialog-tips-bar">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="回测策略支持标的组合、底层算法、指标阈值、风控止盈止损与摩擦模型的全参数持久化。您可以手动微调，或一键导入当前控制台正在运行的参数。"
      />
      <div class="tips-actions" v-if="currentContext">
        <el-button
          type="primary"
          plain
          size="small"
          @click="loadFromCurrentContext"
        >
          <el-icon><Download /></el-icon>
          从当前回测控制台快速提取配置
        </el-button>
        <el-button
          size="small"
          @click="resetToDefaults"
        >
          恢复标准模板
        </el-button>
      </div>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="strategy-form"
    >
      <!-- 1. 基础元信息 -->
      <div class="section-card">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          <span>策略基础信息</span>
        </div>
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="策略名称" prop="name" required>
              <el-input
                v-model="form.name"
                placeholder="例如：茅台MA双均线顺势波段、多标的放量突破"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="标识图标" prop="icon">
              <el-select v-model="form.icon" style="width: 100%">
                <el-option label="🎯 准心" value="🎯" />
                <el-option label="👑 皇冠核心" value="👑" />
                <el-option label="🌟 复合因子" value="🌟" />
                <el-option label="📈 均线趋势" value="📈" />
                <el-option label="🌊 动量波段" value="🌊" />
                <el-option label="⚡ 突破先锋" value="⚡" />
                <el-option label="💎 价值防守" value="💎" />
                <el-option label="🚀 高弹性" value="🚀" />
                <el-option label="🛡️ 严格风控" value="🛡️" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="标签展示色彩" prop="tag_type">
              <el-select v-model="form.tag_type" style="width: 100%">
                <el-option label="🔵 经典蓝" value="primary" />
                <el-option label="🟢 稳健绿" value="success" />
                <el-option label="🟡 价值金" value="warning" />
                <el-option label="🔴 强势红" value="danger" />
                <el-option label="⚪ 中性灰" value="info" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="投资逻辑与策略说明" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="2"
                placeholder="简要记录该策略的选股依据与回测假设，例如：针对大盘蓝筹，以金叉顺势建仓，辅以严苛5%止损保护资金。"
                maxlength="300"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 2. 回测标的与资金设置 -->
      <div class="section-card" style="margin-top: 14px">
        <div class="section-title">
          <el-icon><Coin /></el-icon>
          <span>回测标的与资金分配</span>
        </div>
        <el-row :gutter="14">
          <el-col :span="14">
            <el-form-item label="股票/ETF代码 (支持单标的或多标的逗号分隔)">
              <el-input
                v-model="form.config.symbol"
                placeholder="例如 600519，或 600519, 000001, 300750"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="多标的资金分配模型">
              <el-select v-model="form.config.sizing_model" style="width: 100%">
                <el-option label="⚖️ 等权重分配 (Equal Weight)" value="equal_weight" />
                <el-option label="📉 波动率倒数加权 (Inverse Vol)" value="inverse_volatility" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="初始回测本金 (元)">
              <el-input-number
                v-model="form.config.initial_capital"
                :min="10000"
                :max="100000000"
                :step="10000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="内核底层策略">
              <el-select v-model="form.config.strategy_name" style="width: 100%">
                <el-option label="🌟 自定义多指标组合策略 (Custom Rule)" value="custom_rule" />
                <el-option label="📈 双均线金叉死叉策略 (Dual MA)" value="dual_ma" />
                <el-option label="🌊 MACD 动量趋势策略 (MACD)" value="macd" />
                <el-option label="🎯 布林带均值回归策略 (Bollinger)" value="bollinger" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 3. 内核策略专用参数配置 -->
      <div class="section-card" style="margin-top: 14px">
        <div class="section-title">
          <el-icon><Operation /></el-icon>
          <span>策略指标超参数</span>
        </div>

        <!-- 自定义多指标组合 -->
        <template v-if="form.config.strategy_name === 'custom_rule'">
          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="多条件协同逻辑">
                <el-radio-group v-model="form.config.strategy_params.condition_mode" size="small">
                  <el-radio-button value="and">全部满足 (AND)</el-radio-button>
                  <el-radio-button value="or">任一满足 (OR)</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="均线形态过滤">
                <el-select v-model="form.config.strategy_params.ma_mode" size="small" style="width: 100%">
                  <el-option label="✕ 关闭均线过滤" value="none" />
                  <el-option label="✓ 均线金叉 (快线上穿慢线)" value="cross" />
                  <el-option label="✓ 均线多头排列 (快线 > 慢线)" value="bull" />
                  <el-option label="✓ 站上长期均线 (收盘价 > 慢线)" value="above_long" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="14" v-if="form.config.strategy_params.ma_mode !== 'none'">
            <el-col :span="12">
              <el-form-item label="快线周期 (日)">
                <el-input-number v-model="form.config.strategy_params.ma_fast" :min="2" :max="60" size="small" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="慢线周期 (日)">
                <el-input-number v-model="form.config.strategy_params.ma_slow" :min="5" :max="250" size="small" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="量能异动过滤">
                <el-select v-model="form.config.strategy_params.volume_filter" size="small" style="width: 100%">
                  <el-option label="✕ 关闭量能过滤" value="none" />
                  <el-option label="✓ 放量异动 (当日量 > 均量×倍数)" value="vol_surge" />
                  <el-option label="✓ 连续温和放量 (连续2日放量)" value="vol_expand" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="form.config.strategy_params.volume_filter === 'vol_surge'">
              <el-form-item label="放量倍数阈值">
                <el-input-number v-model="form.config.strategy_params.vol_ratio" :min="1.1" :max="5.0" :step="0.1" size="small" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="RSI 动量过滤">
                <el-select v-model="form.config.strategy_params.rsi_filter" size="small" style="width: 100%">
                  <el-option label="✕ 关闭 RSI 过滤" value="none" />
                  <el-option label="✓ 超跌区间入场 (RSI < 阈值)" value="oversold" />
                  <el-option label="✓ 超跌反弹修复 (自超跌拐头)" value="rebound" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="form.config.strategy_params.rsi_filter !== 'none'">
              <el-form-item label="RSI 阈值">
                <el-input-number v-model="form.config.strategy_params.rsi_threshold" :min="15" :max="45" size="small" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="KDJ 随机指标过滤">
                <el-select v-model="form.config.strategy_params.kdj_filter" size="small" style="width: 100%">
                  <el-option label="✕ 关闭 KDJ 过滤" value="none" />
                  <el-option label="✓ 低位金叉 (K上穿D且D<40)" value="golden_cross" />
                  <el-option label="✓ J值极度超卖触底 (J < 10)" value="low_j" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通道新高突破过滤">
                <el-select v-model="form.config.strategy_params.breakout_filter" size="small" style="width: 100%">
                  <el-option label="✕ 关闭突破过滤" value="none" />
                  <el-option label="✓ 阶段新高突破" value="new_high" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 双均线 -->
        <template v-else-if="form.config.strategy_name === 'dual_ma'">
          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="短期均线周期 (日)">
                <el-input-number v-model="form.config.strategy_params.fast_period" :min="2" :max="60" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="长期均线周期 (日)">
                <el-input-number v-model="form.config.strategy_params.slow_period" :min="5" :max="250" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- MACD -->
        <template v-else-if="form.config.strategy_name === 'macd'">
          <el-row :gutter="14">
            <el-col :span="8">
              <el-form-item label="快线周期 (12)">
                <el-input-number v-model="form.config.strategy_params.fast" :min="2" :max="30" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="慢线周期 (26)">
                <el-input-number v-model="form.config.strategy_params.slow" :min="10" :max="60" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="信号周期 (9)">
                <el-input-number v-model="form.config.strategy_params.signal" :min="2" :max="20" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <!-- 布林带 -->
        <template v-else-if="form.config.strategy_name === 'bollinger'">
          <el-row :gutter="14">
            <el-col :span="12">
              <el-form-item label="布林窗口 (日)">
                <el-input-number v-model="form.config.strategy_params.window" :min="5" :max="60" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="标准差倍数">
                <el-input-number v-model="form.config.strategy_params.num_std" :min="1.0" :max="3.5" :step="0.1" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </div>

      <!-- 4. 仓位与风控规则 -->
      <div class="section-card" style="margin-top: 14px">
        <div class="section-title">
          <el-icon><Lock /></el-icon>
          <span>仓位分配与止盈止损风控</span>
        </div>
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="硬止损比例 (%)">
              <el-input-number
                v-model="form.config.risk_params.stop_loss_pct"
                :min="0"
                :max="30"
                :step="1"
                placeholder="0不设置"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="动态止盈比例 (%)">
              <el-input-number
                v-model="form.config.risk_params.take_profit_pct"
                :min="0"
                :max="100"
                :step="5"
                placeholder="0不设置"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最长持仓天数 (日)">
              <el-input-number
                v-model="form.config.risk_params.max_holding_days"
                :min="0"
                :max="365"
                :step="5"
                placeholder="0不限制"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="单次仓位比例 (%)">
              <el-input-number
                v-model="form.config.risk_params.position_ratio"
                :min="10"
                :max="100"
                :step="5"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 5. 交易摩擦与滑点深度模型 -->
      <div class="section-card" style="margin-top: 14px">
        <div class="section-title">
          <el-icon><Money /></el-icon>
          <span>交易摩擦成本与滑点模型</span>
        </div>
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="费率预设体系">
              <el-select v-model="form.config.friction_params.friction_preset" @change="onFrictionPresetChange" style="width: 100%">
                <el-option label="标准 A 股体系 (万2.5佣金 + 万5印花税)" value="a_share" />
                <el-option label="场内 ETF 体系 (万1佣金 + 免印花税)" value="etf" />
                <el-option label="完全自定义费率" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="撮合滑点模型">
              <el-select v-model="form.config.friction_params.slippage_type" style="width: 100%">
                <el-option label="📊 百分比滑点 (固定比例)" value="percent" />
                <el-option label="🎯 固定点数价差 (如 ±0.02元)" value="fixed_points" />
                <el-option label="🌊 成交量冲击成本模型 (平方根动态)" value="volume_impact" />
                <el-option label="⚡ 理论零滑点 (无损耗)" value="none" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="form.config.friction_params.slippage_type !== 'none'">
            <el-form-item :label="form.config.friction_params.slippage_type === 'fixed_points' ? '每股滑点价差 (元)' : '基准滑点比例 (%)'">
              <el-input-number
                v-model="form.config.friction_params.slippage_val"
                :min="0"
                :max="5"
                :step="0.05"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="双边佣金率 (‱万分之)">
              <el-input-number
                v-model="form.config.friction_params.commission_wan"
                :min="0"
                :max="30"
                :step="0.5"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最低佣金门槛 (元)">
              <el-input-number
                v-model="form.config.friction_params.min_commission"
                :min="0"
                :max="50"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="卖出印花税率 (%)">
              <el-input-number
                v-model="form.config.friction_params.stamp_duty_pct"
                :min="0"
                :max="1"
                :step="0.01"
                :precision="3"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '确认创建策略' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { InfoFilled, Coin, Operation, Lock, Money, Download } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import type {
  CustomBacktestStrategy,
  CustomBacktestStrategyCreatePayload
} from '@/api/quant'

export interface StrategyEditFormConfig {
  symbol: string
  strategy_name: string
  sizing_model: string
  initial_capital: number
  strategy_params: Record<string, any>
  risk_params: {
    stop_loss_pct: number
    take_profit_pct: number
    max_holding_days: number
    position_ratio: number
  }
  friction_params: {
    friction_preset: string
    slippage_type: string
    slippage_val: number
    commission_wan: number
    min_commission: number
    stamp_duty_pct: number
    transfer_fee_wan: number
  }
}

const props = defineProps<{
  visible: boolean
  strategy?: CustomBacktestStrategy | null
  currentContext?: {
    form: {
      symbol: string
      strategy_name: string
      sizing_model: string
      initial_capital: number
    }
    strategyParams: Record<string, any>
    riskParams: Record<string, any>
    frictionParams: Record<string, any>
    frictionPreset: string
  } | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'save', payload: { isEdit: boolean; id?: string; data: CustomBacktestStrategyCreatePayload }): void
}>()

const formRef = ref<FormInstance>()
const saving = ref(false)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => !!props.strategy?.id)

const createDefaultConfig = (): StrategyEditFormConfig => ({
  symbol: '600519',
  strategy_name: 'custom_rule',
  sizing_model: 'equal_weight',
  initial_capital: 100000,
  strategy_params: {
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
    breakout_days: 20,
    fast_period: 5,
    slow_period: 20,
    fast: 12,
    slow: 26,
    signal: 9,
    window: 20,
    num_std: 2.0
  },
  risk_params: {
    stop_loss_pct: 5,
    take_profit_pct: 15,
    max_holding_days: 15,
    position_ratio: 95
  },
  friction_params: {
    friction_preset: 'a_share',
    slippage_type: 'percent',
    slippage_val: 0.1,
    commission_wan: 2.5,
    min_commission: 5,
    stamp_duty_pct: 0.05,
    transfer_fee_wan: 0.1
  }
})

const form = ref<{
  name: string
  description: string
  icon: string
  tag_type: string
  config: StrategyEditFormConfig
}>({
  name: '',
  description: '',
  icon: '🎯',
  tag_type: 'primary',
  config: createDefaultConfig()
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { max: 50, message: '名称不能超过50字', trigger: 'blur' }
  ]
}

// 监听策略数据载入
watch(
  () => props.strategy,
  (val) => {
    if (val) {
      const def = createDefaultConfig()
      form.value = {
        name: val.name || '',
        description: val.description || '',
        icon: val.icon || '🎯',
        tag_type: val.tag_type || 'primary',
        config: {
          symbol: val.config?.symbol || def.symbol,
          strategy_name: val.config?.strategy_name || def.strategy_name,
          sizing_model: val.config?.sizing_model || def.sizing_model,
          initial_capital: val.config?.initial_capital || def.initial_capital,
          strategy_params: { ...def.strategy_params, ...(val.config?.strategy_params || {}) },
          risk_params: { ...def.risk_params, ...(val.config?.risk_params || {}) },
          friction_params: { ...def.friction_params, ...(val.config?.friction_params || {}) }
        }
      }
    } else {
      resetToDefaults()
    }
  },
  { immediate: true }
)

function resetToDefaults() {
  form.value = {
    name: '',
    description: '',
    icon: '🎯',
    tag_type: 'primary',
    config: createDefaultConfig()
  }
}

// 从当前回测控制台快速提取配置
function loadFromCurrentContext() {
  if (!props.currentContext) return
  const ctx = props.currentContext

  form.value.config.symbol = ctx.form.symbol
  form.value.config.strategy_name = ctx.form.strategy_name
  form.value.config.sizing_model = ctx.form.sizing_model
  form.value.config.initial_capital = ctx.form.initial_capital

  form.value.config.strategy_params = {
    ...form.value.config.strategy_params,
    ...ctx.strategyParams
  }

  form.value.config.risk_params = {
    stop_loss_pct: ctx.riskParams.stop_loss_pct,
    take_profit_pct: ctx.riskParams.take_profit_pct,
    max_holding_days: ctx.riskParams.max_holding_days,
    position_ratio: ctx.riskParams.position_ratio
  }

  form.value.config.friction_params = {
    friction_preset: ctx.frictionPreset,
    slippage_type: ctx.frictionParams.slippage_type,
    slippage_val: ctx.frictionParams.slippage_val,
    commission_wan: ctx.frictionParams.commission_wan,
    min_commission: ctx.frictionParams.min_commission,
    stamp_duty_pct: ctx.frictionParams.stamp_duty_pct,
    transfer_fee_wan: ctx.frictionParams.transfer_fee_wan
  }

  if (!form.value.name) {
    const symBrief = ctx.form.symbol.length > 10 ? '标的组合' : ctx.form.symbol
    form.value.name = `${symBrief} 自定义回测策略`
  }

  ElMessage.success('已一键提取当前控制台的所有参数！')
}

function onFrictionPresetChange(val: string) {
  if (val === 'a_share') {
    form.value.config.friction_params.commission_wan = 2.5
    form.value.config.friction_params.min_commission = 5.0
    form.value.config.friction_params.stamp_duty_pct = 0.05
    form.value.config.friction_params.transfer_fee_wan = 0.1
    form.value.config.friction_params.slippage_val = 0.1
  } else if (val === 'etf') {
    form.value.config.friction_params.commission_wan = 1.0
    form.value.config.friction_params.min_commission = 5.0
    form.value.config.friction_params.stamp_duty_pct = 0.0
    form.value.config.friction_params.transfer_fee_wan = 0.1
    form.value.config.friction_params.slippage_val = 0.05
  }
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      emit('save', {
        isEdit: isEdit.value,
        id: props.strategy?.id,
        data: {
          name: form.value.name.trim(),
          description: form.value.description.trim(),
          icon: form.value.icon,
          tag_type: form.value.tag_type,
          config: JSON.parse(JSON.stringify(form.value.config))
        }
      })
      dialogVisible.value = false
    } finally {
      saving.value = false
    }
  })
}
</script>

<style scoped>
.dialog-tips-bar {
  margin-bottom: 14px;
}

.tips-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.strategy-form {
  max-height: 560px;
  overflow-y: auto;
  padding-right: 6px;
}

.section-card {
  padding: 14px 16px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}

.section-title .el-icon {
  color: var(--el-color-primary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
