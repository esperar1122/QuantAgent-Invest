<template>
  <el-form :inline="true" class="filter-form" @submit.prevent="$emit('search')">
    <el-form-item label="标的检索">
      <el-input
        v-model="params.keyword"
        placeholder="代码 / 简称 (例: 000300, 沪深300, 芯片)"
        clearable
        style="width: 240px"
        @clear="$emit('search')"
        @keyup.enter="$emit('search')"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item label="所属板块">
      <el-radio-group v-model="params.market" @change="$emit('search')">
        <el-radio-button label="全部">全部</el-radio-button>
        <el-radio-button label="主板">主板</el-radio-button>
        <el-radio-button label="创业板">创业板</el-radio-button>
        <el-radio-button label="科创板">科创板</el-radio-button>
        <el-radio-button label="北交所">北交所</el-radio-button>
        <el-radio-button label="重要指数">重要指数</el-radio-button>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="数据源">
      <el-select
        v-model="params.source"
        placeholder="数据源"
        style="width: 130px"
        @change="$emit('search')"
      >
        <el-option label="全部数据源" value="全部" />
        <el-option label="AKShare" value="akshare" />
        <el-option label="BaoStock" value="baostock" />
        <el-option label="Tushare" value="tushare" />
      </el-select>
    </el-form-item>

    <el-form-item class="actions-form-item">
      <div class="action-buttons-group">
        <el-button type="primary" class="btn-action btn-search" @click="$emit('search')">
          <el-icon><Search /></el-icon>
          筛选
        </el-button>

        <el-button
          :type="showAdvanced || hasActiveAdvanced ? 'warning' : 'default'"
          :plain="!showAdvanced"
          class="btn-action btn-advanced"
          @click="$emit('toggle-advanced')"
        >
          <el-icon><Filter /></el-icon>
          多维指标筛选
          <el-badge
            v-if="activeAdvancedCount > 0"
            :value="activeAdvancedCount"
            class="filter-badge"
          />
        </el-button>

        <!-- 🎯 量化策略库快捷下拉入口 -->
        <el-dropdown trigger="click" @command="handleCommand">
          <el-button type="success" plain class="btn-action strategy-dropdown-btn">
            <el-icon><Aim /></el-icon>
            量化策略库
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="strategy-dropdown-menu">
              <!-- 核心驱动候选池 -->
              <div class="dropdown-group-header">🎯 系统核心驱动池</div>
              <el-dropdown-item
                v-if="quantCandidateStrategy"
                :command="{ type: 'apply-custom', data: quantCandidateStrategy }"
              >
                <div class="strategy-menu-item">
                  <span>{{ quantCandidateStrategy.icon || '🎯' }} {{ quantCandidateStrategy.name }}</span>
                  <el-tag size="small" type="warning" effect="plain" class="mini-tag">核心驱动</el-tag>
                </div>
              </el-dropdown-item>

              <!-- 经典推荐策略 -->
              <div class="dropdown-group-header header-divider">⚡ 经典推荐策略 (支持自定义)</div>
              <el-dropdown-item
                v-for="strat in systemPresetList"
                :key="strat.id"
                :command="{ type: 'apply-custom', data: strat }"
              >
                <span>{{ strat.icon || '📌' }} {{ strat.name }}</span>
              </el-dropdown-item>

              <!-- 自建策略 -->
              <div class="dropdown-group-header header-divider">★ 我的自建策略 ({{ userCustomList.length }})</div>
              <el-dropdown-item
                v-for="strat in userCustomList"
                :key="strat.id"
                :command="{ type: 'apply-custom', data: strat }"
              >
                <span>{{ strat.icon || '🎯' }} {{ strat.name }}</span>
              </el-dropdown-item>
              <el-dropdown-item v-if="userCustomList.length === 0" disabled>
                <span style="font-size: 12px; color: #94a3b8">暂无自建策略</span>
              </el-dropdown-item>

              <el-dropdown-item divided :command="{ type: 'save-current' }">
                <el-icon><FolderAdd /></el-icon>
                <span class="action-highlight">保存当前条件为策略...</span>
              </el-dropdown-item>
              <el-dropdown-item :command="{ type: 'create' }">
                <el-icon><Plus /></el-icon>
                <span>新建空白量化策略...</span>
              </el-dropdown-item>
              <el-dropdown-item :command="{ type: 'manage' }">
                <el-icon><Setting /></el-icon>
                <span>管理与配置策略库 (增/删/改)...</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <div class="btn-divider" />

        <el-button class="btn-action btn-reset" @click="$emit('reset')">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Search, Filter, Refresh, Aim, ArrowDown, FolderAdd, Plus, Setting } from '@element-plus/icons-vue'
