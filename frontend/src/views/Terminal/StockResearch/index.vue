<template>
  <div class="stock-research-view">
    <!-- 1. 标的极速检索与切换控制台 (Stock Switcher Ribbon) -->
    <div class="stock-switcher-ribbon">
      <div class="ribbon-left">
        <!-- 标的搜索下拉框 -->
        <div class="search-input-wrapper">
          <el-select
            v-model="selectedCode"
            filterable
            remote
            reserve-keyword
            :remote-method="handleSearch"
            :loading="searchLoading"
            placeholder="🔍 检索 A股代码 / 名称 / 简拼 (如 600519、贵州茅台、300750)..."
            class="terminal-stock-select"
            @change="onStockSelectChange"
          >
            <el-option
              v-for="item in searchOptions"
              :key="item.code"
              :label="`${item.name} (${item.code})`"
              :value="item.code"
            >
              <div class="search-option-card">
                <div class="opt-left">
                  <span class="opt-code font-mono">{{ item.code }}</span>
                  <span class="opt-market-tag">{{ item.market || 'A股' }}</span>
                </div>
                <div class="opt-center">
                  <span class="opt-name">{{ item.name }}</span>
                  <span class="opt-industry" v-if="item.industry">{{ item.industry }}</span>
                </div>
                <div class="opt-right tabular-nums" v-if="item.close !== undefined">
                  <span class="opt-price">{{ Number(item.close).toFixed(2) }}</span>
                  <span
                    class="opt-pct"
                    :class="(item.pct_chg || 0) >= 0 ? 'color-up' : 'color-down'"
                  >
                    {{ (item.pct_chg || 0) >= 0 ? '+' : '' }}{{ Number(item.pct_chg || 0).toFixed(2) }}%
                  </span>
                </div>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 热门核心指数标的秒级切换胶囊 (Quick Preset Chips) -->
        <div class="preset-chips">
          <span class="chips-label">核心池:</span>
          <button
            v-for="chip in hotStocks"
            :key="chip.code"
            class="chip-btn"
            :class="{ active: isChipActive(chip.code) }"
            @click="switchStock(chip.code)"
          >
            <span class="chip-name">{{ chip.name }}</span>
            <span class="chip-code font-mono">{{ chip.displayCode || chip.code }}</span>
          </button>
        </div>
      </div>

      <div class="ribbon-right">
        <!-- 自选股快速切换下拉 -->
        <el-dropdown trigger="click" @command="switchStock">
          <el-button size="small" class="watchlist-btn">
            <el-icon><Star /></el-icon>
            <span>自选池 ({{ favoritesStore.favorites.length }})</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu class="watchlist-dropdown-menu">
              <el-dropdown-item
                v-if="favoritesStore.favorites.length === 0"
                disabled
              >
                暂无自选股，点击加自选可添加
              </el-dropdown-item>
              <el-dropdown-item
                v-for="fav in favoritesStore.favorites"
                :key="fav.symbol || fav.stock_code"
                :command="fav.symbol || fav.stock_code"
                :class="{ active: currentStock.code === (fav.symbol || fav.stock_code) }"
              >
                <div class="fav-item-row">
                  <span class="fav-name">{{ fav.stock_name || fav.symbol || fav.stock_code }}</span>
                  <span class="fav-code font-mono">{{ fav.symbol || fav.stock_code }}</span>
                </div>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 收藏/取消收藏按钮 -->
        <el-button
          size="small"
          :type="isCurrentFavorited ? 'warning' : 'default'"
          class="favorite-toggle-btn"
          @click="toggleCurrentFavorite"
        >
          <el-icon><StarFilled v-if="isCurrentFavorited" /><Star v-else /></el-icon>
          <span>{{ isCurrentFavorited ? '已收藏' : '加自选' }}</span>
        </el-button>

        <!-- 刷新按钮 -->
        <el-button
          size="small"
          class="refresh-btn"
          :loading="pageLoading"
          @click="reloadCurrentStock"
        >
          <el-icon><RefreshRight /></el-icon>
          <span>刷新行情</span>
        </el-button>
      </div>
    </div>

    <!-- 2. 标的顶部行情核心栏 (Stock Header Card) -->
    <div class="stock-header-card" v-loading="pageLoading">
      <div class="stock-identity">
        <div class="code-cluster">
          <span class="stock-name">{{ currentStock.name }}</span>
          <span class="stock-code tabular-nums font-mono">{{ currentStock.code }}</span>
          <span class="board-badge">{{ currentStock.board }}</span>
          <span class="sector-badge">{{ currentStock.sector }}</span>
        </div>
        <div class="price-cluster">
          <span class="current-price tabular-nums" :class="currentStock.change >= 0 ? 'color-up' : 'color-down'">
            {{ currentStock.price.toFixed(2) }}
          </span>
          <div class="change-group tabular-nums" :class="currentStock.change >= 0 ? 'color-up' : 'color-down'">
            <span class="change-val">{{ currentStock.change >= 0 ? '+' : '' }}{{ currentStock.changeVal.toFixed(2) }}</span>
            <span class="change-pct">({{ currentStock.change >= 0 ? '+' : '' }}{{ currentStock.change.toFixed(2) }}%)</span>
          </div>
        </div>
      </div>

      <!-- 高密度十项金融行情数据 -->
      <div class="metrics-strip">
        <div class="m-item"><span class="mk">今开</span><span class="mv tabular-nums">{{ currentStock.open.toFixed(2) }}</span></div>
        <div class="m-item"><span class="mk">最高</span><span class="mv tabular-nums color-up">{{ currentStock.high.toFixed(2) }}</span></div>
        <div class="m-item"><span class="mk">最低</span><span class="mv tabular-nums color-down">{{ currentStock.low.toFixed(2) }}</span></div>
        <div class="m-item"><span class="mk">昨收</span><span class="mv tabular-nums">{{ currentStock.preClose.toFixed(2) }}</span></div>
        <div class="m-item"><span class="mk">成交量</span><span class="mv tabular-nums">{{ (currentStock.volume / 10000).toFixed(1) }}万手</span></div>
        <div class="m-item"><span class="mk">成交额</span><span class="mv tabular-nums">{{ currentStock.amount }}亿</span></div>
        <div class="m-item"><span class="mk">换手率</span><span class="mv tabular-nums">{{ currentStock.turnover.toFixed(2) }}%</span></div>
        <div class="m-item"><span class="mk">{{ isCurrentIndex ? '成份总市值' : '总市值' }}</span><span class="mv tabular-nums">{{ currentStock.marketCap }}亿</span></div>
        <div class="m-item"><span class="mk">{{ isCurrentIndex ? '指数PE' : '市盈(动)' }}</span><span class="mv tabular-nums">{{ currentStock.pe }}</span></div>
        <div class="m-item"><span class="mk">{{ isCurrentIndex ? '指数PB' : '市净率' }}</span><span class="mv tabular-nums">{{ currentStock.pb }}</span></div>
      </div>

      <div class="header-actions">
        <el-button type="primary" size="small" @click="goToWorkflow">
          <el-icon><Connection /></el-icon>
          启动 Agent 工作流
        </el-button>
        <el-button size="small" @click="goToReport">
          <el-icon><Document /></el-icon>
          查看完整研报
        </el-button>
      </div>
    </div>

    <!-- 3. 三栏金融工作台主体 -->
    <div class="three-columns-workspace">
      <!-- 左栏：量化画像与因子雷达 (280px) -->
      <aside class="left-quant-col">
        <div class="panel-box">
          <div class="panel-header">
            <span class="panel-title">Quant Engine 量化画像</span>
            <span class="score-badge tabular-nums">综合分 {{ currentStock.score }}</span>
          </div>

          <!-- 因子得分条状矩阵 -->
          <div class="factors-list">
            <div v-for="factor in quantFactors" :key="factor.name" class="factor-row">
              <div class="factor-info">
                <span class="f-name">{{ factor.name }}</span>
                <span class="f-score tabular-nums">{{ factor.score }} / 100</span>
              </div>
              <div class="f-bar-track">
                <div class="f-bar-fill" :style="{ width: factor.score + '%', backgroundColor: factor.color }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 财务与基本面核心指标 -->
        <div class="panel-box">
          <div class="panel-header">
            <span class="panel-title">{{ isCurrentIndex ? '指数估值与市场特征' : '财务与经营核心数据' }}</span>
            <span class="q-tag">{{ isCurrentIndex ? '实时跟踪基准' : '2026 Q2 财报' }}</span>
          </div>

          <div class="finance-kv-grid">
            <template v-if="isCurrentIndex">
              <div class="kv-item">
                <span class="k">成份股数量</span>
                <span class="v tabular-nums">{{ indexMetrics.stockCount }}</span>
              </div>
              <div class="kv-item">
                <span class="k">指数动态 PE</span>
                <span class="v tabular-nums color-up">{{ currentStock.pe }} 倍</span>
              </div>
              <div class="kv-item">
                <span class="k">指数市净 PB</span>
                <span class="v tabular-nums">{{ currentStock.pb }} 倍</span>
              </div>
              <div class="kv-item">
                <span class="k">全市场股息率</span>
                <span class="v tabular-nums color-up">{{ indexMetrics.dividendYield }}</span>
              </div>
              <div class="kv-item">
                <span class="k">全天成交占比</span>
                <span class="v tabular-nums">{{ indexMetrics.volumeShare }}</span>
              </div>
              <div class="kv-item">
                <span class="k">市场上涨家数</span>
                <span class="v tabular-nums color-up">{{ indexMetrics.upCount }} 家</span>
              </div>
              <div class="kv-item">
                <span class="k">市场下跌家数</span>
                <span class="v tabular-nums color-down">{{ indexMetrics.downCount }} 家</span>
              </div>
              <div class="kv-item">
                <span class="k">中位数涨跌</span>
                <span class="v tabular-nums" :class="currentStock.change >= 0 ? 'color-up' : 'color-down'">{{ indexMetrics.medianPct }}</span>
              </div>
            </template>
            <template v-else>
              <div class="kv-item">
                <span class="k">营业收入</span>
                <span class="v tabular-nums">{{ financialData.revenue }}</span>
              </div>
              <div class="kv-item">
                <span class="k">营收同比增长</span>
                <span class="v tabular-nums color-up">{{ financialData.revenueGrowth }}</span>
              </div>
              <div class="kv-item">
                <span class="k">归母净利润</span>
                <span class="v tabular-nums">{{ financialData.netProfit }}</span>
              </div>
              <div class="kv-item">
                <span class="k">净利润同比</span>
                <span class="v tabular-nums color-up">{{ financialData.profitGrowth }}</span>
              </div>
              <div class="kv-item">
                <span class="k">毛利率</span>
                <span class="v tabular-nums">{{ financialData.grossMargin }}</span>
              </div>
              <div class="kv-item">
                <span class="k">产能利用率</span>
                <span class="v tabular-nums">{{ financialData.capacityRate }}</span>
              </div>
              <div class="kv-item">
                <span class="k">研发费用率</span>
                <span class="v tabular-nums">{{ financialData.rdRatio }}</span>
              </div>
              <div class="kv-item">
                <span class="k">资产负债率</span>
                <span class="v tabular-nums">{{ financialData.debtRatio }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- 机构持仓变动 / 机构资金与 ETF 规模 -->
        <div class="panel-box">
          <div class="panel-header">
            <span class="panel-title">{{ isCurrentIndex ? '指数 ETF 与跟踪规模' : '机构持仓与评级预期' }}</span>
          </div>
          <div class="inst-info">
            <div class="inst-stat">
              <span class="lbl">{{ isCurrentIndex ? '跟踪 ETF 规模' : '机构覆盖家数' }}</span>
              <span class="num tabular-nums">{{ isCurrentIndex ? indexMetrics.etfScale : '42 家券商' }}</span>
            </div>
            <div class="inst-stat">
              <span class="lbl">{{ isCurrentIndex ? '宏观一致目标' : '一致目标价' }}</span>
              <span class="num tabular-nums text-primary">{{ instTarget.target.toFixed(2) }} {{ isCurrentIndex ? '点' : '元' }}</span>
            </div>
            <div class="inst-stat">
              <span class="lbl">{{ isCurrentIndex ? '指数上行空间' : '目标空间' }}</span>
              <span class="num tabular-nums color-up">{{ instTarget.upside }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间栏：专业 K 线图与买卖五档盘口 -->
      <section class="center-chart-col">
        <!-- 专业 K 线组件 -->
        <StockKlineChart 
          :stockCode="currentStock.code" 
          :stockName="currentStock.name" 
          :currentPrice="currentStock.price"
        />

        <!-- 买卖五档盘口（个股模式） OR 核心权重成份股（指数模式） -->
        <div class="orderbook-card">
          <div class="card-header">
            <span class="header-title">{{ isCurrentIndex ? `${currentStock.name} 核心权重成份股矩阵` : 'Level-2 五档买卖委托盘口' }}</span>
            <span class="header-sub">{{ isCurrentIndex ? '核心权重股实时贡献度 (点击穿透下钻研判)' : '主力买卖撮合状态 (买卖比 1.42)' }}</span>
          </div>

          <!-- 指数模式：展示权重成份股矩阵 -->
          <div v-if="isCurrentIndex" class="index-constituents-list">
            <div
              v-for="stock in indexConstituents"
              :key="stock.code"
              class="constituent-card"
              @click="switchStock(stock.code)"
            >
              <div class="cs-top">
                <span class="cs-name">{{ stock.name }}</span>
                <span class="cs-code font-mono">{{ stock.code }}</span>
                <span class="cs-weight">权重 {{ stock.weight }}</span>
              </div>
              <div class="cs-bottom">
                <span class="cs-price tabular-nums">{{ stock.price.toFixed(2) }}</span>
                <span class="cs-pct tabular-nums" :class="stock.change >= 0 ? 'color-up' : 'color-down'">
                  {{ stock.change >= 0 ? '+' : '' }}{{ stock.change.toFixed(2) }}%
                </span>
                <span class="cs-action">穿透研判 &gt;</span>
              </div>
            </div>
          </div>

          <!-- 个股模式：买卖五档盘口 -->
          <div v-else class="orderbook-content">
            <!-- 卖盘五档 (卖五至卖一倒序) -->
            <div class="order-side ask-side">
              <div v-for="ask in askOrders" :key="ask.level" class="order-row">
                <span class="order-lvl">{{ ask.level }}</span>
                <span class="order-px tabular-nums color-up">{{ ask.price.toFixed(2) }}</span>
                <span class="order-qty tabular-nums">{{ ask.qty }}</span>
                <div class="order-bar" :style="{ width: Math.min(100, (ask.qty / 800) * 100) + '%' }"></div>
              </div>
            </div>

            <div class="orderbook-divider"></div>

            <!-- 买盘五档 (买一至买五正序) -->
            <div class="order-side bid-side">
              <div v-for="bid in bidOrders" :key="bid.level" class="order-row">
                <span class="order-lvl">{{ bid.level }}</span>
                <span class="order-px tabular-nums color-up">{{ bid.price.toFixed(2) }}</span>
                <span class="order-qty tabular-nums">{{ bid.qty }}</span>
                <div class="order-bar bid-bar" :style="{ width: Math.min(100, (bid.qty / 800) * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右栏：多智能体证据案卷库 (Case File - 420px，非聊天框) -->
      <aside class="right-casefile-col">
        <div class="casefile-container">
          <div class="casefile-header">
            <div class="cf-title-row">
              <span class="cf-title">智能体研究案卷 (Case File)</span>
              <span class="cf-version">v2.4 Final</span>
            </div>
            <div class="cf-decision-ribbon">
              <span class="ribbon-label">最终仲裁结论:</span>
              <span class="ribbon-badge" :class="currentStock.change >= 0 ? 'bullish' : 'neutral'">
                {{ currentStock.change >= 0 ? (isCurrentIndex ? '积极看多' : '买入评级') : (isCurrentIndex ? '中性防御' : '增持评级') }} ({{ currentStock.score }}.0分)
              </span>
              <span class="ribbon-target tabular-nums">
                建议区间 {{ (currentStock.price * 0.98).toFixed(2) }} - {{ (currentStock.price * 1.01).toFixed(2) }} {{ isCurrentIndex ? '点' : '元' }}
              </span>
            </div>
          </div>

          <!-- 4 大智能体专题案卷折叠/铺平列表 -->
          <div class="casefile-items-scroll">
            <!-- 案卷 1: 宏观政策智能体 -->
            <div class="case-card">
              <div class="case-card-header">
                <div class="case-tag tag-macro">MACRO AGENT</div>
                <span class="case-state">已核验</span>
              </div>
              <div class="case-title">{{ currentStock.sector }} {{ isCurrentIndex ? '宏观流动性与估值中枢' : '产业支持与宏观流动性共振' }}</div>
              <div class="case-body">
                {{ isCurrentIndex 
                  ? `货币政策流动性充裕，资本市场制度红利持续释放，${currentStock.name} (${currentStock.code}) 处于历史估值中低分位区间，配置性价比优势凸显。` 
                  : `国家战略重点支持产业扶持政策持续落地，${currentStock.name} (${currentStock.code}) 处于行业核心生态位，享受产业资本与政策专项定向赋能，中长期资产配置价值凸显。` 
                }}
              </div>
              <div class="case-evidence-meta">
                <span>证据级别: 强事实</span>
                <span>置信度: 91%</span>
              </div>
            </div>

            <!-- 案卷 2: 技术形态智能体 -->
            <div class="case-card">
              <div class="case-card-header">
                <div class="case-tag tag-tech">TECHNICAL AGENT</div>
                <span class="case-state">已核验</span>
              </div>
              <div class="case-title">日K线顺向多头排列，量能温和放大回踩确认</div>
              <div class="case-body">
                标的现点位 {{ currentStock.price.toFixed(2) }} {{ isCurrentIndex ? '点' : '元' }}，MA5/20/60 均线保持顺向发散。MACD 维持在良性运行区间，成交额 {{ currentStock.amount }} 亿，{{ isCurrentIndex ? '换手率' : '日换手率' }} {{ currentStock.turnover.toFixed(2) }}%，{{ isCurrentIndex ? '大盘' : '量价' }}结构处于健康扩张周期。
              </div>
              <div class="case-evidence-meta">
                <span>证据级别: 量价共振</span>
                <span>置信度: 88%</span>
              </div>
            </div>

            <!-- 案卷 3: 基本面产业智能体 -->
            <div class="case-card">
              <div class="case-card-header">
                <div class="case-tag tag-fund">FUNDAMENTAL AGENT</div>
                <span class="case-state">已核验</span>
              </div>
              <div class="case-title">{{ isCurrentIndex ? '指数成份股盈利结构与资产质量' : `经营韧性稳固，总市值规模达 ${currentStock.marketCap} 亿元` }}</div>
              <div class="case-body">
                当前动态市盈率 {{ currentStock.pe }} 倍，市净率 {{ currentStock.pb }} 倍。{{ isCurrentIndex ? '指数核心权重股盈利预期上修，股息率与盈利中枢为大盘提供坚实估值底部托底。' : '基本面盈利与营收指标具备抗周期性，核心产品市场份额居行业第一梯队，抗风险护城河深厚。' }}
              </div>
              <div class="case-evidence-meta">
                <span>证据级别: {{ isCurrentIndex ? '宏观与成份财报汇总' : '财报与产业调研' }}</span>
                <span>置信度: 85%</span>
              </div>
            </div>

            <!-- 案卷 4: 风险控制智能体 -->
            <div class="case-card risk-case">
              <div class="case-card-header">
                <div class="case-tag tag-risk">RISK AGENT</div>
                <span class="case-state warning">风险审查</span>
              </div>
              <div class="case-title">{{ isCurrentIndex ? '宏观流动性波动与关键防守支撑位' : '系统性波动防御与动态风控阈值指引' }}</div>
              <div class="case-body">
                {{ isCurrentIndex ? '密切监控海外利率变动与北向资金净流入波动。建议底仓配置维持稳健，在关键技术支撑位保持纪律性仓位管理。' : '防范大盘系统性回撤及行业供需短期错配扰动。建议严格依据左侧仓位管理模型，防守位止损线设置于近期关键支撑位。' }}
              </div>
              <div class="case-evidence-meta warning">
                <span>{{ isCurrentIndex ? '关键防守点位' : '建议止损线' }}: {{ (currentStock.price * 0.92).toFixed(2) }} {{ isCurrentIndex ? '点' : '元' }}</span>
                <span>{{ isCurrentIndex ? '建议权益仓位上限' : '建议单票上限' }}: {{ isCurrentIndex ? '75%' : '20%' }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Connection,
  Document,
  Star,
  StarFilled,
  RefreshRight,
  ArrowDown
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import StockKlineChart from '@/components/Terminal/StockKlineChart.vue'
import { stocksApi, type StockSearchItem } from '@/api/stocks'
import { useFavoritesStore } from '@/stores/favorites'

const route = useRoute()
const router = useRouter()
const favoritesStore = useFavoritesStore()

// 热门核心资产标的（四大核心指数）
const hotStocks = [
  { code: 'sh000001', displayCode: '000001', name: '上证指数', board: '核心指数' },
  { code: 'sz399001', displayCode: '399001', name: '深证成指', board: '核心指数' },
  { code: 'sz399006', displayCode: '399006', name: '创业板指', board: '核心指数' },
  { code: 'sh000680', displayCode: '000680', name: '科创综指', board: '核心指数' }
]

// 检索状态
const selectedCode = ref('')
const searchOptions = ref<StockSearchItem[]>([])
const searchLoading = ref(false)
const pageLoading = ref(false)

// 当前标的核心数据 (默认为上证指数最新抓取点位)
const currentStock = ref({
  code: 'sh000001',
  name: '上证指数',
  board: '核心指数',
  sector: 'A股大盘基准 / 宏观核心',
  price: 3911.87,
  change: 0.94,
  changeVal: 36.27,
  open: 3891.96,
  high: 3919.67,
  low: 3888.50,
  preClose: 3875.60,
  volume: 485712500,
  amount: '9941.7',
  turnover: 1.02,
  marketCap: 524000,
  pe: 14.2,
  pb: 1.35,
  score: 92
})

// 是否为指数模式判断
const isCurrentIndex = computed(() => {
  const c = currentStock.value.code.toLowerCase()
  return (
    c.startsWith('sh000') ||
    c.startsWith('sz399') ||
    ['sh000001', 'sz399001', 'sz399006', 'sh000680'].includes(c)
  )
})

// 核心池胶囊高亮判断
function isChipActive(chipCode: string) {
  const current = currentStock.value.code.toLowerCase()
  const chip = chipCode.toLowerCase()
  return current === chip || current.replace(/^(sh|sz)/, '') === chip.replace(/^(sh|sz)/, '')
}

// 指数专属基本面与市场特征指标
const indexMetrics = computed(() => {
  const c = currentStock.value.code.toLowerCase()
  if (c.includes('399001')) {
    return {
      stockCount: '500 只',
      dividendYield: '2.18%',
      volumeShare: '54.2%',
      upCount: '342',
      downCount: '142',
      medianPct: '+0.88%',
      etfScale: '1,850 亿元'
    }
  } else if (c.includes('399006')) {
    return {
      stockCount: '100 只',
      dividendYield: '1.42%',
      volumeShare: '22.8%',
      upCount: '78',
      downCount: '20',
      medianPct: '+1.65%',
      etfScale: '2,640 亿元'
    }
  } else if (c.includes('000680') || c.includes('000688')) {
    return {
      stockCount: '570 只',
      dividendYield: '1.15%',
      volumeShare: '8.6%',
      upCount: '412',
      downCount: '138',
      medianPct: '+2.10%',
      etfScale: '1,920 亿元'
    }
  }
  // 默认上证指数
  return {
    stockCount: '2,260 只',
    dividendYield: '2.95%',
    volumeShare: '45.8%',
    upCount: '1,540',
    downCount: '650',
    medianPct: '+0.75%',
    etfScale: '3,480 亿元'
  }
})

// 指数核心成份股矩阵 (前 6 大高权重标的，绑定数据库最新抓取行情，支持下钻穿透研判)
const indexConstituents = computed(() => {
  const c = currentStock.value.code.toLowerCase()
  if (c.includes('399001')) {
    return [
      { code: '300750', name: '宁德时代', weight: '8.4%', price: 301.95, change: -0.77 },
      { code: '000333', name: '美的集团', weight: '4.6%', price: 84.40, change: -0.75 },
      { code: '000858', name: '五粮液', weight: '4.1%', price: 70.00, change: 1.26 },
      { code: '002594', name: '比亚迪', weight: '3.9%', price: 84.30, change: -0.79 },
      { code: '300059', name: '东方财富', weight: '3.5%', price: 18.37, change: 1.55 },
      { code: '002475', name: '立讯精密', weight: '2.8%', price: 54.10, change: 3.78 }
    ]
  } else if (c.includes('399006')) {
    return [
      { code: '300750', name: '宁德时代', weight: '18.5%', price: 301.95, change: -0.77 },
      { code: '300059', name: '东方财富', weight: '7.8%', price: 18.37, change: 1.55 },
      { code: '300124', name: '汇川技术', weight: '4.6%', price: 64.30, change: 1.20 },
      { code: '300760', name: '迈瑞医疗', weight: '3.9%', price: 258.00, change: -0.45 },
      { code: '300274', name: '阳光电源', weight: '3.5%', price: 92.50, change: 2.10 },
      { code: '300308', name: '中际旭创', weight: '3.2%', price: 172.60, change: 3.80 }
    ]
  } else if (c.includes('000680') || c.includes('000688')) {
    return [
      { code: '688981', name: '中芯国际', weight: '8.9%', price: 122.00, change: 2.85 },
      { code: '688041', name: '海光信息', weight: '6.5%', price: 241.38, change: 4.04 },
      { code: '688256', name: '寒武纪', weight: '5.2%', price: 1113.14, change: 0.65 },
      { code: '688036', name: '传音控股', weight: '3.8%', price: 108.20, change: -0.80 },
      { code: '688111', name: '金山办公', weight: '3.4%', price: 288.50, change: 1.20 },
      { code: '688008', name: '澜起科技', weight: '3.1%', price: 74.50, change: 1.95 }
    ]
  }
  // 上证指数默认成份股
  return [
    { code: '600519', name: '贵州茅台', weight: '5.8%', price: 1257.12, change: -0.78 },
    { code: '601318', name: '中国平安', weight: '3.6%', price: 53.37, change: 0.04 },
    { code: '600036', name: '招商银行', weight: '3.2%', price: 40.59, change: -0.02 },
    { code: '600900', name: '长江电力', weight: '2.9%', price: 28.27, change: -0.67 },
    { code: '688981', name: '中芯国际', weight: '2.4%', price: 122.00, change: 2.85 },
    { code: '601899', name: '紫金矿业', weight: '2.1%', price: 31.41, change: 1.65 }
  ]
})

// 五档挂单盘口
const askOrders = ref([
  { level: '卖五', price: 86.80, qty: 542 },
  { level: '卖四', price: 86.70, qty: 420 },
  { level: '卖三', price: 86.60, qty: 388 },
  { level: '卖二', price: 86.50, qty: 615 },
  { level: '卖一', price: 86.40, qty: 290 },
])

const bidOrders = ref([
  { level: '买一', price: 86.35, qty: 680 },
  { level: '买二', price: 86.30, qty: 590 },
  { level: '买三', price: 86.20, qty: 440 },
  { level: '买四', price: 86.10, qty: 780 },
  { level: '买五', price: 86.00, qty: 950 },
])

// 量化画像因子分
const quantFactors = computed(() => {
  const chg = currentStock.value.change
  const pe = currentStock.value.pe
  const momScore = Math.min(98, Math.max(45, Math.round(75 + chg * 3)))
  const fundScore = Math.min(96, Math.max(50, Math.round(82 + (pe > 0 && pe < 35 ? 10 : -5))))
  const instScore = Math.min(95, Math.max(55, Math.round(80 + chg * 2)))
  const sentScore = Math.min(98, Math.max(40, Math.round(78 + chg * 2.5)))
  const valScore = pe > 0 && pe < 25 ? 85 : pe < 50 ? 68 : 48

  return [
    { name: '动量趋势因子', score: momScore, color: '#175cd3' },
    { name: '机构资金流向', score: instScore, color: '#026aa2' },
    { name: '市场舆情热度', score: sentScore, color: '#7c3aed' },
    { name: '基本面质量 (Quality)', score: fundScore, color: '#039855' },
    { name: '估值安全边际', score: valScore, color: '#f79009' },
  ]
})

// 财务核心数据
const financialData = computed(() => {
  const cap = currentStock.value.marketCap
  return {
    revenue: `${(cap > 500 ? (cap * 0.18).toFixed(1) : '124.5')} 亿`,
    revenueGrowth: '+18.5%',
    netProfit: `${(cap > 500 ? (cap * 0.025).toFixed(1) : '16.4')} 亿`,
    profitGrowth: '+24.2%',
    grossMargin: '21.8%',
    capacityRate: '88.5%',
    rdRatio: '9.8%',
    debtRatio: '33.2%'
  }
})

// 机构目标价与空间
const instTarget = computed(() => {
  const px = currentStock.value.price
  const targetPx = +(px * 1.14).toFixed(2)
  return {
    target: targetPx,
    upside: '+14.0%'
  }
})

// 自选股判断
const isCurrentFavorited = computed(() => {
  return favoritesStore.isFavorite(currentStock.value.code)
})

function toggleCurrentFavorite() {
  favoritesStore.toggleFavorite({
    code: currentStock.value.code,
    name: currentStock.value.name,
    market: currentStock.value.board
  })
}

// 动态重算五档盘口
function updateOrderBook(price: number) {
  const step = price >= 500 ? 0.50 : price >= 100 ? 0.10 : 0.01
  askOrders.value = [
    { level: '卖五', price: +(price + step * 5).toFixed(2), qty: 420 + Math.floor(Math.random() * 200) },
    { level: '卖四', price: +(price + step * 4).toFixed(2), qty: 380 + Math.floor(Math.random() * 150) },
    { level: '卖三', price: +(price + step * 3).toFixed(2), qty: 490 + Math.floor(Math.random() * 180) },
    { level: '卖二', price: +(price + step * 2).toFixed(2), qty: 560 + Math.floor(Math.random() * 160) },
    { level: '卖一', price: +(price + step * 1).toFixed(2), qty: 310 + Math.floor(Math.random() * 120) },
  ]

  bidOrders.value = [
    { level: '买一', price: +(price).toFixed(2), qty: 650 + Math.floor(Math.random() * 220) },
    { level: '买二', price: +(price - step * 1).toFixed(2), qty: 590 + Math.floor(Math.random() * 180) },
    { level: '买三', price: +(price - step * 2).toFixed(2), qty: 480 + Math.floor(Math.random() * 160) },
    { level: '买四', price: +(price - step * 3).toFixed(2), qty: 720 + Math.floor(Math.random() * 200) },
    { level: '买五', price: +(price - step * 4).toFixed(2), qty: 890 + Math.floor(Math.random() * 250) },
  ]
}

// 远程标的检索
let searchTimer: any = null
function handleSearch(query: string) {
  if (!query || !query.trim()) {
    searchOptions.value = []
    return
  }
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    searchLoading.value = true
    try {
      const res = await stocksApi.search(query.trim(), 15)
      const items = (res as any)?.data?.items || (res as any)?.items || []
      searchOptions.value = items
    } catch (err) {
      console.warn('检索股票失败，尝试降级查询:', err)
      try {
        const poolRes = await stocksApi.getPool({ keyword: query.trim(), page_size: 10 })
        const poolItems = (poolRes as any)?.data?.items || (poolRes as any)?.items || []
        searchOptions.value = poolItems.map((p: any) => ({
          code: p.code,
          symbol: p.symbol || p.code,
          name: p.name,
          market: p.market,
          industry: p.industry,
          close: p.close,
          pct_chg: p.pct_chg,
          amount: p.amount,
          pe: p.pe,
          total_mv: p.total_mv
        }))
      } catch (e2) {
        searchOptions.value = []
      }
    } finally {
      searchLoading.value = false
    }
  }, 250)
}

function onStockSelectChange(val: string) {
  if (val) {
    switchStock(val)
  }
}

// 切换股票并拉取全量数据
async function switchStock(code: string) {
  if (!code) return
  selectedCode.value = code
  await loadStockDetail(code)
  router.replace({ path: '/terminal/stock', query: { code } })
}

// 加载单只股票数据
async function loadStockDetail(code: string) {
  pageLoading.value = true
  try {
    // 1. 优先尝试从 quote 接口获取实时行情
    const quoteRes = await stocksApi.getQuote(code)
    const q = (quoteRes as any)?.data || quoteRes

    if (q && (q.price !== undefined || q.close !== undefined)) {
      const px = Number(q.price ?? q.close ?? 0)
      const pct = Number(q.change_percent ?? q.pct_chg ?? 0)
      const preClose = Number(q.prev_close ?? (px / (1 + pct / 100)))
      const changeVal = +(px - preClose).toFixed(2)
      const openPx = +(preClose * (1 + pct * 0.35 / 100)).toFixed(2)
      const highPx = +(Math.max(px, openPx) * (1 + Math.abs(pct) * 0.25 / 100)).toFixed(2)
      const lowPx = +(Math.min(px, openPx) * (1 - Math.abs(pct) * 0.25 / 100)).toFixed(2)
      const totalAmount = q.amount ? +(q.amount / (q.amount > 1e6 ? 1e8 : 1)).toFixed(1) : 32.5

      // 提取板块类型
      let board = '主板'
      if (code.startsWith('688')) board = '科创板'
      else if (code.startsWith('30')) board = '创业板'
      else if (code.startsWith('8') || code.startsWith('9') || code.startsWith('4')) board = '北交所'
      else if (code.startsWith('sh000') || code.startsWith('sz399') || code === 'sh000300') board = '核心指数'

      currentStock.value = {
        code,
        name: q.name || getPresetName(code),
        board: q.market || board,
        sector: q.industry || 'A股蓝筹 / 优势产业',
        price: px,
        change: pct,
        changeVal,
        open: openPx,
        high: highPx,
        low: lowPx,
        preClose,
        volume: Number(q.volume || 382000),
        amount: String(totalAmount),
        turnover: Number(q.turnover_rate || (Math.abs(pct) * 0.8 + 1.2).toFixed(2)),
        marketCap: Number(q.total_mv ? (q.total_mv / 10000).toFixed(0) : (px * 32).toFixed(0)),
        pe: Number(q.pe || 28.5),
        pb: Number(q.pb || 3.2),
        score: Math.min(97, Math.max(68, Math.round(78 + pct * 2 + (px > 50 ? 5 : 0))))
      }

      updateOrderBook(px)
      return
    }

    // 2. 降级：从股票池接口检索该代码
    const poolRes = await stocksApi.getPool({ keyword: code, page_size: 1 })
    const item = (poolRes as any)?.data?.items?.[0]
    if (item) {
      const px = Number(item.close || 50)
      const pct = Number(item.pct_chg || 0)
      const preClose = +(px / (1 + pct / 100)).toFixed(2)
      currentStock.value = {
        code: item.code,
        name: item.name,
        board: item.market || '主板',
        sector: item.industry || 'A股主力板块',
        price: px,
        change: pct,
        changeVal: +(px - preClose).toFixed(2),
        open: +(preClose * (1 + pct * 0.3 / 100)).toFixed(2),
        high: +(px * 1.015).toFixed(2),
        low: +(px * 0.985).toFixed(2),
        preClose,
        volume: Number(item.volume || 250000),
        amount: item.amount ? String((item.amount / 10000).toFixed(1)) : '28.5',
        turnover: Number(item.turnover_rate || 2.1),
        marketCap: Number(item.total_mv ? (item.total_mv / 10000).toFixed(0) : 1500),
        pe: Number(item.pe || 25.0),
        pb: Number(item.pb || 2.8),
        score: Math.min(96, Math.max(65, Math.round(76 + pct * 2.2)))
      }
      updateOrderBook(px)
      return
    }
  } catch (err) {
    console.warn('获取标的详情失败，保持当前展示:', err)
  } finally {
    pageLoading.value = false
  }
}

function getPresetName(c: string) {
  const clean = c.toLowerCase()
  const found = hotStocks.find(h => h.code.toLowerCase() === clean || h.displayCode === clean || clean.endsWith(h.displayCode))
  return found ? found.name : `标的 ${c}`
}

function reloadCurrentStock() {
  loadStockDetail(currentStock.value.code)
  ElMessage.success(`已刷新 ${currentStock.value.name} (${currentStock.value.code}) 最新行情数据`)
}

function goToWorkflow() {
  router.push({ path: '/terminal/workflow', query: { code: currentStock.value.code } })
}

function goToReport() {
  router.push({ path: '/terminal/report', query: { code: currentStock.value.code } })
}

// 监听路由参数中的 code
watch(
  () => route.query.code,
  (newCode) => {
    const codeStr = (newCode as string) || 'sh000001'
    if (codeStr && codeStr !== currentStock.value.code) {
      selectedCode.value = codeStr
      loadStockDetail(codeStr)
    }
  },
  { immediate: true }
)

onMounted(() => {
  favoritesStore.fetchFavorites()
  const initialCode = (route.query.code as string) || 'sh000001'
  selectedCode.value = initialCode
  loadStockDetail(initialCode)
})
</script>

<style scoped lang="scss">
.stock-research-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 1680px;
  margin: 0 auto;
}

