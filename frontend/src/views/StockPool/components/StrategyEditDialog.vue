<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? `修改量化策略：${form.name || ''}` : '新建自定义量化选股策略'"
    width="780px"
    destroy-on-close
    class="strategy-edit-dialog"
    append-to-body
  >
    <div class="dialog-tips-bar">
      <el-alert
        v-if="isQuantCandidate"
        type="warning"
        :closable="false"
        show-icon
        title="⭐ 核心策略驱动提示：您正在自定义系统【量化初筛候选池】的筛选规则。此策略为全链路初筛基准源，修改后【市场总览】候选池标的统计及股票池初筛将立即同步生效。本策略为系统核心，不可删除，但支持自由修改所有指标参数。"
        style="margin-bottom: 10px"
      />
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="量化策略支持多因子自由组合与区间设定。您可以手动配置以下指标，或直接载入当前筛选池中的指标参数。"
      />
      <div class="tips-actions">
        <el-button
          v-if="currentParams"
          type="primary"
          plain
          size="small"
          @click="loadFromCurrentParams"
        >
          <el-icon><Download /></el-icon>
          从当前页面筛选条件快速提取
        </el-button>
        <el-button
          size="small"
          @click="resetFormToEmpty"
        >
          清空所有指标
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
      <!-- 基础元信息 -->
      <div class="section-card">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          <span>策略基础信息</span>
        </div>
        <el-row :gutter="16">
          <el-col :span="14">
            <el-form-item label="策略名称" prop="name" required>
              <el-input
                v-model="form.name"
                placeholder="例如：低估值高成长精选、突破放量先锋"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="标签展示色彩" prop="tag_type">
              <el-select v-model="form.tag_type" style="width: 100%">
                <el-option label="🔵 经典蓝 (Primary)" value="primary" />
                <el-option label="🟢 稳健绿 (Success)" value="success" />
                <el-option label="🟡 价值金 (Warning)" value="warning" />
                <el-option label="🔴 强势红 (Danger)" value="danger" />
                <el-option label="⚪ 中性灰 (Info)" value="info" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="投资逻辑与策略说明" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="2"
                placeholder="简要记录该策略的筛选选股逻辑，例如：结合合理估值与业绩增长，过滤流动性充沛的核心标的"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 多因子量化指标配置 -->
      <div class="section-card" style="margin-top: 14px">
        <div class="section-title">
          <el-icon><Operation /></el-icon>
          <span>多因子量化指标配置</span>
          <el-tag size="small" type="warning" class="active-indicator-pill">
            已配置 {{ configuredIndicatorCount }} 项因子约束
          </el-tag>
        </div>

        <el-tabs v-model="activeTab" class="indicator-tabs">
          <!-- 1. 估值因子 -->
          <el-tab-pane label="📊 估值因子" name="valuation">
            <div class="param-grid">
              <div class="param-item">
                <span class="param-label">市盈率 (PE):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_pe" :min="0" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_pe" :min="0" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">市净率 (PB):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_pb" :min="0" :precision="2" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_pb" :min="0" :precision="2" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">市销率 (PS):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_ps" :min="0" :precision="2" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_ps" :min="0" :precision="2" placeholder="Max" controls-position="right" />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 2. 行情与量能 -->
          <el-tab-pane label="⚡ 行情与流动性" name="market">
            <div class="param-grid">
              <div class="param-item">
                <span class="param-label">股价 (元):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_close" :min="0" :precision="2" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_close" :min="0" :precision="2" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">日涨跌幅 (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_pct_chg" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_pct_chg" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">换手率 (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_turnover_rate" :min="0" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_turnover_rate" :min="0" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">量比:</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_volume_ratio" :min="0" :precision="2" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_volume_ratio" :min="0" :precision="2" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">日最低成交额 (流动性门槛):</span>
                <div class="range-inputs">
                  <el-input-number
                    v-model="minAmountWan"
                    :min="0"
                    :precision="0"
                    :step="1000"
                    placeholder="例如 8000"
                    controls-position="right"
                    style="width: 100%"
                  />
                  <span class="range-sep" style="font-size: 12px; color: #64748b; margin-left: 6px">万元</span>
                </div>
              </div>
              <div class="param-item full-span">
                <span class="param-label">成交额活跃度分级:</span>
                <el-radio-group v-model="form.params.volume_level" size="small">
                  <el-radio-button label="">不限活跃度</el-radio-button>
                  <el-radio-button label="high">🔥 高活跃 (&gt;10亿元)</el-radio-button>
                  <el-radio-button label="medium">⚖️ 正常 (3-10亿元)</el-radio-button>
                  <el-radio-button label="low">❄️ 清淡 (&lt;3亿元)</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </el-tab-pane>

          <!-- 3. 财务与成长 -->
          <el-tab-pane label="🚀 财务与成长质量" name="growth">
            <div class="param-grid">
              <div class="param-item">
                <span class="param-label">净资产收益率 ROE (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_roe" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_roe" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">净利润同比增速 (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_net_profit_growth" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_net_profit_growth" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">营收同比增速 (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_revenue_growth" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_revenue_growth" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item">
                <span class="param-label">销售毛利率 (%):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_gross_margin" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_gross_margin" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 4. 市值与板块 -->
          <el-tab-pane label="🏢 市值与板块" name="market_cap">
            <div class="param-grid">
              <div class="param-item">
                <span class="param-label">市值分级:</span>
                <el-select v-model="form.params.market_cap_range" clearable placeholder="全部分级" style="width: 100%">
                  <el-option label="全部分级" value="" />
                  <el-option label="小盘 (&lt; 100亿)" value="small" />
                  <el-option label="中盘 (100 - 500亿)" value="medium" />
                  <el-option label="大盘 (&gt; 500亿)" value="large" />
                </el-select>
              </div>
              <div class="param-item">
                <span class="param-label">自定义市值 (亿元):</span>
                <div class="range-inputs">
                  <el-input-number v-model="form.params.min_market_cap" :min="0" :precision="1" placeholder="Min" controls-position="right" />
                  <span class="range-sep">~</span>
                  <el-input-number v-model="form.params.max_market_cap" :min="0" :precision="1" placeholder="Max" controls-position="right" />
                </div>
              </div>
              <div class="param-item full-span">
                <span class="param-label">限定板块:</span>
                <el-radio-group v-model="form.params.market" size="small">
                  <el-radio-button label="全部">全部板块</el-radio-button>
                  <el-radio-button label="主板">主板</el-radio-button>
                  <el-radio-button label="创业板">创业板</el-radio-button>
                  <el-radio-button label="科创板">科创板</el-radio-button>
                  <el-radio-button label="北交所">北交所</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSave">
          <el-icon><Check /></el-icon>
          {{ isEdit ? '保存修改' : '确认创建策略' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { Download, Operation, InfoFilled, Check } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance } from 'element-plus'
import type { CustomQuantStrategy, StockPoolParams } from '@/api/stocks'

const props = defineProps<{
  visible: boolean
  strategy?: CustomQuantStrategy | null
  currentParams?: StockPoolParams
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'save', payload: any, id?: string): void
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const activeTab = ref('valuation')

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const isEdit = computed(() => !!props.strategy?.id)
const isQuantCandidate = computed(() => {
  return props.strategy?.id === 'preset_quant_candidate' || props.strategy?.cannot_delete === true
})

const initialParams = () => ({
  min_pe: null as number | null,
  max_pe: null as number | null,
  min_pb: null as number | null,
  max_pb: null as number | null,
  min_ps: null as number | null,
  max_ps: null as number | null,
  min_close: null as number | null,
  max_close: null as number | null,
  min_pct_chg: null as number | null,
  max_pct_chg: null as number | null,
  min_turnover_rate: null as number | null,
  max_turnover_rate: null as number | null,
  min_volume_ratio: null as number | null,
  max_volume_ratio: null as number | null,
  min_amount: null as number | null,
  volume_level: '',
  market_cap_range: '',
  min_market_cap: null as number | null,
  max_market_cap: null as number | null,
  min_roe: null as number | null,
  max_roe: null as number | null,
  min_net_profit_growth: null as number | null,
  max_net_profit_growth: null as number | null,
  min_revenue_growth: null as number | null,
  max_revenue_growth: null as number | null,
  min_gross_margin: null as number | null,
  max_gross_margin: null as number | null,
  market: '全部',
  source: '全部',
  preset: undefined as string | undefined
})

const form = reactive({
  name: '',
  description: '',
  tag_type: 'primary',
  icon: '🎯',
  params: initialParams()
})

const minAmountWan = computed({
  get: () => (form.params.min_amount != null ? form.params.min_amount / 10000 : undefined),
  set: (val: number | undefined) => {
    form.params.min_amount = val != null ? val * 10000 : null
  }
})

const rules = {
  name: [
    { required: true, message: '请输入量化策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// 统计当前配置的有效约束项数
const configuredIndicatorCount = computed(() => {
  let count = 0
  const p = form.params
  if (p.min_pe != null || p.max_pe != null) count++
  if (p.min_pb != null || p.max_pb != null) count++
  if (p.min_ps != null || p.max_ps != null) count++
  if (p.min_close != null || p.max_close != null) count++
  if (p.min_pct_chg != null || p.max_pct_chg != null) count++
  if (p.min_turnover_rate != null || p.max_turnover_rate != null) count++
  if (p.min_volume_ratio != null || p.max_volume_ratio != null) count++
  if (p.min_amount != null) count++
  if (p.volume_level) count++
  if (p.min_roe != null || p.max_roe != null) count++
  if (p.min_net_profit_growth != null || p.max_net_profit_growth != null) count++
  if (p.min_revenue_growth != null || p.max_revenue_growth != null) count++
  if (p.min_gross_margin != null || p.max_gross_margin != null) count++
  if (p.market_cap_range || p.min_market_cap != null || p.max_market_cap != null) count++
  if (p.market && p.market !== '全部') count++
  return count
})

// 从当前筛选条件快速载入
const loadFromCurrentParams = () => {
  if (!props.currentParams) return
  const cur = props.currentParams
  form.params = {
    ...initialParams(),
    min_pe: cur.min_pe ?? null,
    max_pe: cur.max_pe ?? null,
    min_pb: cur.min_pb ?? null,
    max_pb: cur.max_pb ?? null,
    min_ps: cur.min_ps ?? null,
    max_ps: cur.max_ps ?? null,
    min_close: cur.min_close ?? null,
    max_close: cur.max_close ?? null,
    min_pct_chg: cur.min_pct_chg ?? null,
    max_pct_chg: cur.max_pct_chg ?? null,
    min_turnover_rate: cur.min_turnover_rate ?? null,
    max_turnover_rate: cur.max_turnover_rate ?? null,
    min_volume_ratio: cur.min_volume_ratio ?? null,
    max_volume_ratio: cur.max_volume_ratio ?? null,
    min_amount: cur.min_amount ?? null,
    volume_level: cur.volume_level || '',
    market_cap_range: cur.market_cap_range || '',
    min_market_cap: cur.min_market_cap ?? null,
    max_market_cap: cur.max_market_cap ?? null,
    min_roe: cur.min_roe ?? null,
    max_roe: cur.max_roe ?? null,
    min_net_profit_growth: cur.min_net_profit_growth ?? null,
    max_net_profit_growth: cur.max_net_profit_growth ?? null,
    min_revenue_growth: cur.min_revenue_growth ?? null,
    max_revenue_growth: cur.max_revenue_growth ?? null,
    min_gross_margin: cur.min_gross_margin ?? null,
    max_gross_margin: cur.max_gross_margin ?? null,
    market: cur.market || '全部',
    source: cur.source || '全部',
    preset: cur.preset || undefined
  }
  ElMessage.success(`已提取当前页面的 ${configuredIndicatorCount.value} 项筛选条件！`)
}

// 清空表单
const resetFormToEmpty = () => {
  form.params = initialParams()
  ElMessage.info('已重置所有量化指标参数')
}

// 监听打开与回显数据
watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (props.strategy) {
        form.name = props.strategy.name || ''
        form.description = props.strategy.description || ''
        form.tag_type = props.strategy.tag_type || 'primary'
        form.icon = props.strategy.icon || '🎯'
        form.params = { ...initialParams(), ...(props.strategy.params || {}) }
      } else {
        form.name = ''
        form.description = ''
        form.tag_type = 'primary'
        form.icon = '🎯'
        // 新建时，如果页面有现成筛选参数，优先自动填入
        if (props.currentParams) {
          loadFromCurrentParams()
        } else {
          form.params = initialParams()
        }
      }
    }
  }
)

const handleSave = async () => {
  if (!formRef.value) return
  await formRef.value.validate((valid) => {
    if (!valid) return
    const payload: any = {
      name: form.name.trim(),
      description: form.description?.trim() || '',
      tag_type: form.tag_type,
      icon: form.icon,
      params: { ...form.params }
    }
    if (isQuantCandidate.value) {
      payload.params.preset = 'quant_candidate'
      payload.cannot_delete = true
    }
    emit('save', payload, props.strategy?.id)
  })
}
</script>

<style scoped lang="scss">
.strategy-edit-dialog {
  :deep(.el-dialog__body) {
    padding: 16px 20px;
    max-height: 68vh;
    overflow-y: auto;
  }
}

.dialog-tips-bar {
  margin-bottom: 16px;
  .tips-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
  }
}

.section-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;

  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;

    .active-indicator-pill {
      margin-left: auto;
    }
  }
}

.indicator-tabs {
  background: #ffffff;
  border-radius: 6px;
  padding: 10px 14px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 20px;
  padding: 6px 0;

  .param-item {
    display: flex;
    flex-direction: column;
    gap: 6px;

    &.full-span {
      grid-column: span 2;
    }

    .param-label {
      font-size: 12px;
      color: #475569;
      font-weight: 500;
    }

    .range-inputs {
      display: flex;
      align-items: center;
      gap: 6px;

      :deep(.el-input-number) {
        width: 100%;
      }

      .range-sep {
        color: #94a3b8;
        font-weight: 600;
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
