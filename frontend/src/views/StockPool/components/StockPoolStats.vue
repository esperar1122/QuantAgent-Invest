<template>
  <div class="stats-overview-container">
    <div class="stats-grid">
      <div
        v-for="card in cards"
        :key="card.key"
        class="stat-card"
        :class="[card.theme, { active: currentMarket === card.filterValue }]"
        @click="$emit('quick-filter', card.filterValue)"
      >
        <!-- 顶边高亮色条 -->
        <div class="card-accent-bar"></div>

        <div class="card-content">
          <!-- 1. 顶行：板块标识与标题 + 标签/激活状态 -->
          <div class="card-header-row">
            <div class="title-cluster">
              <div class="icon-avatar">
                <component :is="card.icon" />
              </div>
              <span class="card-title">{{ card.label }}</span>
            </div>

            <div class="tag-cluster">
              <span class="code-badge font-mono">{{ card.codeRange }}</span>
              <span v-if="currentMarket === card.filterValue" class="active-pill">
                <el-icon class="check-icon"><Check /></el-icon>
                <span>当前</span>
              </span>
            </div>
          </div>

          <!-- 2. 中行：核心数值与占比胶囊 -->
          <div class="card-metric-row">
            <div class="metric-group">
              <span class="metric-value tabular-nums">{{ card.count.toLocaleString() }}</span>
              <span class="metric-unit">{{ card.unit }}</span>
            </div>

            <div class="share-badge tabular-nums">
              {{ card.shareText }}
            </div>
          </div>

          <!-- 3. 底行：市场结构微型进度条与特征说明 -->
          <div class="card-footer-row">
            <div class="mini-progress-track">
              <div class="mini-progress-fill" :style="{ width: card.progressWidth }"></div>
            </div>

            <div class="footer-meta">
              <span class="caption-text">{{ card.description }}</span>
              <span class="action-hint">快速筛选</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Coin,
  OfficeBuilding,
  TrendCharts,
  Cpu,
  Star,
  DataLine,
  Check
} from '@element-plus/icons-vue'
import type { StockPoolStats } from '@/api/stocks'

const props = withDefaults(
  defineProps<{
    stats: StockPoolStats
    currentMarket?: string
  }>(),
  {
    currentMarket: '全部'
  }
)

defineEmits<{
  (e: 'quick-filter', market: string): void
}>()

const total = computed(() => props.stats.total_stocks || 5575)
const mainCount = computed(() => props.stats.main_board_count || 3197)
const chinextCount = computed(() => props.stats.chinext_count || 1406)
const starCount = computed(() => props.stats.star_count || 617)
const bseCount = computed(() => props.stats.bse_count || 344)
const indexCount = computed(() => props.stats.index_count ?? 10)

