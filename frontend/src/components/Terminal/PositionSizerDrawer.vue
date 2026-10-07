<template>
  <el-drawer
    v-model="visible"
    title="📐 海龟 ATR 仓位管理与半凯利风险预算"
    size="520px"
    :destroy-on-close="false"
    class="position-sizer-drawer"
  >
    <div class="sizer-container">
      <!-- 标的信息条 -->
      <div class="stock-banner">
        <div class="sb-left">
          <span class="sb-name">{{ stockName || '标的资产' }}</span>
          <span class="sb-code font-mono">{{ stockCode }}</span>
        </div>
        <div class="sb-right">
          <span class="sb-label">参考现价:</span>
          <span class="sb-price font-mono tabular-nums">¥{{ (currentPrice || 10).toFixed(2) }}</span>
        </div>
      </div>

      <!-- 参数配置卡片 -->
      <el-card shadow="never" class="config-card">
        <div class="card-title">1. 核心风险预算参数</div>
        <el-form label-position="top" size="small" class="sizer-form">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="账户总本金 (元)">
                <el-input-number
                  v-model="form.accountEquity"
                  :min="10000"
                  :max="100000000"
                  :step="10000"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="单笔最大风险容忍 (%)">
                <el-input-number
                  v-model="form.riskTolerancePct"
                  :min="0.2"
                  :max="5.0"
                  :step="0.2"
                  :precision="1"
                  class="full-width"
                />
                <span class="form-hint">单笔止损最多亏损账户总资金比例</span>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="ATR 止损倍数 (N 倍波动)">
                <el-input-number
                  v-model="form.atrMultiplier"
                  :min="1.0"
                  :max="4.0"
                  :step="0.5"
                  :precision="1"
                  class="full-width"
                />
                <span class="form-hint">海龟交易法推荐 2.0 倍 ATR</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="ATR 计算周期 (天)">
                <el-input-number
                  v-model="form.atrPeriod"
                  :min="5"
                  :max="30"
                  :step="1"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="card-title" style="margin-top: 16px;">2. 策略胜率与凯利公式 (0.5 Kelly)</div>
        <el-form label-position="top" size="small">
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="预期策略胜率 (%)">
                <el-input-number
                  v-model="form.winRate"
                  :min="30"
                  :max="90"
                  :step="5"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预期盈亏比 (盈利:亏损)">
                <el-input-number
                  v-model="form.payoffRatio"
                  :min="1.0"
                  :max="5.0"
                  :step="0.2"
                  :precision="1"
                  class="full-width"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="calc-btn-row">
          <el-button type="primary" :loading="calculating" @click="runCalculation" class="full-width-btn">
            ⚡ 立即执行量化头寸科学测算
          </el-button>
        </div>
      </el-card>

      <!-- 测算结果展示面板 -->
      <div v-if="result" class="result-section">
        <div class="result-headline">
          <span class="hl-tag">严守 A 股 100 股整手交易规则</span>
          <span class="hl-atr">当前日线 ATR 波动值: ¥{{ result.atr_value.toFixed(2) }}</span>
        </div>

        <!-- 关键输出指标卡片矩阵 -->
        <div class="metrics-grid">
          <div class="metric-card primary">
            <span class="m-lbl">建议建仓手数 / 股数</span>
            <div class="m-val-row">
              <span class="m-val tabular-nums font-mono">{{ result.suggested_lots }} 手</span>
              <span class="m-sub">({{ result.suggested_shares }} 股)</span>
            </div>
            <span class="m-desc">根据真实波动科学防爆仓，严格向下整手取整</span>
          </div>

          <div class="metric-card">
            <span class="m-lbl">占用资金 / 仓位占比</span>
            <div class="m-val-row">
              <span class="m-val tabular-nums font-mono">¥{{ formatNumber(result.position_value) }}</span>
              <span class="m-sub highlight">({{ result.capital_ratio_pct }}%)</span>
            </div>
            <span class="m-desc">海龟风险预算下的建议头寸市值规模</span>
          </div>

          <div class="metric-card danger">
            <span class="m-lbl">严格技术止损参考价</span>
            <div class="m-val-row">
              <span class="m-val tabular-nums font-mono color-down">¥{{ result.stop_loss_price.toFixed(2) }}</span>
              <span class="m-sub color-down">({{ ((result.stop_loss_price - currentPrice) / currentPrice * 100).toFixed(1) }}%)</span>
            </div>
            <span class="m-desc">现价 - {{ form.atrMultiplier }} × ATR，破位须坚决离场</span>
          </div>

          <div class="metric-card">
            <span class="m-lbl">单笔最大预估亏损</span>
            <div class="m-val-row">
              <span class="m-val tabular-nums font-mono">¥{{ formatNumber(result.max_loss_amount) }}</span>
              <span class="m-sub">({{ result.risk_tolerance_pct }}% 本金)</span>
            </div>
            <span class="m-desc">即使触及止损线，本金损耗绝不超过承受红线</span>
          </div>
        </div>

        <!-- 半凯利公式对比提示 -->
        <div v-if="kellyResult" class="kelly-box">
          <div class="kb-header">
            <span class="kb-title">半凯利防爆仓建议仓位上限:</span>
            <span class="kb-pct font-mono tabular-nums">{{ kellyResult.suggested_fraction_pct }}%</span>
          </div>
          <p class="kb-desc">
            全凯利值为 {{ kellyResult.full_kelly_pct }}%，为防止金融市场肥尾极端黑天鹅，学术界与顶级量化机构一致推荐使用半凯利 (0.5 Kelly) 作为组合敞口硬约束。
          </p>
        </div>

        <!-- 联动操作区 -->
        <div class="action-footer">
          <el-button type="success" size="default" class="full-width-btn" @click="handleApplyToPaperTrade">
            🎮 将此测算结果 ({{ result.suggested_lots }}手 / ¥{{ currentPrice.toFixed(2) }}) 带入虚拟模拟盘下单
          </el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { quantApi, type AtrCalculateResponse, type KellyCalculateResponse } from '@/api/quant'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  stockCode: string
  stockName?: string
  currentPrice: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'applyOrder', order: { symbol: string; name: string; price: number; shares: number }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