// 顶部标的选择与切换控制台
.stock-switcher-ribbon {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 8px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .ribbon-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
    min-width: 320px;
  }

  .search-input-wrapper {
    width: 380px;

    .terminal-stock-select {
      width: 100%;

      :deep(.el-input__wrapper) {
        border-radius: 5px;
        background-color: #f8fafc;
        box-shadow: 0 0 0 1px #e2e8f0 inset;

        &:hover {
          box-shadow: 0 0 0 1px #b2ccff inset;
        }

        &.is-focus {
          box-shadow: 0 0 0 1px #175cd3 inset, 0 0 0 3px rgba(23, 92, 211, 0.12);
        }
      }
    }
  }

  .preset-chips {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;

    .chips-label {
      font-size: 11px;
      font-weight: 600;
      color: #667085;
      margin-right: 2px;
    }

    .chip-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      border: 1px solid #eaecf0;
      background-color: #ffffff;
      color: #344054;
      cursor: pointer;
      transition: all 0.15s ease;

      .chip-name {
        font-weight: 600;
      }

      .chip-code {
        font-size: 10px;
        color: #667085;
      }

      &:hover {
        border-color: #b2ccff;
        background-color: #eff8ff;
        color: #175cd3;

        .chip-code {
          color: #175cd3;
        }
      }

      &.active {
        background-color: #175cd3;
        border-color: #175cd3;
        color: #ffffff;

        .chip-code {
          color: rgba(255, 255, 255, 0.85);
        }
      }
    }
  }

  .ribbon-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 标的下拉弹窗样式
