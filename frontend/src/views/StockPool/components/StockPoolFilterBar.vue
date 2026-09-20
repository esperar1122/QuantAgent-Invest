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

    <el-form-item>
      <el-button type="primary" @click="$emit('search')">
        <el-icon><Search /></el-icon>
        筛选
      </el-button>
      <el-button
        :type="showAdvanced || hasActiveAdvanced ? 'warning' : 'default'"
        :plain="!showAdvanced"
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
      <el-button @click="$emit('reset')">
        <el-icon><Refresh /></el-icon>
        重置
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { Search, Filter, Refresh } from '@element-plus/icons-vue'
import type { StockPoolParams } from '@/api/stocks'

defineProps<{
  params: StockPoolParams
  showAdvanced: boolean
  hasActiveAdvanced: boolean
  activeAdvancedCount: number
}>()

defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
  (e: 'toggle-advanced'): void
}>()
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

  .filter-badge {
    margin-left: 6px;
  }
}
</style>