const cards = computed(() => [
  {
    key: 'all',
    label: 'A股全景池',
    filterValue: '全部',
    icon: Coin,
    theme: 'theme-all',
    count: total.value,
    unit: '只标的',
    codeRange: '全市场',
    shareText: '100% 覆盖',
    progressWidth: '100%',
    description: '全市场在市交易标的全覆盖'
  },
  {
    key: 'main',
    label: '沪深主板',
    filterValue: '主板',
    icon: OfficeBuilding,
    theme: 'theme-main',
    count: mainCount.value,
    unit: '家企业',
    codeRange: '60/00代码',
    shareText: `占比 ${((mainCount.value / (total.value || 1)) * 100).toFixed(1)}%`,
    progressWidth: `${Math.min(100, (mainCount.value / (total.value || 1)) * 100)}%`,
    description: '核心蓝筹骨干与成熟行业支柱'
  },
  {
    key: 'chinext',
    label: '创业板',
    filterValue: '创业板',
    icon: TrendCharts,
    theme: 'theme-chinext',
    count: chinextCount.value,
    unit: '家企业',
    codeRange: '30xxxx',
    shareText: `占比 ${((chinextCount.value / (total.value || 1)) * 100).toFixed(1)}%`,
    progressWidth: `${Math.min(100, (chinextCount.value / (total.value || 1)) * 100)}%`,
    description: '高新技术与创新型成长企业'
  },
  {
    key: 'star',
    label: '科创板',
    filterValue: '科创板',
    icon: Cpu,
    theme: 'theme-star',
    count: starCount.value,
    unit: '家企业',
    codeRange: '688xxx',
    shareText: `占比 ${((starCount.value / (total.value || 1)) * 100).toFixed(1)}%`,
    progressWidth: `${Math.min(100, (starCount.value / (total.value || 1)) * 100)}%`,
    description: '硬核科技先锋与新质生产力'
  },
  {
    key: 'bse',
    label: '北交所',
    filterValue: '北交所',
    icon: Star,
    theme: 'theme-bse',
    count: bseCount.value,
    unit: '家企业',
    codeRange: '8/9xxxx',
    shareText: `占比 ${((bseCount.value / (total.value || 1)) * 100).toFixed(1)}%`,
    progressWidth: `${Math.min(100, (bseCount.value / (total.value || 1)) * 100)}%`,
    description: '创新型中小企业与专精特新'
  },
  {
    key: 'index',
    label: '核心指数',
    filterValue: '重要指数',
    icon: DataLine,
    theme: 'theme-index',
    count: indexCount.value,
    unit: '组基准',
    codeRange: 'INDEX',
    shareText: '基准大盘',
    progressWidth: '85%',
    description: '沪深300/中证500/行业基准'
  }
])
</script>

<style scoped lang="scss">
.stats-overview-container {
  width: 100%;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;

  @media (max-width: 1440px) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
}

