<template>
  <el-card class="table-card" shadow="never">
    <div class="table-header-info">
      <span class="info-text">
        共找到 <strong class="highlight-count">{{ total }}</strong> 只符合条件的 A 股标的
        <span v-if="selectedStocks.length > 0" class="selected-badge">
          (已选中 {{ selectedStocks.length }} 只)
        </span>
      </span>

      <div class="table-actions">
        <!-- 批量研判 -->
        <el-button
          type="primary"
          :disabled="selectedStocks.length === 0"
          @click="$emit('batch-analyze')"
        >
          <el-icon><TrendCharts /></el-icon>
          批量智能研判 {{ selectedStocks.length > 0 ? `(${selectedStocks.length})` : '' }}
        </el-button>

        <!-- 导出筛选结果 -->
        <el-button type="success" plain @click="$emit('export-csv')">
          <el-icon><Download /></el-icon>
          导出表格 (CSV)
        </el-button>

        <!-- 刷新 -->
        <el-button size="default" :icon="Refresh" @click="$emit('refresh')">刷新</el-button>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="stocks"
      stripe
      style="width: 100%"
      class="stock-table"
      @selection-change="(selection) => $emit('selection-change', selection)"
      @sort-change="(sort) => $emit('sort-change', sort)"
    >
      <!-- 复选框列 -->
      <el-table-column type="selection" width="50" align="center" fixed="left" />

      <!-- 股票代码 -->
      <el-table-column prop="code" label="代码" width="130" fixed="left" sortable="custom">
        <template #default="{ row }">
          <div class="symbol-col">
            <span class="symbol-code num-tabular">{{ row.code }}</span>
            <el-tag size="small" :type="getExchangeTagType(row.code)" effect="plain" class="exchange-tag">
              {{ getExchangeName(row.code) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 股票名称 (点击查看技术指标与行情) -->
      <el-table-column prop="name" label="名称" width="140" fixed="left">
        <template #default="{ row }">
          <el-tooltip content="点击查看技术指标全景与交互行情" placement="top" :show-after="200">
            <span class="stock-name" @click="openTechnicalModal(row)">{{ row.name || '--' }}</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <!-- 量化综合估值评级 -->
      <el-table-column label="量化估值评级" width="130" align="center">
        <template #default="{ row }">
          <el-tag :type="getValuationTagType(row)" size="small" effect="light" round>
            {{ getValuationRating(row) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 所属板块 -->
      <el-table-column prop="market" label="所属板块" width="100">
        <template #default="{ row }">
          <el-tag :type="getMarketTagType(row.market)" size="small">
            {{ row.market || '主板' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 最新收盘价 / 点位 -->
      <el-table-column prop="close" label="最新价 / 点位" width="130" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.close !== null && row.close !== undefined" :class="getPriceClass(row.pct_chg)" class="num-cell num-tabular bold">
            {{ row.market === '重要指数' ? `${Number(row.close).toFixed(2)} 点` : `¥ ${Number(row.close).toFixed(2)}` }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 日涨跌幅 -->
      <el-table-column prop="pct_chg" label="日涨跌幅" width="120" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.pct_chg !== null && row.pct_chg !== undefined" :class="getPriceBadgeClass(row.pct_chg)" class="num-tabular">
            {{ row.pct_chg > 0 ? '+' : '' }}{{ Number(row.pct_chg).toFixed(2) }}%
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 换手率 -->
      <el-table-column prop="turnover_rate" label="换手率" width="110" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.turnover_rate !== null && row.turnover_rate !== undefined" class="num-cell num-tabular" :class="{ 'text-up': row.turnover_rate >= 5, 'bold': row.turnover_rate >= 3 }">
            {{ Number(row.turnover_rate).toFixed(2) }}%
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 量比 -->
      <el-table-column prop="volume_ratio" label="量比" width="95" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.volume_ratio !== null && row.volume_ratio !== undefined" class="num-cell num-tabular" :class="{ 'text-up': row.volume_ratio >= 2, 'bold': row.volume_ratio >= 1.5 }">
            {{ Number(row.volume_ratio).toFixed(2) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 成交额 -->
      <el-table-column prop="amount" label="成交额" width="125" align="right" sortable="custom">
        <template #default="{ row }">
          <span class="num-cell num-tabular">{{ formatAmount(row.amount) }}</span>
        </template>
      </el-table-column>

      <!-- 流通市值 -->
      <el-table-column prop="circ_mv" label="流通市值" width="115" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.circ_mv !== null && row.circ_mv !== undefined" class="num-cell num-tabular">
            {{ Number(row.circ_mv).toFixed(1) }} 亿
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 市盈率 PE -->
      <el-table-column prop="pe" label="市盈率(PE-TTM)" width="130" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.pe !== null && row.pe !== undefined" class="num-cell num-tabular">
            {{ Number(row.pe).toFixed(2) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 市净率 PB -->
      <el-table-column prop="pb" label="市净率(PB-MRQ)" width="130" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.pb !== null && row.pb !== undefined" class="num-cell num-tabular">
            {{ Number(row.pb).toFixed(2) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 市销率 PS -->
      <el-table-column prop="ps" label="市销率(PS)" width="120" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.ps !== null && row.ps !== undefined" class="num-cell num-tabular">
            {{ Number(row.ps).toFixed(2) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 净资产收益率 ROE -->
      <el-table-column prop="roe" label="ROE(%)" width="115" align="right" sortable="custom">
        <template #default="{ row }">
          <el-tag
            v-if="row.roe !== null && row.roe !== undefined"
            :type="row.roe >= 15 ? 'danger' : row.roe >= 10 ? 'warning' : 'info'"
            size="small"
            effect="light"
            class="num-tabular"
          >
            {{ Number(row.roe).toFixed(2) }}%
          </el-tag>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 净利润同比增长率 -->
      <el-table-column prop="net_profit_growth" label="净利增速" width="115" align="right" sortable="custom">
        <template #default="{ row }">
          <span
            v-if="row.net_profit_growth !== null && row.net_profit_growth !== undefined"
            class="num-cell num-tabular"
            :class="{ 'text-up': row.net_profit_growth > 0, 'bold': row.net_profit_growth >= 30 }"
          >
            {{ row.net_profit_growth > 0 ? '+' : '' }}{{ Number(row.net_profit_growth).toFixed(1) }}%
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 营收同比增长率 -->
      <el-table-column prop="revenue_growth" label="营收增速" width="115" align="right" sortable="custom">
        <template #default="{ row }">
          <span
            v-if="row.revenue_growth !== null && row.revenue_growth !== undefined"
            class="num-cell num-tabular"
            :class="{ 'text-up': row.revenue_growth > 0, 'bold': row.revenue_growth >= 20 }"
          >
            {{ row.revenue_growth > 0 ? '+' : '' }}{{ Number(row.revenue_growth).toFixed(1) }}%
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 销售毛利率 -->
      <el-table-column prop="gross_margin" label="毛利率" width="110" align="right" sortable="custom">
        <template #default="{ row }">
          <span v-if="row.gross_margin !== null && row.gross_margin !== undefined" class="num-cell num-tabular">
            {{ Number(row.gross_margin).toFixed(1) }}%
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>

      <!-- 数据源 -->
      <el-table-column prop="source" label="数据源" width="110" align="center">
        <template #default="{ row }">
          <el-tag size="small" type="info" effect="plain">
            {{ formatSource(row.source) }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 交易日 -->
      <el-table-column prop="trade_date" label="最新交易日" width="120" align="center">
        <template #default="{ row }">
          <span class="trade-date-text num-tabular">{{ formatTradeDate(row.trade_date) }}</span>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作与研判" min-width="170" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              type="primary"
              size="small"
              class="analyze-btn"
              @click="$emit('analyze', row)"
            >
              <el-icon><Cpu /></el-icon>
              智能研判
            </el-button>
            <el-tooltip :content="isFavorited(row.code) ? '取消自选' : '加入自选'" placement="top">
              <el-button
                size="small"
                :type="isFavorited(row.code) ? 'warning' : 'default'"
                :class="{ 'favorited-btn': isFavorited(row.code) }"
                @click="$emit('toggle-favorite', row)"
              >
                <el-icon><Star /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页控制 -->
    <div class="pagination-wrapper">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="(val) => $emit('size-change', val)"
        @current-change="(val) => $emit('current-change', val)"
      />
    </div>

    <!-- 技术指标全景诊断与交互行情弹窗 -->
    <TechnicalAnalysisModal ref="technicalModalRef" />
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { TrendCharts, Download, Refresh, Cpu, Star } from '@element-plus/icons-vue'
import type { StockPoolItem } from '@/api/stocks'
import TechnicalAnalysisModal from '@/components/TechnicalIndicators/TechnicalAnalysisModal.vue'

defineProps<{
  stocks: StockPoolItem[]
  selectedStocks: StockPoolItem[]
  loading: boolean
  total: number
  page?: number
  pageSize?: number
  isFavorited: (code: string) => boolean
}>()

defineEmits<{
  (e: 'selection-change', selection: StockPoolItem[]): void
  (e: 'sort-change', sort: { prop: string; order: string | null }): void
  (e: 'batch-analyze'): void
  (e: 'export-csv'): void
  (e: 'refresh'): void
  (e: 'analyze', row: StockPoolItem): void
  (e: 'toggle-favorite', row: StockPoolItem): void
  (e: 'size-change', val: number): void
  (e: 'current-change', val: number): void
}>()

const technicalModalRef = ref<InstanceType<typeof TechnicalAnalysisModal> | null>(null)

const openTechnicalModal = (row: StockPoolItem) => {
  technicalModalRef.value?.open(row.code, row.name)
}

// 辅助量化评级计算
const getValuationRating = (row: StockPoolItem) => {
  if (row.market === '重要指数' || row.is_index) return '📊 基准指数'
  const pe = row.pe
  const pb = row.pb
  if (pe === null || pe === undefined || pe <= 0) return '成长观察'
  if (pe < 15 && (pb ?? 1) < 1.8) return '💎 优质低估'
  if (pe < 25) return '⚖️ 估值适中'
  if (pe < 50) return '📈 高成长'
  return '⚠️ 偏高估'
}

const getValuationTagType = (row: StockPoolItem) => {
  if (row.market === '重要指数' || row.is_index) return 'danger'
  const pe = row.pe
  if (pe === null || pe === undefined || pe <= 0) return 'info'
  if (pe < 15) return 'success'
  if (pe < 25) return 'primary'
  if (pe < 50) return 'warning'
  return 'danger'
}

const getExchangeTagType = (code: string) => {
  const c = code.toLowerCase()
  if (c.startsWith('sh') || c.startsWith('6')) return 'primary'
  if (c.startsWith('sz') || c.startsWith('0') || c.startsWith('3') || c.startsWith('9')) return 'success'
  return 'warning'
}

const getExchangeName = (code: string) => {
  const c = code.toLowerCase()
  if (c.startsWith('sh') || c.startsWith('6')) return 'SH'
  if (c.startsWith('sz') || c.startsWith('0') || c.startsWith('3') || c.startsWith('9')) return 'SZ'
  return 'BJ'
}

const getMarketTagType = (market: string) => {
  switch (market) {
    case '重要指数': return 'danger'
    case '科创板': return 'danger'
    case '创业板': return 'warning'
    case '北交所': return 'info'
    default: return 'primary'
  }
}

const getPriceClass = (pct_chg?: number | null) => {
  if (pct_chg === undefined || pct_chg === null) return ''
  return pct_chg > 0 ? 'text-up' : pct_chg < 0 ? 'text-down' : 'text-flat'
}

const getPriceBadgeClass = (pct_chg?: number | null) => {
  if (pct_chg === undefined || pct_chg === null) return 'badge-flat'
  return pct_chg > 0 ? 'badge-up' : pct_chg < 0 ? 'badge-down' : 'badge-flat'
}

const formatAmount = (amount?: number | null) => {
  if (amount === undefined || amount === null) return '--'
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)} 亿`
  }
  if (amount >= 10000) {
    return `${(amount / 10000).toFixed(1)} 万`
  }
  return `${amount.toFixed(0)} 元`
}

const formatSource = (source?: string) => {
  if (!source) return '本地缓存'
  const map: Record<string, string> = {
    baostock: 'BaoStock',
    akshare: 'AKShare',
    tushare: 'Tushare',
    mongodb_cache: '本地缓存'
  }
  return map[source] || source
}

const formatTradeDate = (d?: string) => {
  if (!d) return '--'
  if (d.length === 8) {
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
  }
  return d
}
</script>

<style scoped lang="scss">
.table-card {
  border: 1px solid var(--el-border-color-lighter, #e2e8f0);
  border-radius: 12px;
  background: var(--el-bg-color, #ffffff);

  .table-header-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;

    .info-text {
      font-size: 14px;
      color: var(--el-text-color-regular, #475569);

      .highlight-count {
        color: #2563eb;
        font-weight: 700;
        font-size: 16px;
      }

      .selected-badge {
        color: #d97706;
        font-weight: 600;
        margin-left: 8px;
      }
    }

    .table-actions {
      display: flex;
      gap: 10px;
    }
  }

  .stock-table {
    border-radius: 8px;
    overflow: hidden;

    .symbol-col {
      display: flex;
      align-items: center;
      gap: 6px;

      .symbol-code {
        font-weight: 600;
        color: var(--el-text-color-primary, #1e293b);
      }

      .exchange-tag {
        font-size: 10px;
        padding: 0 4px;
        height: 18px;
        line-height: 18px;
      }
    }

    .stock-name {
      font-weight: 600;
      color: #2563eb;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-block;

      &:hover {
        color: #1d4ed8;
        text-decoration: underline;
        transform: scale(1.02);
      }
    }

    .num-cell {
      font-size: 13px;
      color: var(--el-text-color-primary, #1e293b);

      &.bold { font-weight: 600; }
    }

    .text-up { color: var(--qa-stock-up, #ef4444); }
    .text-down { color: var(--qa-stock-down, #16a34a); }
    .text-flat { color: var(--qa-stock-flat, #64748b); }
    .text-muted { color: var(--el-text-color-secondary, #94a3b8); }

    .badge-up {
      background: var(--qa-stock-up-bg, #fef2f2);
      color: var(--qa-stock-up, #ef4444);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
      border: 1px solid var(--qa-stock-up-border, rgba(239, 68, 68, 0.2));
    }

    .badge-down {
      background: var(--qa-stock-down-bg, #f0fdf4);
      color: var(--qa-stock-down, #16a34a);
      padding: 2px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 12px;
      border: 1px solid var(--qa-stock-down-border, rgba(22, 163, 74, 0.2));
    }

    .badge-flat {
      background: var(--el-fill-color-light, #f8fafc);
      color: var(--qa-stock-flat, #64748b);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
    }

    .trade-date-text {
      color: var(--el-text-color-secondary, #64748b);
      font-size: 12px;
    }

    .action-buttons {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;

      .analyze-btn {
        font-weight: 500;
      }

      .favorited-btn {
        background: #fbbf24;
        border-color: #f59e0b;
        color: #fff;
      }
    }
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
