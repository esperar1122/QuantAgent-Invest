<template>
  <div class="stock-pool-container">
    <!-- 页面标题与顶部介绍 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon class="title-icon"><Collection /></el-icon>
          A股与核心指数股票池 (QuantAgent Universe)
        </h1>
        <p class="page-description">
          全量覆盖全市场在市交易 A 股上市公司标的档案与大盘核心指数，深度融合多因子量化指标、实时行情与多维筛选系统，支持全盘极速检索与一键批量多智能体投研研判。
        </p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="syncing"
          @click="handleTriggerSync"
        >
          <el-icon><RefreshRight /></el-icon>
          {{ syncing ? '正在多源同步...' : '同步最新行情档案' }}
        </el-button>
      </div>
    </div>

    <!-- 顶部全景核心指标卡片 -->
    <StockPoolStats
      :stats="stats"
      :current-market="queryParams.market"
      @quick-filter="quickFilterMarket"
    />

    <!-- 综合筛选与量化控制栏 -->
    <el-card class="filter-card" shadow="never">
      <StockPoolFilterBar
        :params="queryParams"
        :show-advanced="showAdvancedFilter"
        :has-active-advanced="hasActiveAdvancedFilters"
        :active-advanced-count="activeAdvancedCount"
        :custom-strategies="customStrategies"
        :presets="strategyPresets"
        @search="handleSearch"
        @reset="handleReset"
        @toggle-advanced="toggleAdvancedFilter"
        @apply-custom="applyCustomStrategy"
        @apply-preset="applyStrategyPreset"
        @save-current="openCreateStrategy"
        @create-strategy="openCreateStrategy"
        @manage-strategies="openManageStrategies"
      />

      <AdvancedFilterPanel
        :show="showAdvancedFilter"
        :params="queryParams"
        :presets="strategyPresets"
        :custom-strategies="customStrategies"
        :active-tags="activeFilterTags"
        @search="handleSearch"
        @reset-advanced="resetAdvancedFilters"
        @close="showAdvancedFilter = false"
        @apply-preset="applyStrategyPreset"
        @apply-custom="applyCustomStrategy"
        @save-current="openCreateStrategy"
        @create-strategy="openCreateStrategy"
        @edit-strategy="openEditStrategy"
        @delete-strategy="handleDeleteStrategy"
        @manage-strategies="openManageStrategies"
        @remove-tag="removeFilterTag"
        @clear-all="handleReset"
      />
    </el-card>

    <!-- 股票池全量数据表格与交互模态框 -->
    <StockPoolTable
      :stocks="stockList"
      :selected-stocks="selectedStocks"
      :loading="loading"
      :total="total"
      :page="queryParams.page || 1"
      :page-size="queryParams.page_size || 20"
      :is-favorited="isFavorited"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @batch-analyze="handleBatchAnalyze"
      @export-csv="exportCSV"
      @refresh="loadData"
      @analyze="goToAnalysis"
      @toggle-favorite="toggleFavorite"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- 自定义量化选股策略编辑/新建弹窗 -->
    <StrategyEditDialog
      v-model:visible="strategyEditVisible"
      :strategy="currentEditingStrategy"
      :current-params="queryParams"
      @save="handleSaveStrategy"
    />

    <!-- 自定义量化策略库集中管理弹窗 -->
    <StrategyManageDialog
      v-model:visible="strategyManageVisible"
      :strategies="customStrategies"
      @apply="applyCustomStrategy"
      @create="openCreateStrategy"
      @edit="openEditStrategy"
      @delete="handleDeleteStrategy"
      @reset-defaults="resetToDefaultTemplates"
    />
  </div>
</template>

<script setup lang="ts">
import { Collection, RefreshRight } from '@element-plus/icons-vue'
import { useStockPool } from '@/composables/useStockPool'
import StockPoolStats from './components/StockPoolStats.vue'
import StockPoolFilterBar from './components/StockPoolFilterBar.vue'
import AdvancedFilterPanel from './components/AdvancedFilterPanel.vue'
import StockPoolTable from './components/StockPoolTable.vue'
import StrategyEditDialog from './components/StrategyEditDialog.vue'
import StrategyManageDialog from './components/StrategyManageDialog.vue'

const {
  loading,
  syncing,
  showAdvancedFilter,
  stockList,
  selectedStocks,
  total,
  stats,
  queryParams,
  strategyPresets,
  customStrategies,
  resetToDefaultTemplates,
  strategyEditVisible,
  strategyManageVisible,
  currentEditingStrategy,
  openCreateStrategy,
  openEditStrategy,
  openManageStrategies,
  applyCustomStrategy,
  handleSaveStrategy,
  handleDeleteStrategy,
  activeAdvancedCount,
  hasActiveAdvancedFilters,
  activeFilterTags,
  removeFilterTag,
  toggleAdvancedFilter,
  applyStrategyPreset,
  resetAdvancedFilters,
  loadData,
  quickFilterMarket,
  handleSearch,
  handleReset,
  handleSelectionChange,
  handleBatchAnalyze,
  exportCSV,
  isFavorited,
  toggleFavorite,
  handleSizeChange,
  handleCurrentChange,
  handleSortChange,
  goToAnalysis,
  handleTriggerSync
} = useStockPool()
</script>

<style scoped lang="scss">
.stock-pool-container {
  padding: 0;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;

    .header-content {
      .page-title {
        font-size: 24px;
        font-weight: 700;
        color: var(--el-text-color-primary, #0f172a);
        margin: 0 0 8px 0;
        display: flex;
        align-items: center;
        gap: 10px;

        .title-icon {
          color: #2563eb;
          font-size: 26px;
        }
      }

      .page-description {
        font-size: 14px;
        color: var(--el-text-color-secondary, #64748b);
        margin: 0;
        line-height: 1.5;
        max-width: 860px;
      }
    }
  }

  .filter-card {
    border: 1px solid var(--el-border-color-lighter, #e2e8f0);
    border-radius: 12px;
    background: var(--el-bg-color, #ffffff);
    margin-bottom: 20px;
  }
}
</style>