.stat-card {
  position: relative;
  background-color: var(--el-bg-color, #ffffff);
  border: 1px solid var(--el-border-color-lighter, #e4e7ec);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  user-select: none;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 24, 40, 0.08);
    border-color: var(--el-color-primary-light-3, #b2ccff);

    .card-footer-row .action-hint {
      color: var(--el-color-primary, #175cd3);
      transform: translateX(2px);
    }
  }

  // 顶边微型主题装饰线
  .card-accent-bar {
    height: 3px;
    width: 100%;
    background-color: transparent;
    transition: background-color 0.2s ease;
  }

  .card-content {
    padding: 12px 14px 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    height: 100%;
  }

  // 顶行
  .card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title-cluster {
      display: flex;
      align-items: center;
      gap: 7px;

      .icon-avatar {
        width: 24px;
        height: 24px;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        flex-shrink: 0;
      }

      .card-title {
        font-size: 13px;
        font-weight: 700;
        color: var(--el-text-color-primary, #101828);
        letter-spacing: -0.01em;
      }
    }

    .tag-cluster {
      display: flex;
      align-items: center;
      gap: 5px;

      .code-badge {
        font-size: 10px;
        font-weight: 600;
        color: var(--el-text-color-secondary, #667085);
        background-color: var(--el-fill-color-light, #f2f4f7);
        padding: 1px 5px;
        border-radius: 3px;
      }

      .active-pill {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        font-size: 10px;
        font-weight: 700;
        padding: 1px 5px;
        border-radius: 3px;

        .check-icon {
          font-size: 10px;
        }
      }
    }
  }

  // 中行
  .card-metric-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin: 2px 0 0 0;

    .metric-group {
      display: flex;
      align-items: baseline;
      gap: 4px;

      .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: var(--el-text-color-primary, #101828);
        line-height: 1.1;
      }

      .metric-unit {
        font-size: 11px;
        font-weight: 500;
        color: var(--el-text-color-secondary, #667085);
      }
    }

    .share-badge {
      font-size: 11px;
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 4px;
    }
  }

  // 底行
  .card-footer-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: auto;
    padding-top: 4px;

    .mini-progress-track {
      width: 100%;
      height: 3px;
      background-color: var(--el-fill-color-light, #eaecf0);
      border-radius: 2px;
      overflow: hidden;

      .mini-progress-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.4s ease;
      }
    }

    .footer-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;

      .caption-text {
        color: var(--el-text-color-secondary, #667085);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 120px;
      }

      .action-hint {
        color: var(--el-text-color-placeholder, #98a2b3);
        font-size: 10px;
        font-weight: 600;
        transition: all 0.15s ease;
        flex-shrink: 0;
      }
    }
  }

  // 各主题配色方案
  // 1. 全部A股 (蓝)
  &.theme-all {
    .icon-avatar { background-color: #eff8ff; color: #175cd3; }
    .share-badge { background-color: #eff8ff; color: #175cd3; }
    .mini-progress-fill { background-color: #175cd3; }
    .card-accent-bar { background-color: #175cd3; opacity: 0.3; }

    &.active {
      border-color: #175cd3;
      background: linear-gradient(180deg, rgba(239, 248, 255, 0.45) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #175cd3; color: #ffffff; }
    }
  }

  // 2. 沪深主板 (绿)
  &.theme-main {
    .icon-avatar { background-color: #ecfdf3; color: #039855; }
    .share-badge { background-color: #ecfdf3; color: #039855; }
    .mini-progress-fill { background-color: #039855; }
    .card-accent-bar { background-color: #039855; opacity: 0.3; }

    &.active {
      border-color: #039855;
      background: linear-gradient(180deg, rgba(236, 253, 243, 0.45) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #039855; color: #ffffff; }
    }
  }

  // 3. 创业板 (金/琥珀)
  &.theme-chinext {
    .icon-avatar { background-color: #fffaeb; color: #b54708; }
    .share-badge { background-color: #fffaeb; color: #b54708; }
    .mini-progress-fill { background-color: #f79009; }
    .card-accent-bar { background-color: #f79009; opacity: 0.3; }

    &.active {
      border-color: #f79009;
      background: linear-gradient(180deg, rgba(255, 250, 235, 0.5) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #f79009; color: #ffffff; }
    }
  }

  // 4. 科创板 (玫红/硬核紫红)
  &.theme-star {
    .icon-avatar { background-color: #fdf2fa; color: #c11574; }
    .share-badge { background-color: #fdf2fa; color: #c11574; }
    .mini-progress-fill { background-color: #c11574; }
    .card-accent-bar { background-color: #c11574; opacity: 0.3; }

    &.active {
      border-color: #c11574;
      background: linear-gradient(180deg, rgba(253, 242, 250, 0.5) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #c11574; color: #ffffff; }
    }
  }

  // 5. 北交所 (蓝紫)
  &.theme-bse {
    .icon-avatar { background-color: #f4f3ff; color: #5925dc; }
    .share-badge { background-color: #f4f3ff; color: #5925dc; }
    .mini-progress-fill { background-color: #5925dc; }
    .card-accent-bar { background-color: #5925dc; opacity: 0.3; }

    &.active {
      border-color: #5925dc;
      background: linear-gradient(180deg, rgba(244, 243, 255, 0.5) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #5925dc; color: #ffffff; }
    }
  }

  // 6. 核心指数 (红)
  &.theme-index {
    .icon-avatar { background-color: #fef3f2; color: #d92d20; }
    .share-badge { background-color: #fef3f2; color: #d92d20; }
    .mini-progress-fill { background-color: #d92d20; }
    .card-accent-bar { background-color: #d92d20; opacity: 0.3; }

    &.active {
      border-color: #d92d20;
      background: linear-gradient(180deg, rgba(254, 243, 242, 0.5) 0%, rgba(255, 255, 255, 1) 100%);
      .card-accent-bar { opacity: 1; height: 3px; }
      .active-pill { background-color: #d92d20; color: #ffffff; }
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.font-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
}
</style>