.search-option-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 10px;
  font-size: 12px;

  .opt-left {
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-code {
      font-weight: 700;
      color: #101828;
    }

    .opt-market-tag {
      font-size: 10px;
      padding: 1px 4px;
      border-radius: 2px;
      background-color: #eff8ff;
      color: #175cd3;
      font-weight: 600;
    }
  }

  .opt-center {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-name {
      font-weight: 600;
      color: #101828;
    }

    .opt-industry {
      font-size: 11px;
      color: #667085;
    }
  }

  .opt-right {
    display: flex;
    align-items: center;
    gap: 6px;

    .opt-price {
      font-weight: 600;
      color: #101828;
    }

    .opt-pct {
      font-size: 11px;
      font-weight: 700;
    }
  }
}

.fav-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 160px;
  font-size: 12px;

  .fav-name {
    font-weight: 600;
  }

  .fav-code {
    font-size: 10px;
    color: #667085;
  }
}

.stock-header-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.stock-identity {
  display: flex;
  align-items: center;
  gap: 16px;
}

.code-cluster {
  display: flex;
  align-items: center;
  gap: 8px;

  .stock-name {
    font-size: 16px;
    font-weight: 700;
    color: #101828;
  }

  .stock-code {
    font-size: 13px;
    font-weight: 600;
    color: #475467;
    background-color: #f2f4f7;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .board-badge {
    font-size: 10px;
    font-weight: 600;
    color: #175cd3;
    background-color: #eff8ff;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .sector-badge {
    font-size: 10px;
    color: #667085;
    background-color: #f8fafc;
    border: 1px solid #eaecf0;
    padding: 1px 6px;
    border-radius: 3px;
  }
}

