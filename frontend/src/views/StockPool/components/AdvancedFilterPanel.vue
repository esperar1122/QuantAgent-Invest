<template>
  <div class="advanced-filter-wrapper">
    <!-- 展开式：多维度量化指标高级筛选面板 -->
    <el-collapse-transition>
      <div v-show="show" class="advanced-filter-panel">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon><Operation /></el-icon>
            <span>多维量化筛选条件配置</span>
          </div>

          <div class="header-action-group">
            <el-button
              type="primary"
              size="small"
              @click="$emit('create-strategy')"
            >
              <el-icon><Plus /></el-icon>
              新建策略
            </el-button>
            <el-button
              type="warning"
              plain
              size="small"
              @click="$emit('save-current')"
            >
              <el-icon><FolderAdd /></el-icon>
              保存当前条件为策略
            </el-button>
            <el-button
              size="small"
              @click="$emit('manage-strategies')"
            >
              <el-icon><Setting /></el-icon>
              管理策略库
            </el-button>
          </div>
        </div>

        <!-- 策略快捷预设栏 -->
        <div class="preset-section">
          <!-- 1. 系统经典预设库（可直接应用，也可点击小笔修改） -->
          <div class="preset-subgroup">
            <span class="preset-label">⚡ 经典推荐策略 (支持自定义修改):</span>
            <div class="preset-chips">
              <el-button-group
                v-for="strat in systemStrategies"
                :key="strat.id"
                class="custom-strat-btn-group"
              >
                <el-button
                  size="small"
                  round
                  :type="strat.tag_type || 'primary'"
                  class="strat-main-btn"
                  @click="$emit('apply-custom', strat)"
                >
                  {{ strat.icon || '🎯' }} {{ strat.name }}
                </el-button>
                <el-button
                  size="small"
                  round
                  :type="strat.tag_type || 'primary'"
                  class="strat-action-btn"
                  title="自定义修改此策略指标规则"
                  @click.stop="$emit('edit-strategy', strat)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>

          <!-- 2. 用户自建策略 -->
          <div v-if="userStrategies.length > 0" class="preset-subgroup" style="margin-top: 8px">
            <span class="preset-label custom-label">★ 自定义策略:</span>
            <div class="preset-chips">
              <el-button-group
                v-for="strat in userStrategies"
                :key="strat.id"
                class="custom-strat-btn-group"
              >
                <el-button
                  size="small"
                  round
                  :type="strat.tag_type || 'primary'"
                  class="strat-main-btn"
                  @click="$emit('apply-custom', strat)"
                >
                  {{ strat.icon || '🎯' }} {{ strat.name }}
                </el-button>
                <el-button
                  size="small"
                  round
                  :type="strat.tag_type || 'primary'"
                  class="strat-action-btn"
                  title="编辑修改此自建策略"
                  @click.stop="$emit('edit-strategy', strat)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-button-group>
            </div>
          </div>
        </div>

        <el-divider style="margin: 12px 0 16px 0" />

        <el-row :gutter="14" class="filter-groups-row">
          <!-- 1. 估值因子 -->
          <el-col :xs="24" :sm="12" :md="12" :lg="6" class="filter-col">
            <div class="filter-group-card">
              <div class="group-header">
                <div class="group-title">
                  <span class="group-icon">📊</span>
                  <span>估值因子区间</span>
                </div>
                <span class="group-tag">Valuation</span>
              </div>

              <div class="group-body">
                <!-- 市盈率 PE -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">市盈率 (PE)</span>
                    <span v-if="params.min_pe != null || params.max_pe != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_pe"
                      :min="0"
                      :precision="1"
                      placeholder="最小值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_pe"
                      :min="0"
                      :precision="1"
                      placeholder="最大值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 市净率 PB -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">市净率 (PB)</span>
                    <span v-if="params.min_pb != null || params.max_pb != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_pb"
                      :min="0"
                      :precision="2"
                      placeholder="最小值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_pb"
                      :min="0"
                      :precision="2"
                      placeholder="最大值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 市销率 PS -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">市销率 (PS)</span>
                    <span v-if="params.min_ps != null || params.max_ps != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_ps"
                      :min="0"
                      :precision="2"
                      placeholder="最小值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_ps"
                      :min="0"
                      :precision="2"
                      placeholder="最大值"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <!-- 2. 行情动态与交易 -->
          <el-col :xs="24" :sm="12" :md="12" :lg="6" class="filter-col">
            <div class="filter-group-card">
              <div class="group-header">
                <div class="group-title">
                  <span class="group-icon">📈</span>
                  <span>行情动态区间</span>
                </div>
                <span class="group-tag">Market</span>
              </div>

              <div class="group-body">
                <!-- 最新股价 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">最新股价 (¥)</span>
                    <span v-if="params.min_close != null || params.max_close != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_close"
                      :min="0"
                      :precision="2"
                      placeholder="最低价"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_close"
                      :min="0"
                      :precision="2"
                      placeholder="最高价"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 日涨跌幅 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">日涨跌幅 (%)</span>
                    <span v-if="params.min_pct_chg != null || params.max_pct_chg != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_pct_chg"
                      :precision="2"
                      placeholder="最小跌幅"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_pct_chg"
                      :precision="2"
                      placeholder="最大涨幅"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 换手率 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">换手率 (%)</span>
                    <span v-if="params.min_turnover_rate != null || params.max_turnover_rate != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_turnover_rate"
                      :min="0"
                      :precision="2"
                      placeholder="最低换手"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_turnover_rate"
                      :min="0"
                      :precision="2"
                      placeholder="最高换手"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 量比区间 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">量比区间</span>
                    <span v-if="params.min_volume_ratio != null || params.max_volume_ratio != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_volume_ratio"
                      :min="0"
                      :precision="2"
                      placeholder="最小量比"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_volume_ratio"
                      :min="0"
                      :precision="2"
                      placeholder="最大量比"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <!-- 3. 财务质量与成长 -->
          <el-col :xs="24" :sm="12" :md="12" :lg="6" class="filter-col">
            <div class="filter-group-card">
              <div class="group-header">
                <div class="group-title">
                  <span class="group-icon">💡</span>
                  <span>财务质量与成长</span>
                </div>
                <span class="group-tag">Financial</span>
              </div>

              <div class="group-body">
                <!-- 净资产收益率 ROE -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">净资产收益率 (ROE %)</span>
                    <span v-if="params.min_roe != null || params.max_roe != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_roe"
                      :precision="1"
                      placeholder="最低ROE"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_roe"
                      :precision="1"
                      placeholder="最高ROE"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 净利同比增速 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">净利同比增速 (%)</span>
                    <span v-if="params.min_net_profit_growth != null || params.max_net_profit_growth != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_net_profit_growth"
                      :precision="1"
                      placeholder="最低增速"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_net_profit_growth"
                      :precision="1"
                      placeholder="最高增速"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 营收同比增速 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">营收同比增速 (%)</span>
                    <span v-if="params.min_revenue_growth != null || params.max_revenue_growth != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_revenue_growth"
                      :precision="1"
                      placeholder="最低增速"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_revenue_growth"
                      :precision="1"
                      placeholder="最高增速"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>

                <!-- 销售毛利率 -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">销售毛利率 (%)</span>
                    <span v-if="params.min_gross_margin != null || params.max_gross_margin != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-inputs">
                    <el-input-number
                      v-model="params.min_gross_margin"
                      :precision="1"
                      placeholder="最低毛利"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_gross_margin"
                      :precision="1"
                      placeholder="最高毛利"
                      :controls="false"
                      size="small"
                      class="range-input"
                    />
                  </div>
                </div>
              </div>
            </div>
          </el-col>

          <!-- 4. 规模与流动性 -->
          <el-col :xs="24" :sm="12" :md="12" :lg="6" class="filter-col">
            <div class="filter-group-card">
              <div class="group-header">
                <div class="group-title">
                  <span class="group-icon">🏢</span>
                  <span>规模与流动性</span>
                </div>
                <span class="group-tag">Liquidity</span>
              </div>

              <div class="group-body">
                <!-- 1. 日均成交活跃度 (快捷预设 + 自定义范围) -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">日均成交活跃度 (亿元)</span>
                    <span v-if="params.volume_level || params.min_amount != null || params.max_amount != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-full-row">
                    <el-radio-group
                      v-model="params.volume_level"
                      size="small"
                      class="fluid-radio-group"
                      @change="onVolumePresetChange"
                    >
                      <el-radio-button label="">全部</el-radio-button>
                      <el-radio-button label="high">&gt;10亿</el-radio-button>
                      <el-radio-button label="medium">3-10亿</el-radio-button>
                      <el-radio-button label="low">&lt;3亿</el-radio-button>
                    </el-radio-group>
                  </div>
                  <div class="field-inputs" style="margin-top: 4px;">
                    <el-input-number
                      v-model="params.min_amount"
                      :min="0"
                      :precision="1"
                      placeholder="最低成交(亿)"
                      :controls="false"
                      size="small"
                      class="range-input"
                      @change="onAmountInputChange"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_amount"
                      :min="0"
                      :precision="1"
                      placeholder="最高成交(亿)"
                      :controls="false"
                      size="small"
                      class="range-input"
                      @change="onAmountInputChange"
                    />
                  </div>
                </div>

                <!-- 2. 市值分类 (快捷预设 + 自定义范围) -->
                <div class="filter-field">
                  <div class="field-header">
                    <span class="field-label">市值分类与区间 (亿元)</span>
                    <span v-if="params.market_cap_range || params.min_market_cap != null || params.max_market_cap != null" class="active-indicator">已设</span>
                  </div>
                  <div class="field-full-row">
                    <el-radio-group
                      v-model="params.market_cap_range"
                      size="small"
                      class="fluid-radio-group"
                      @change="onMarketCapPresetChange"
                    >
                      <el-radio-button label="">全部</el-radio-button>
                      <el-radio-button label="small">&lt;100亿</el-radio-button>
                      <el-radio-button label="medium">100-500亿</el-radio-button>
                      <el-radio-button label="large">&gt;500亿</el-radio-button>
                    </el-radio-group>
                  </div>
                  <div class="field-inputs" style="margin-top: 4px;">
                    <el-input-number
                      v-model="params.min_market_cap"
                      :min="0"
                      :precision="0"
                      placeholder="最低市值(亿)"
                      :controls="false"
                      size="small"
                      class="range-input"
                      @change="onMarketCapInputChange"
                    />
                    <span class="range-sep">~</span>
                    <el-input-number
                      v-model="params.max_market_cap"
                      :min="0"
                      :precision="0"
                      placeholder="最高市值(亿)"
                      :controls="false"
                      size="small"
                      class="range-input"
                      @change="onMarketCapInputChange"
                    />
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 底部统一操作与提示栏 -->
        <div class="panel-bottom-bar">
          <div class="bottom-tips">
            <el-icon><InfoFilled /></el-icon>
            <span>多因子组合筛选：输入框留空表示不限制；调整后点击【执行筛选】生效</span>
          </div>
          <div class="bottom-actions">
            <el-button size="small" @click="$emit('reset-advanced')">
              <el-icon><Refresh /></el-icon>
              清空高级条件
            </el-button>
            <el-button type="primary" size="small" @click="$emit('search')">
              <el-icon><Search /></el-icon>
              执行筛选
            </el-button>
            <el-button size="small" text @click="$emit('close')">
              收起面板
            </el-button>
          </div>
        </div>
      </div>
    </el-collapse-transition>

    <!-- 当前生效过滤条件标签栏 -->
    <div v-if="activeTags.length > 0" class="active-tags-bar">
      <span class="tags-label">当前生效筛选:</span>
      <el-tag
        v-for="tag in activeTags"
        :key="tag.key"
        closable
        effect="light"
        class="filter-tag-item"
        @close="$emit('remove-tag', tag.key)"
      >
        <strong>{{ tag.label }}:</strong> {{ tag.text }}
      </el-tag>
      <el-button type="text" size="small" class="clear-all-btn" @click="$emit('clear-all')">
        清空全部条件
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Operation, Search, Plus, FolderAdd, Setting, Edit, Refresh, InfoFilled } from '@element-plus/icons-vue'
import type { StockPoolParams, CustomQuantStrategy } from '@/api/stocks'

