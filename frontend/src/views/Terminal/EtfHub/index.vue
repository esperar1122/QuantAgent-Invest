<template>
  <div class="etf-hub-view">
    <!-- 1. 顶部控制栏与宏观状态 -->
    <div class="etf-header-ribbon">
      <div class="ribbon-brand">
        <div class="pulse-indicator"></div>
        <div class="brand-text">
          <span class="title">场内 ETF 全景专区</span>
          <span class="subtitle">ON-EXCHANGE ETF RADAR · 毫秒级极速切片聚合</span>
        </div>
      </div>

      <div class="ribbon-actions">
        <!-- 自动刷新计时器提示 -->
        <span class="refresh-indicator tabular-nums">
          <span class="refresh-dot"></span>
          实盘自动轮询 · {{ autoRefreshCounter }}s
        </span>

        <!-- 手动刷新按钮 -->
        <el-button 
          size="small" 
          class="action-btn" 
          :loading="loading" 
          @click="fetchData(true)"
        >
          <el-icon><RefreshRight /></el-icon>
          <span>立即刷新</span>
        </el-button>
      </div>
    </div>

    <!-- 2. 全景宏观 KPI 指征栏 -->
    <div class="etf-macro-strip" v-loading="loading && !etfItems.length">
      <!-- KPI 1: 市场涨跌分布 -->
      <div class="macro-card">
        <div class="card-label">标的涨跌分布</div>
        <div class="ratio-numbers tabular-nums">
          <span class="num up">涨 {{ summary.up_count || 0 }}</span>
          <span class="num flat">平 {{ summary.flat_count || 0 }}</span>
          <span class="num down">跌 {{ summary.down_count || 0 }}</span>
        </div>
        <div class="distribution-bar">
          <div 
            class="seg up" 
            :style="{ width: `${getRatioPercent(summary.up_count)}%` }"
          ></div>
          <div 
            class="seg flat" 
            :style="{ width: `${getRatioPercent(summary.flat_count)}%` }"
          ></div>
          <div 
            class="seg down" 
            :style="{ width: `${getRatioPercent(summary.down_count)}%` }"
          ></div>
        </div>
      </div>

      <!-- KPI 2: 全场成交额 -->
      <div class="macro-card">
        <div class="card-label">场内核心成交额</div>
        <div class="card-value tabular-nums highlight">
          {{ summary.total_amount_yi ? summary.total_amount_yi.toFixed(1) : '0.0' }} <span class="unit">亿元</span>
        </div>
        <div class="card-subtext">样本总数 {{ summary.total_count || 0 }} 只主流标的</div>
      </div>

      <!-- KPI 3: 平均涨跌幅 -->
      <div class="macro-card">
        <div class="card-label">场内加权平均表现</div>
        <div 
          class="card-value tabular-nums" 
          :class="(summary.avg_change_pct || 0) >= 0 ? 'color-up' : 'color-down'"
        >
          {{ (summary.avg_change_pct || 0) >= 0 ? '+' : '' }}{{ (summary.avg_change_pct || 0).toFixed(2) }}%
        </div>
        <div class="card-subtext">更新于 {{ summary.updated_at ? summary.updated_at.split(' ')[1] : '--' }}</div>
      </div>

      <!-- KPI 4: 领涨先锋板块 -->
      <div class="macro-card top-leaders">
        <div class="card-label">🔥 今日领涨先锋</div>
        <div class="leaders-list">
          <div 
            v-for="(item, idx) in (summary.top_gainers || []).slice(0, 2)" 
            :key="item.code" 
            class="leader-row"
            @click="navToResearch(item.code)"
          >
            <span class="leader-rank">{{ idx + 1 }}</span>
            <span class="leader-name">{{ item.name }}</span>
            <span class="leader-pct tabular-nums color-up">+{{ item.pct_chg.toFixed(2) }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 分类切换与检索筛选栏 -->
    <div class="filter-controls-row">
      <!-- 分类标签页 -->
      <div class="category-tabs">
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="cat-tab-btn"
          :class="{ active: currentCategory === cat.id }"
          @click="currentCategory = cat.id"
        >
          <span class="cat-name">{{ cat.name }}</span>
          <span class="cat-count tabular-nums">{{ cat.count }}</span>
        </button>
      </div>

      <!-- 搜索与视图切换 -->
      <div class="filter-actions">
        <el-input
          v-model="searchQuery"
          placeholder="快速搜索代码 / 名称 / 标签 (如 562590、半导体、黄金)..."
          :prefix-icon="Search"
          clearable
          size="small"
          class="etf-search-input"
        />

        <el-select v-model="sortBy" size="small" class="sort-select" placeholder="排序方式">
          <el-option label="按涨跌幅降序 ▾" value="pct_desc" />
          <el-option label="按涨跌幅升序 ▴" value="pct_asc" />
          <el-option label="按成交额降序 ▾" value="amount_desc" />
          <el-option label="按现价降序 ▾" value="price_desc" />
        </el-select>

        <div class="view-mode-toggle">
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'grid' }" 
            @click="viewMode = 'grid'" 
            title="卡片网格视图"
          >
            <el-icon><Menu /></el-icon>
          </button>
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'table' }" 
            @click="viewMode = 'table'" 
            title="密集表格视图"
          >
            <el-icon><List /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- 4.1 卡片网格视图 (Grid View) -->
    <div v-if="viewMode === 'grid'" class="etf-cards-grid" v-loading="loading && !filteredItems.length">
      <div 
        v-for="etf in filteredItems" 
        :key="etf.code" 
        class="etf-card"
        :class="{ 'is-up': etf.pct_chg > 0, 'is-down': etf.pct_chg < 0 }"
        @click="navToResearch(etf.code)"
      >
        <!-- 卡片头部：名称、代码、标签 -->
        <div class="card-head">
          <div class="identity-cluster">
            <span class="etf-name" :title="etf.name">{{ etf.name }}</span>
            <div class="sub-codes">
              <span class="etf-code font-mono">{{ etf.code }}</span>
              <span class="market-pill">{{ etf.code.startsWith('15') || etf.code.startsWith('16') ? 'SZ' : 'SH' }}</span>
              <span class="category-pill">{{ etf.category_name }}</span>
            </div>
          </div>
          <el-tag size="small" effect="dark" class="tag-badge">{{ etf.tag }}</el-tag>
        </div>

        <!-- 价格与涨跌幅主显示 (3位小数千分位) -->
        <div class="price-display-cluster">
          <span 
            class="main-price tabular-nums font-mono"
            :class="etf.pct_chg >= 0 ? 'color-up' : 'color-down'"
          >
            ¥{{ etf.price.toFixed(3) }}
          </span>

          <div 
            class="chg-badge tabular-nums font-mono"
            :class="etf.pct_chg >= 0 ? 'badge-up' : 'badge-down'"
          >
            <span class="arrow">{{ etf.pct_chg >= 0 ? '▲' : '▼' }}</span>
            <span class="val">{{ etf.pct_chg >= 0 ? '+' : '' }}{{ etf.pct_chg.toFixed(2) }}%</span>
          </div>
        </div>

        <!-- 四项数据条 -->
        <div class="stats-row">
          <div class="stat-col">
            <span class="lbl">成交额</span>
            <span class="val tabular-nums">{{ etf.amount >= 1 ? `${etf.amount.toFixed(1)}亿` : `${(etf.amount * 10000).toFixed(0)}万` }}</span>
          </div>
          <div class="stat-col">
            <span class="lbl">成交量</span>
            <span class="val tabular-nums">{{ (etf.volume / 10000).toFixed(1) }}万手</span>
          </div>
          <div class="stat-col">
            <span class="lbl">预估规模</span>
            <span class="val tabular-nums">{{ etf.fund_scale ? `${etf.fund_scale.toFixed(0)}亿` : '--' }}</span>
          </div>
          <div class="stat-col">
            <span class="lbl">换手率</span>
            <span class="val tabular-nums">{{ etf.turnover_rate.toFixed(2) }}%</span>
          </div>
        </div>

        <!-- 底部快捷动作 -->
        <div class="card-footer-actions" @click.stop>
          <el-button 
            size="small" 
            type="primary" 
            class="research-btn"
            @click="navToResearch(etf.code)"
          >
            <el-icon><TrendCharts /></el-icon>
            <span>深度投研 ↗</span>
          </el-button>
          <el-button 
            size="small" 
            class="fav-btn"
            :class="{ 'is-fav': isFavorited(etf.code) }"
            @click="toggleFavorite(etf)"
          >
            <el-icon><StarFilled v-if="isFavorited(etf.code)" /><Star v-else /></el-icon>
            <span>{{ isFavorited(etf.code) ? '已自选' : '加自选' }}</span>
          </el-button>
        </div>
      </div>

      <div v-if="filteredItems.length === 0 && !loading" class="empty-state">
        <el-empty description="未匹配到相关场内 ETF，请尝试其他关键词" />
      </div>
    </div>

    <!-- 4.2 密集表格视图 (Dense Table View) -->
    <div v-else class="etf-table-container" v-loading="loading && !filteredItems.length">
      <el-table 
        :data="filteredItems" 
        style="width: 100%" 
        class="terminal-dense-table"
        @row-click="(row) => navToResearch(row.code)"
      >
        <el-table-column label="代码" width="105">
          <template #default="{ row }">
            <span class="font-mono font-bold text-primary">{{ row.code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="基金名称" min-width="160">
          <template #default="{ row }">
            <div class="table-name-wrap">
              <span class="table-fund-name font-bold">{{ row.name }}</span>
              <el-tag size="small" effect="plain" class="table-tag">{{ row.tag }}</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="所属板块" width="110">
          <template #default="{ row }">
            <el-tag size="small" effect="dark" type="info">{{ row.category_name }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="现价 (¥)" width="115" align="right">
          <template #default="{ row }">
            <span 
              class="font-mono font-bold tabular-nums"
              :class="row.pct_chg >= 0 ? 'color-up' : 'color-down'"
            >
              {{ row.price.toFixed(3) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="涨跌幅" width="115" align="right">
          <template #default="{ row }">
            <span 
              class="font-mono font-bold tabular-nums"
              :class="row.pct_chg >= 0 ? 'color-up' : 'color-down'"
            >
              {{ row.pct_chg >= 0 ? '+' : '' }}{{ row.pct_chg.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>

        <el-table-column label="涨跌额" width="100" align="right">
          <template #default="{ row }">
            <span 
              class="font-mono tabular-nums"
              :class="row.change >= 0 ? 'color-up' : 'color-down'"
            >
              {{ row.change >= 0 ? '+' : '' }}{{ row.change.toFixed(3) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="成交额 (亿)" width="120" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums">{{ row.amount.toFixed(2) }} 亿</span>
          </template>
        </el-table-column>

        <el-table-column label="预估规模" width="115" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums">{{ row.fund_scale ? `${row.fund_scale.toFixed(0)} 亿` : '--' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="换手率" width="100" align="right">
          <template #default="{ row }">
            <span class="font-mono tabular-nums">{{ row.turnover_rate.toFixed(2) }}%</span>
          </template>
        </el-table-column>

        <el-table-column label="投研操作" width="190" align="center" fixed="right">
          <template #default="{ row }">
            <div class="table-actions-cell" @click.stop>
              <el-button 
                size="small" 
                type="primary" 
                link
                @click="navToResearch(row.code)"
              >
                分时 / K线 ↗
              </el-button>
              <el-button 
                size="small" 
                link
                :type="isFavorited(row.code) ? 'warning' : 'default'"
                @click="toggleFavorite(row)"
              >
                {{ isFavorited(row.code) ? '★ 已选' : '☆ 自选' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  RefreshRight,
  Search,
  Menu,
  List,
  TrendCharts,
  Star,
  StarFilled
} from '@element-plus/icons-vue'
import { stocksApi } from '@/api/stocks'
import { useFavoritesStore } from '@/stores/favorites'

const router = useRouter()
const favoritesStore = useFavoritesStore()

const loading = ref(false)
const viewMode = ref<'grid' | 'table'>('grid')
const currentCategory = ref<string>('all')
const searchQuery = ref<string>('')
const sortBy = ref<string>('pct_desc')

const summary = ref<any>({
  total_count: 0,
  up_count: 0,
  down_count: 0,
  flat_count: 0,
  total_amount_yi: 0,
  avg_change_pct: 0,
  top_gainers: [],
  top_volume: [],
  updated_at: ''
})

const categories = ref<Array<{ id: string; name: string; count: number }>>([
  { id: 'all', name: '全部热门', count: 0 },
  { id: 'broad', name: '核心宽基', count: 0 },
  { id: 'tech', name: '硬核科技', count: 0 },
  { id: 'industry', name: '制造周期', count: 0 },
  { id: 'macro', name: '大类跨境', count: 0 }
])

const etfItems = ref<any[]>([])

// 自动轮询计时器
const autoRefreshCounter = ref(5)
let timer: any = null
let counterTimer: any = null

async function fetchData(force = false) {
  loading.value = true
  try {
    const res = await stocksApi.getEtfOverview(force)
    const d = (res as any)?.data || res
    if (d) {
      if (d.summary) summary.value = d.summary
      if (d.categories) categories.value = d.categories
      if (Array.isArray(d.items)) etfItems.value = d.items
    }
  } catch (err) {
    console.error('获取ETF实时行情异常:', err)
  } finally {
    loading.value = false
    autoRefreshCounter.value = 5
  }
}

// 筛选与排序
const filteredItems = computed(() => {
  let list = [...etfItems.value]

  // 1. 分类筛选
  if (currentCategory.value !== 'all') {
    list = list.filter(item => item.category === currentCategory.value)
  }

  // 2. 文本搜索
  const kw = searchQuery.value.trim().toLowerCase()
  if (kw) {
    list = list.filter(item => 
      item.code.toLowerCase().includes(kw) ||
      item.name.toLowerCase().includes(kw) ||
      (item.tag && item.tag.toLowerCase().includes(kw))
    )
  }

  // 3. 排序
  if (sortBy.value === 'pct_desc') {
    list.sort((a, b) => b.pct_chg - a.pct_chg)
  } else if (sortBy.value === 'pct_asc') {
    list.sort((a, b) => a.pct_chg - b.pct_chg)
  } else if (sortBy.value === 'amount_desc') {
    list.sort((a, b) => b.amount - a.amount)
  } else if (sortBy.value === 'price_desc') {
    list.sort((a, b) => b.price - a.price)
  }

  return list
})

function getRatioPercent(count: number = 0): number {
  const total = summary.value.total_count || 1
  return Math.round((count / total) * 100)
}

function navToResearch(code: string) {
  router.push({
    path: '/terminal/stock',
    query: { code }
  })
}

function isFavorited(code: string): boolean {
  return favoritesStore.favorites.some(
    fav => fav.symbol === code || fav.stock_code === code
  )
}

async function toggleFavorite(etf: any) {
  const code = etf.code
  if (isFavorited(code)) {
    await favoritesStore.removeFavorite(code)
    ElMessage.info(`已将 ${etf.name} 移出自选池`)
  } else {
    await favoritesStore.addFavorite({
      stock_code: code,
      stock_name: etf.name,
      symbol: code
    })
    ElMessage.success(`已将 ${etf.name} 加入自选池`)
  }
}

onMounted(() => {
  favoritesStore.fetchFavorites()
  fetchData()

  // 倒计时与轮询
  counterTimer = setInterval(() => {
    if (autoRefreshCounter.value > 1) {
      autoRefreshCounter.value--
    } else {
      fetchData()
    }
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (counterTimer) clearInterval(counterTimer)
})
</script>

<style scoped>
.etf-hub-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px;
  min-height: 100%;
  color: #e2e8f0;
}

/* 1. 顶部控制栏 */
.etf-header-ribbon {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  backdrop-filter: blur(12px);
}

.ribbon-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pulse-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 10px #3b82f6;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  70% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
  100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-text .title {
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0.5px;
}

.brand-text .subtitle {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 0.8px;
  margin-top: 1px;
}

.ribbon-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.refresh-indicator {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}

.refresh-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

/* 2. 宏观指征栏 */
.etf-macro-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.macro-card {
  padding: 14px 16px;
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.macro-card .card-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}

.ratio-numbers {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}

.ratio-numbers .up { color: #f43f5e; }
.ratio-numbers .flat { color: #94a3b8; }
.ratio-numbers .down { color: #10b981; }

.distribution-bar {
  display: flex;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.distribution-bar .seg.up { background: #f43f5e; }
.distribution-bar .seg.flat { background: #64748b; }
.distribution-bar .seg.down { background: #10b981; }

.macro-card .card-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}

.macro-card .card-value .unit {
  font-size: 13px;
  font-weight: normal;
  color: #94a3b8;
}

.macro-card .card-subtext {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}

.macro-card.top-leaders .leaders-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.leader-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.leader-row:hover {
  background: rgba(255, 255, 255, 0.06);
}

.leader-rank {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(244, 63, 94, 0.15);
  color: #f43f5e;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.leader-name {
  color: #cbd5e1;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 3. 筛选与分类切换 */
.filter-controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.category-tabs {
  display: flex;
  gap: 8px;
}

.cat-tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(30, 41, 59, 0.5);
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cat-tab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
}

.cat-tab-btn.active {
  background: #2563eb;
  border-color: #3b82f6;
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
}

.cat-count {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.25);
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.etf-search-input {
  width: 280px;
}

.sort-select {
  width: 140px;
}

.view-mode-toggle {
  display: flex;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 2px;
}

.toggle-btn {
  background: transparent;
  border: none;
  color: #64748b;
  padding: 5px 8px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.15s ease;
}

.toggle-btn.active {
  background: #334155;
  color: #38bdf8;
}

/* 4. 网格视图 */
.etf-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
}

.etf-card {
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.etf-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  background: rgba(30, 41, 59, 0.7);
}

.etf-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  transition: background 0.2s ease;
}

.etf-card.is-up::before { background: #f43f5e; }
.etf-card.is-down::before { background: #10b981; }

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.identity-cluster {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.etf-name {
  font-size: 14px;
  font-weight: 700;
  color: #f1f5f9;
}

.sub-codes {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.etf-code {
  color: #94a3b8;
}

.market-pill {
  font-size: 10px;
  padding: 0 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
}

.category-pill {
  font-size: 10px;
  color: #64748b;
}

.tag-badge {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #60a5fa !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

.price-display-cluster {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 4px 0;
}

.main-price {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.chg-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
}

.chg-badge.badge-up {
  background: rgba(244, 63, 94, 0.16);
  color: #f43f5e;
}

.chg-badge.badge-down {
  background: rgba(16, 185, 129, 0.16);
  color: #10b981;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.stat-col {
  display: flex;
  flex-direction: column;
}

.stat-col .lbl {
  font-size: 10px;
  color: #64748b;
}

.stat-col .val {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  margin-top: 1px;
}

.card-footer-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.research-btn {
  flex: 1;
  background: #2563eb !important;
  border-color: #3b82f6 !important;
  font-weight: 600;
}

.fav-btn {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #cbd5e1 !important;
}

.fav-btn.is-fav {
  color: #f59e0b !important;
  border-color: rgba(245, 158, 11, 0.3) !important;
}

/* 5. 密集表格 */
.etf-table-container {
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
}

.table-name-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-fund-name {
  color: #f8fafc;
}

.table-tag {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #60a5fa !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.table-actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 通用配色 */
.color-up { color: #f43f5e !important; }
.color-down { color: #10b981 !important; }

@media (max-width: 1024px) {
  .etf-macro-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