import type { StockPoolParams, CustomQuantStrategy } from '@/api/stocks'

const props = defineProps<{
  params: StockPoolParams
  showAdvanced: boolean
  hasActiveAdvanced: boolean
  activeAdvancedCount: number
  customStrategies?: CustomQuantStrategy[]
  presets?: Array<{ name: string; type: any; params: any }>
}>()

const quantCandidateStrategy = computed(() => {
  return props.customStrategies?.find(s => s.id === 'preset_quant_candidate' || s.cannot_delete)
})

const systemPresetList = computed<CustomQuantStrategy[]>(() => {
  const list = props.customStrategies?.filter(s => (s.is_system || s.id.startsWith('preset_')) && s.id !== 'preset_quant_candidate') || []
  if (list.length > 0) return list
  return (props.presets || []).filter(p => (p as any).id !== 'preset_quant_candidate').map((p: any, idx) => ({
    id: p.id || `preset_${idx}`,
    name: p.name,
    icon: '📌',
    tag_type: p.type || 'primary',
    params: p.params || {}
  }))
})

const userCustomList = computed(() => {
  return props.customStrategies?.filter(s => !s.is_system && !s.id.startsWith('preset_')) || []
})

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
  (e: 'toggle-advanced'): void
  (e: 'apply-custom', strat: CustomQuantStrategy): void
  (e: 'apply-preset', preset: any): void
  (e: 'save-current'): void
  (e: 'create-strategy'): void
  (e: 'manage-strategies'): void
}>()

const handleCommand = (cmd: { type: string; data?: any }) => {
  if (cmd.type === 'apply-custom') {
    emit('apply-custom', cmd.data)
  } else if (cmd.type === 'apply-preset') {
    emit('apply-preset', cmd.data)
  } else if (cmd.type === 'save-current') {
    emit('save-current')
  } else if (cmd.type === 'create') {
    emit('create-strategy')
  } else if (cmd.type === 'manage') {
    emit('manage-strategies')
  }
}
</script>

<style scoped lang="scss">
.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;

  :deep(.el-form-item) {
    margin-bottom: 0;
    margin-right: 0;
  }

  .action-buttons-group {
    display: inline-flex;
    align-items: center;
    gap: 12px; // 12px 舒适清晰的间距

    :deep(.el-button) {
      margin-left: 0 !important; // 消除 Element Plus 内部坍塌或不均等 margin
    }

    .btn-action {
      margin-left: 0 !important;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .filter-badge {
      margin-left: 6px;
    }

    .strategy-dropdown-btn {
      border-color: #86efac;
      color: #15803d;
      background: #f0fdf4;
      &:hover {
        background: #dcfce7;
        border-color: #4ade80;
        color: #166534;
      }
    }

    .btn-divider {
      width: 1px;
      height: 22px;
      background: #e2e8f0;
      margin: 0 4px;
    }

    .btn-reset {
      color: #64748b;
      border-color: #cbd5e1;
      &:hover {
        color: #ef4444;
        border-color: #fca5a5;
        background: #fef2f2;
      }
    }
  }
}
</style>

<style lang="scss">
.strategy-dropdown-menu {
  min-width: 200px;
  .dropdown-group-header {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    padding: 6px 16px 4px 16px;
    user-select: none;
    letter-spacing: 0.5px;
  }
  .header-divider {
    border-top: 1px solid #f1f5f9;
    margin-top: 4px;
    padding-top: 8px;
  }
  .action-highlight {
    color: #2563eb;
    font-weight: 600;
  }
  .strategy-menu-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 8px;

    .mini-tag {
      font-size: 10px;
      padding: 0 4px;
      height: 18px;
      line-height: 16px;
    }
  }
}
</style>