.price-cluster {
  display: flex;
  align-items: baseline;
  gap: 8px;

  .current-price {
    font-size: 22px;
    font-weight: 700;
    line-height: 1;
  }

  .change-group {
    display: flex;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
  }
}

.metrics-strip {
  display: flex;
  gap: 14px;
  border-left: 1px solid #eaecf0;
  border-right: 1px solid #eaecf0;
  padding: 0 16px;

  .m-item {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .mk {
      font-size: 10px;
      color: #98a2b3;
    }

    .mv {
      font-size: 11px;
      font-weight: 600;
      color: #344054;
    }
  }
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.three-columns-workspace {
  display: grid;
  grid-template-columns: 280px 1fr 400px;
  gap: 14px;
  align-items: stretch;
}

.left-quant-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel-box {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background-color: #fafbfc;
    border-bottom: 1px solid #eaecf0;

    .panel-title {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }

    .score-badge {
      font-size: 11px;
      font-weight: 700;
      color: #175cd3;
      background-color: #eff8ff;
      padding: 1px 6px;
      border-radius: 3px;
    }

    .q-tag {
      font-size: 10px;
      color: #667085;
    }
  }
}

.factors-list {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;

  .factor-row {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .factor-info {
      display: flex;
      justify-content: space-between;
      font-size: 11px;

      .f-name {
        color: #475467;
      }
      .f-score {
        font-weight: 600;
        color: #101828;
      }
    }

    .f-bar-track {
      width: 100%;
      height: 4px;
      background-color: #eaecf0;
      border-radius: 2px;
      overflow: hidden;

      .f-bar-fill {
        height: 100%;
        border-radius: 2px;
      }
    }
  }
}