const form = ref({
  accountEquity: 100000,
  riskTolerancePct: 1.0,
  atrMultiplier: 2.0,
  atrPeriod: 14,
  winRate: 55,
  payoffRatio: 2.0
})

const calculating = ref(false)
const result = ref<AtrCalculateResponse | null>(null)
const kellyResult = ref<KellyCalculateResponse | null>(null)

function formatNumber(num: number | undefined) {
  if (num === undefined || num === null) return '0.00'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function runCalculation() {
  if (!props.stockCode) {
    ElMessage.warning('标的代码为空，无法测算')
    return
  }
  calculating.value = true
  try {
    const [atrRes, kellyRes] = await Promise.all([
      quantApi.calculateAtr({
        symbol: props.stockCode,
        current_price: props.currentPrice || 10.0,
        account_equity: form.value.accountEquity,
        risk_tolerance_pct: form.value.riskTolerancePct,
        atr_multiplier: form.value.atrMultiplier,
        atr_period: form.value.atrPeriod
      }),
      quantApi.calculateKelly({
        win_rate: form.value.winRate / 100,
        payoff_ratio: form.value.payoffRatio,
        half_kelly: true
      })
    ])

    result.value = ((atrRes as any)?.data || atrRes) as AtrCalculateResponse
    kellyResult.value = ((kellyRes as any)?.data || kellyRes) as KellyCalculateResponse
    ElMessage.success('量化头寸科学测算完成')
  } catch (err: any) {
    console.error('测算失败:', err)
    ElMessage.error(err.message || '测算失败，请重试')
  } finally {
    calculating.value = false
  }
}

function handleApplyToPaperTrade() {
  if (!result.value) return
  emit('applyOrder', {
    symbol: props.stockCode,
    name: props.stockName || props.stockCode,
    price: props.currentPrice,
    shares: result.value.suggested_shares
  })
  visible.value = false
}

// 打开时若无结果自动跑一次
watch(
  () => props.modelValue,
  (val) => {
    if (val && !result.value && props.stockCode) {
      runCalculation()
    }
  }
)
</script>

<style scoped lang="scss">
.sizer-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stock-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f0f7ff;
  border-radius: 8px;
  border-left: 4px solid #1677ff;

  .sb-left {
    display: flex;
    align-items: baseline;
    gap: 8px;
    .sb-name {
      font-size: 16px;
      font-weight: 700;
      color: #1f2937;
    }
    .sb-code {
      font-size: 13px;
      color: #6b7280;
    }
  }

  .sb-right {
    display: flex;
    align-items: baseline;
    gap: 6px;
    .sb-label {
      font-size: 12px;
      color: #6b7280;
    }
    .sb-price {
      font-size: 18px;
      font-weight: 700;
      color: #1677ff;
    }
  }
}

.card-title {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sizer-form {
  .full-width {
    width: 100%;
  }
  .form-hint {
    font-size: 11px;
    color: #9ca3af;
    margin-top: 2px;
    display: block;
  }
}

.calc-btn-row {
  margin-top: 14px;
  .full-width-btn {
    width: 100%;
    font-weight: 600;
  }
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-headline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;

  .hl-tag {
    background: #eef2ff;
    color: #4f46e5;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
  }
  .hl-atr {
    color: #6b7280;
    font-weight: 500;
  }
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;

  .metric-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;

    &.primary {
      background: #f0fdf4;
      border-color: #bbf7d0;
      .m-val {
        color: #16a34a;
      }
    }

    &.danger {
      background: #fef2f2;
      border-color: #fecaca;
      .m-val {
        color: #dc2626;
      }
    }

    .m-lbl {
      font-size: 12px;
      color: #6b7280;
    }

    .m-val-row {
      display: flex;
      align-items: baseline;
      gap: 6px;
      .m-val {
        font-size: 20px;
        font-weight: 800;
      }
      .m-sub {
        font-size: 12px;
        color: #6b7280;
        &.highlight {
          color: #2563eb;
          font-weight: 600;
        }
      }
    }

    .m-desc {
      font-size: 11px;
      color: #9ca3af;
      margin-top: 2px;
    }
  }
}

.kelly-box {
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  border-radius: 8px;
  padding: 12px 14px;

  .kb-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .kb-title {
      font-size: 13px;
      font-weight: 700;
      color: #5b21b6;
    }
    .kb-pct {
      font-size: 16px;
      font-weight: 800;
      color: #7c3aed;
    }
  }

  .kb-desc {
    margin: 6px 0 0 0;
    font-size: 11px;
    color: #6d28d9;
    line-height: 1.5;
  }
}

.action-footer {
  margin-top: 8px;
  .full-width-btn {
    width: 100%;
    font-weight: 600;
  }
}

.color-down {
  color: #10b981;
}
</style>
