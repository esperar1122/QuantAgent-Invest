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
          <div class="preset-group">
            <span class="preset-label">量化策略预设:</span>
            <el-button
              v-for="preset in presets"
              :key="preset.name"
              size="small"
              round
              :type="preset.type"
              @click="$emit('apply-preset', preset)"
            >
              {{ preset.name }}
            </el-button>
          </div>
        </div>

        <el-divider style="margin: 12px 0 16px 0" />

        <el-row :gutter="16">
          <!-- 1. 估值因子 -->
          <el-col :xs="24" :sm="12" :md="6">
            <div class="filter-group-title">📊 估值因子区间</div>
            <div class="range-row">
              <span class="range-label">市盈率 (PE):</span>
              <el-input-number
                v-model="params.min_pe"
                :min="0"
                :precision="1"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_pe"
                :min="0"
                :precision="1"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">市净率 (PB):</span>
              <el-input-number
                v-model="params.min_pb"
                :min="0"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_pb"
                :min="0"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">市销率 (PS):</span>
              <el-input-number
                v-model="params.min_ps"
                :min="0"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_ps"
                :min="0"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>
          </el-col>

          <!-- 2. 行情动态与交易 -->
          <el-col :xs="24" :sm="12" :md="6">
            <div class="filter-group-title">📈 行情动态区间</div>
            <div class="range-row">
              <span class="range-label">最新股价 (¥):</span>
              <el-input-number
                v-model="params.min_close"
                :min="0"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_close"
                :min="0"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">日涨跌幅 (%):</span>
              <el-input-number
                v-model="params.min_pct_chg"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_pct_chg"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">换手率 (%):</span>
              <el-input-number
                v-model="params.min_turnover_rate"
                :min="0"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_turnover_rate"
                :min="0"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">量比区间:</span>
              <el-input-number
                v-model="params.min_volume_ratio"
                :min="0"
                :precision="2"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_volume_ratio"
                :min="0"
                :precision="2"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>
          </el-col>

          <!-- 3. 财务质量与成长 -->
          <el-col :xs="24" :sm="12" :md="6">
            <div class="filter-group-title">💡 财务质量与成长</div>
            <div class="range-row">
              <span class="range-label">净资产收益率 (ROE %):</span>
              <el-input-number
                v-model="params.min_roe"
                :precision="1"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_roe"
                :precision="1"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">净利同比增速 (%):</span>
              <el-input-number
                v-model="params.min_net_profit_growth"
                :precision="1"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_net_profit_growth"
                :precision="1"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">营收同比增速 (%):</span>
              <el-input-number
                v-model="params.min_revenue_growth"
                :precision="1"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_revenue_growth"
                :precision="1"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <div class="range-row">
              <span class="range-label">销售毛利率 (%):</span>
              <el-input-number
                v-model="params.min_gross_margin"
                :precision="1"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_gross_margin"
                :precision="1"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>
          </el-col>

          <!-- 4. 规模与操作 -->
          <el-col :xs="24" :sm="12" :md="6">
            <div class="filter-group-title">🏢 规模与操作</div>
            <div class="range-row">
              <span class="range-label">成交活跃度:</span>
              <el-select
                v-model="params.volume_level"
                placeholder="全部活跃度"
                clearable
                style="width: 175px"
              >
                <el-option label="全部活跃度" value="" />
                <el-option label="🔥 高活跃 (> 10亿)" value="high" />
                <el-option label="⚖️ 正常 (3-10亿)" value="medium" />
                <el-option label="❄️ 清淡 (< 3亿)" value="low" />
              </el-select>
            </div>

            <div class="range-row" style="margin-top: 10px">
              <span class="range-label">市值分类:</span>
              <el-radio-group v-model="params.market_cap_range" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="small">&lt;100亿</el-radio-button>
                <el-radio-button label="medium">100-500亿</el-radio-button>
                <el-radio-button label="large">&gt;500亿</el-radio-button>
              </el-radio-group>
            </div>

            <div class="range-row" style="margin-top: 10px">
              <span class="range-label">自定义市值 (亿):</span>
              <el-input-number
                v-model="params.min_market_cap"
                :min="0"
                :precision="0"
                placeholder="Min"
                controls-position="right"
                class="range-input"
              />
              <span class="range-separator">~</span>
              <el-input-number
                v-model="params.max_market_cap"
                :min="0"
                :precision="0"
                placeholder="Max"
                controls-position="right"
                class="range-input"
              />
            </div>

            <!-- 面板操作按钮 -->
            <div class="panel-action-btns">
              <el-button type="primary" size="default" @click="$emit('search')">
                <el-icon><Search /></el-icon>
                执行筛选
              </el-button>
              <el-button size="default" @click="$emit('reset-advanced')">
                清空高级
              </el-button>
              <el-button type="text" size="default" @click="$emit('close')">
                收起
              </el-button>
            </div>
          </el-col>
        </el-row>
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
import { Operation, Search } from '@element-plus/icons-vue'
import type { StockPoolParams } from '@/api/stocks'

defineProps<{
  show: boolean
  params: StockPoolParams
  presets: Array<{ name: string; type: any; params: any }>
  activeTags: Array<{ key: string; label: string; text: string }>
}>()

defineEmits<{
  (e: 'search'): void
  (e: 'reset-advanced'): void
  (e: 'close'): void
  (e: 'apply-preset', preset: any): void
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

    .preset-group {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;

      .preset-label {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
      }
    }
  }

  .filter-group-title {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    margin-bottom: 10px;
    border-bottom: 1px dashed #cbd5e1;
    padding-bottom: 4px;
  }

  .range-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;

    .range-label {
      font-size: 12px;
      color: #475569;
      width: 130px;
      flex-shrink: 0;
      text-align: right;
    }

    .range-input {
      width: 90px;

      :deep(.el-input__inner) {
        text-align: center;
        padding: 0 4px;
      }
    }

    .range-separator {
      color: #94a3b8;
      font-size: 12px;
    }
  }

  .panel-action-btns {
    margin-top: 18px;
    display: flex;
    gap: 8px;
    align-items: center;
    justify-content: flex-end;
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