const props = defineProps<{
  show: boolean
  params: StockPoolParams
  presets: Array<{ name: string; type: any; params: any }>
  activeTags: Array<{ key: string; label: string; text: string }>
  customStrategies?: CustomQuantStrategy[]
}>()

const systemStrategies = computed(() => {
  const sys = props.customStrategies?.filter(s => s.is_system || s.id.startsWith('preset_')) || []
  if (sys.length > 0) return sys
  return (props.presets || []).map((p: any, idx) => ({
    id: p.id || `preset_${idx}`,
    name: p.name,
    icon: '',
    tag_type: p.type || 'primary',
    params: p.params
  }))
})

const userStrategies = computed(() => {
  return props.customStrategies?.filter(s => !s.is_system && !s.id.startsWith('preset_')) || []
})

// 快捷预设与自定义日均成交额同步联动
const onVolumePresetChange = (val: any) => {
  if (val === 'high') {
    props.params.min_amount = 10
    props.params.max_amount = null
  } else if (val === 'medium') {
    props.params.min_amount = 3
    props.params.max_amount = 10
  } else if (val === 'low') {
    props.params.min_amount = null
    props.params.max_amount = 3
  } else {
    props.params.min_amount = null
    props.params.max_amount = null
  }
}

const onAmountInputChange = () => {
  const min = props.params.min_amount
  const max = props.params.max_amount
  if (min === 10 && (max === null || max === undefined)) {
    props.params.volume_level = 'high'
  } else if (min === 3 && max === 10) {
    props.params.volume_level = 'medium'
  } else if ((min === null || min === undefined || min === 0) && max === 3) {
    props.params.volume_level = 'low'
  } else if (min == null && max == null) {
    props.params.volume_level = ''
  } else {
    // 自定义区间，不匹配默认三大档位时取消预设单选高亮
    props.params.volume_level = ''
  }
}