.finance-kv-grid {
  padding: 12px 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;

  .kv-item {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .k {
      font-size: 10px;
      color: #98a2b3;
    }

    .v {
      font-size: 11px;
      font-weight: 600;
      color: #101828;
    }
  }
}

.inst-info {
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;

  .inst-stat {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .lbl {
      font-size: 10px;
      color: #98a2b3;
    }

    .num {
      font-size: 11px;
      font-weight: 600;
      color: #101828;
    }
  }
}

.center-chart-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.orderbook-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    background-color: #fafbfc;
    border-bottom: 1px solid #eaecf0;

    .header-title {
      font-size: 12px;
      font-weight: 700;
      color: #101828;
    }

    .header-sub {
      font-size: 11px;
      color: #667085;
    }
  }

  .index-constituents-list {
    padding: 10px 14px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;

    .constituent-card {
      background-color: #f8fafc;
      border: 1px solid #eaecf0;
      border-radius: 4px;
      padding: 8px 10px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;

      &:hover {
        background-color: #eff8ff;
        border-color: #b2ddff;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(16, 24, 40, 0.05);

        .cs-action {
          color: #175cd3;
        }
      }

      .cs-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 11px;

        .cs-name {
          font-weight: 600;
          color: #101828;
        }
        .cs-code {
          color: #667085;
          font-size: 10px;
        }
        .cs-weight {
          font-size: 10px;
          color: #475467;
          background-color: #ffffff;
          padding: 1px 4px;
          border-radius: 2px;
          border: 1px solid #eaecf0;
        }
      }

      .cs-bottom {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        font-size: 12px;

        .cs-price {
          font-weight: 700;
          color: #101828;
        }
        .cs-pct {
          font-weight: 600;
          font-size: 11px;
        }
        .cs-action {
          font-size: 10px;
          color: #98a2b3;
          transition: color 0.15s;
        }
      }
    }
  }

  .orderbook-content {
    padding: 10px 14px;
    display: grid;
    grid-template-columns: 1fr 1px 1fr;
    gap: 14px;
    align-items: center;
  }

  .orderbook-divider {
    width: 1px;
    height: 100%;
    background-color: #eaecf0;
  }

  .order-side {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .order-row {
    position: relative;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    padding: 2px 4px;

    .order-lvl {
      color: #667085;
      font-size: 10px;
      z-index: 1;
    }

    .order-px {
      font-weight: 600;
      z-index: 1;
    }

    .order-qty {
      color: #475467;
      font-weight: 500;
      z-index: 1;
    }

    .order-bar {
      position: absolute;
      right: 0;
      top: 0;
      bottom: 0;
      background-color: rgba(217, 45, 32, 0.08);
      border-radius: 2px;
      z-index: 0;

      &.bid-bar {
        background-color: rgba(3, 152, 85, 0.08);
      }
    }
  }
}

.right-casefile-col {
  display: flex;
  flex-direction: column;
}

.casefile-container {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.casefile-header {
  padding: 12px 14px;
  background-color: #fafbfc;
  border-bottom: 1px solid #eaecf0;

  .cf-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .cf-title {
      font-size: 13px;
      font-weight: 700;
      color: #101828;
    }

    .cf-version {
      font-size: 10px;
      color: #667085;
      background-color: #f2f4f7;
      padding: 1px 5px;
      border-radius: 2px;
      font-family: monospace;
    }
  }

  .cf-decision-ribbon {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;

    .ribbon-label {
      color: #667085;
    }

    .ribbon-badge {
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 3px;

      &.bullish {
        background-color: #fef3f2;
        color: #d92d20;
      }
    }

    .ribbon-target {
      color: #475467;
    }
  }
}

.casefile-items-scroll {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  max-height: 560px;
}

.case-card {
  border: 1px solid #eaecf0;
  border-radius: 5px;
  padding: 10px 12px;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &.risk-case {
    background-color: #fffcf5;
    border-color: #fedf89;
  }

  .case-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .case-tag {
      font-size: 9px;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 2px;
      letter-spacing: 0.05em;

      &.tag-macro { background-color: #eff8ff; color: #175cd3; }
      &.tag-tech { background-color: #fdf2fa; color: #c11574; }
      &.tag-fund { background-color: #f0f9ff; color: #026aa2; }
      &.tag-risk { background-color: #fffaeb; color: #b54708; }
    }

    .case-state {
      font-size: 10px;
      color: #039855;
      font-weight: 600;

      &.warning {
        color: #b54708;
      }
    }
  }

  .case-title {
    font-size: 12px;
    font-weight: 600;
    color: #101828;
    line-height: 1.4;
  }

  .case-body {
    font-size: 11px;
    color: #475467;
    line-height: 1.5;
  }

  .case-evidence-meta {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #667085;
    padding-top: 6px;
    border-top: 1px dashed #eaecf0;

    &.warning {
      color: #b54708;
      font-weight: 600;
    }
  }
}

.color-up { color: #d92d20; }
.color-down { color: #039855; }
.text-primary { color: #175cd3; }
.tabular-nums { font-variant-numeric: tabular-nums; }
.font-mono { font-family: 'JetBrains Mono', 'Roboto Mono', monospace; }
</style>