// 快捷预设与自定义市值同步联动
const onMarketCapPresetChange = (val: any) => {
  if (val === 'small') {
    props.params.min_market_cap = null
    props.params.max_market_cap = 100
  } else if (val === 'medium') {
    props.params.min_market_cap = 100
    props.params.max_market_cap = 500
  } else if (val === 'large') {
    props.params.min_market_cap = 500
    props.params.max_market_cap = null
  } else {
    props.params.min_market_cap = null
    props.params.max_market_cap = null
  }
}

const onMarketCapInputChange = () => {
  const min = props.params.min_market_cap
  const max = props.params.max_market_cap
  if ((min === null || min === undefined || min === 0) && max === 100) {
    props.params.market_cap_range = 'small'
  } else if (min === 100 && max === 500) {
    props.params.market_cap_range = 'medium'
  } else if (min === 500 && (max === null || max === undefined)) {
    props.params.market_cap_range = 'large'
  } else if (min == null && max == null) {
    props.params.market_cap_range = ''
  } else {
    // 自定义区间，不匹配默认三大档位时取消预设单选高亮
    props.params.market_cap_range = ''
  }
}

defineEmits<{
  (e: 'search'): void
  (e: 'reset-advanced'): void
  (e: 'close'): void
  (e: 'apply-preset', preset: any): void
  (e: 'apply-custom', strat: CustomQuantStrategy): void
  (e: 'save-current'): void
  (e: 'create-strategy'): void
  (e: 'edit-strategy', strat: CustomQuantStrategy): void
  (e: 'delete-strategy', id: string): void
  (e: 'manage-strategies'): void
  (e: 'remove-tag', key: string): void
  (e: 'clear-all'): void
}>()
</script>

<style scoped lang="scss">
.advanced-filter-panel {
  margin-top: 16px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
  border: 1px solid #cbd5e1;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;

    .panel-title {
      font-weight: 600;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 15px;
    }

    .header-action-group {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
  }

  .preset-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 12px 0 6px 0;
    padding: 10px 14px;
    background: #ffffff;
    border-radius: 6px;
    border: 1px solid #e2e8f0;

    .preset-subgroup {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;

      .preset-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        min-width: 80px;

        &.custom-label {
          color: #2563eb;
        }
      }

      .preset-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
    }
  }

  .custom-strat-btn-group {
    .strat-main-btn {
      padding-right: 8px;
    }
    .strat-action-btn {
      padding-left: 6px;
      padding-right: 6px;
      opacity: 0.85;
      &:hover {
        opacity: 1;
      }
    }
  }

  .filter-groups-row {
    margin-bottom: 8px;
  }

  .filter-col {
    margin-bottom: 12px;
  }

  .filter-group-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
    overflow: hidden;

    &:hover {
      border-color: #cbd5e1;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }

    .group-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 8px;
      margin-bottom: 10px;
      border-bottom: 1px dashed #e2e8f0;

      .group-title {
        font-size: 13px;
        font-weight: 600;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 6px;

        .group-icon {
          font-size: 14px;
        }
      }

      .group-tag {
        font-size: 10px;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background: #f8fafc;
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid #f1f5f9;
      }
    }

    .group-body {
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex: 1;
    }
  }

  .filter-field {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .field-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .field-label {
        font-size: 12px;
        color: #475569;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .active-indicator {
        font-size: 10px;
        color: #2563eb;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 3px;
        padding: 0 4px;
        line-height: 14px;
        font-weight: 600;
      }
    }

    .field-inputs {
      display: flex;
      align-items: center;
      gap: 6px;
      width: 100%;

      .range-input {
        flex: 1 1 0;
        min-width: 0;
        width: 0;

        :deep(.el-input__wrapper) {
          padding: 0 6px;
        }

        :deep(.el-input__inner) {
          text-align: center;
          padding: 0;
          font-size: 12px;
        }
      }

      .range-sep {
        color: #94a3b8;
        font-size: 12px;
        flex-shrink: 0;
      }
    }

    .field-full-row {
      width: 100%;

      .full-select {
        width: 100%;
      }

      .fluid-radio-group {
        display: flex;
        width: 100%;

        :deep(.el-radio-button) {
          flex: 1;
          text-align: center;
        }

        :deep(.el-radio-button__inner) {
          width: 100%;
          padding: 6px 2px;
          font-size: 11px;
        }
      }
    }
  }

  .panel-bottom-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 6px;
    padding: 10px 14px;
    background: #ffffff;
    border-radius: 6px;
    border: 1px solid #e2e8f0;

    .bottom-tips {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #64748b;

      .el-icon {
        color: #3b82f6;
      }
    }

    .bottom-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.active-tags-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;

  .tags-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
  }

  .filter-tag-item {
    font-size: 12px;
  }

  .clear-all-btn {
    color: #ef4444;
    font-size: 12px;
    padding: 0 4px;

    &:hover {
      color: #dc2626;
    }
  }
}
</style>
