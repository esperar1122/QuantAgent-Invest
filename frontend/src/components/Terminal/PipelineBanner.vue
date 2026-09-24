<template>
  <div class="pipeline-card">
    <div class="pipeline-header">
      <div class="pipeline-title-group">
        <span class="tag-badge">SYSTEM PIPELINE</span>
        <h3 class="pipeline-title">系统核心投研全链路：量化因子初筛 ➔ 多智能体深度研判 ➔ 证据仲裁与决策</h3>
        <span class="nav-hint">（点击节点可直达对应业务模块）</span>
      </div>
      <div class="pipeline-note">全流程自动化协同 · 结构化数据支撑 · 杜绝黑盒幻觉</div>
    </div>

    <div class="steps-flow-wrapper">
      <div class="steps-flow">
      <!-- 01 市场扫描 -->
      <div 
        class="step-box clickable" 
        :title="'点击直达：大盘行情与行业资金流看板'"
        @click="handleStepClick('01', '/terminal/overview')"
      >
        <div class="step-top-action">
          <span class="step-num">01</span>
          <el-icon class="jump-icon"><TopRight /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-name">市场扫描</div>
          <div class="step-desc">
            {{ displayKpis.up_count && displayKpis.down_count ? `多空比 ${displayKpis.up_count}:${displayKpis.down_count}` : '指数 / 市场宽度 / 行业资金' }}
          </div>
          <div class="step-badge">全市场 {{ displayKpis.total_stocks.toLocaleString() }} 标的</div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 02 Quant Engine -->
      <div 
        class="step-box highlight clickable" 
        :title="'点击直达：A股多因子量化选股池'"
        @click="handleStepClick('02', '/terminal/screening')"
      >
        <div class="step-top-action">
          <span class="step-num">02</span>
          <el-icon class="jump-icon"><TopRight /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-name">Quant Engine</div>
          <div class="step-desc">多因子量化精筛 · 初筛率 {{ displayKpis.pool_rate }}</div>
          <div class="step-badge highlight-badge">
            {{ displayKpis.total_stocks.toLocaleString() }} ➔ {{ displayKpis.pool_count.toLocaleString() }} 标的
          </div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 03 Multi-Agent -->
      <div 
        class="step-box clickable" 
        :title="'点击直达：多智能体协同流水线与单股研判'"
        @click="handleStepClick('03', '/terminal/workflow')"
      >
        <div class="step-top-action">
          <span class="step-num">03</span>
          <el-icon class="jump-icon"><TopRight /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-name">Multi-Agent</div>
          <div class="step-desc">宏观 / 基本面 / 技术面 / 风险</div>
          <div class="step-badge">
            4大智能体 · {{ displayKpis.running_tasks }} 组运行
          </div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 04 Evidence -->
      <div 
        class="step-box clickable" 
        :title="'点击直达：个股投研与多空证据博辩'"
        @click="handleStepClick('04', '/terminal/stock')"
      >
        <div class="step-top-action">
          <span class="step-num">04</span>
          <el-icon class="jump-icon"><TopRight /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-name">Evidence</div>
          <div class="step-desc">支持证据 / 风险项 / 多空博辩</div>
          <div class="step-badge">
            证据链 · {{ displayKpis.completed_tasks }} 案卷归档
          </div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 05 Decision -->
      <div 
        class="step-box final clickable" 
        :title="'点击直达：全息投研研报库'"
        @click="handleStepClick('05', '/terminal/reports')"
      >
        <div class="step-top-action">
          <span class="step-num">05</span>
          <el-icon class="jump-icon"><TopRight /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-name">Decision</div>
          <div class="step-desc">买卖信号 / 置信度 / 仓位指引</div>
          <div class="step-badge final-badge">全息决策白皮书</div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { TopRight } from '@element-plus/icons-vue'
import { stocksApi } from '@/api/stocks'

export interface KpisProps {
  total_stocks?: number
  pool_count?: number
  pool_rate?: string
  running_tasks?: number
  completed_tasks?: number
  failed_tasks?: number
  up_count?: number
  down_count?: number
  sentiment_score?: number
  sentiment_status?: string
}

const props = defineProps<{
  kpis?: KpisProps
}>()

const router = useRouter()
const route = useRoute()

// 内部兜底状态（当独立使用未传入 props 时启动）
const internalKpis = ref<KpisProps>({
  total_stocks: 5575,
  pool_count: 168,
  pool_rate: '3.0%',
  running_tasks: 0,
  completed_tasks: 1,
  failed_tasks: 0,
  up_count: 4546,
  down_count: 936
})

// 归一化展示数据源（优先使用父组件 props，保持 Single Source of Truth）
const displayKpis = computed(() => {
  return {
    total_stocks: props.kpis?.total_stocks ?? internalKpis.value.total_stocks ?? 5575,
    pool_count: props.kpis?.pool_count ?? internalKpis.value.pool_count ?? 168,
    pool_rate: props.kpis?.pool_rate ?? internalKpis.value.pool_rate ?? '3.0%',
    running_tasks: props.kpis?.running_tasks ?? internalKpis.value.running_tasks ?? 0,
    completed_tasks: props.kpis?.completed_tasks ?? internalKpis.value.completed_tasks ?? 1,
    failed_tasks: props.kpis?.failed_tasks ?? internalKpis.value.failed_tasks ?? 0,
    up_count: props.kpis?.up_count ?? internalKpis.value.up_count ?? 4546,
    down_count: props.kpis?.down_count ?? internalKpis.value.down_count ?? 936
  }
})

onMounted(async () => {
  // 如果父组件未传 kpis，才执行独立拉取
  if (!props.kpis || !props.kpis.total_stocks) {
    try {
      const res = await stocksApi.getMarketOverview()
      const data = (res as any)?.data || (res as any)
      if (data && data.kpis) {
        internalKpis.value = { ...internalKpis.value, ...data.kpis }
      }
    } catch (err) {
      // 保持兜底值
    }
  }
})

function handleStepClick(stepId: string, targetPath: string) {
  if (stepId === '01') {
    if (route.path === '/terminal/overview') {
      const anchorEl = document.getElementById('market-dashboard-anchor')
      if (anchorEl) {
        anchorEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
        return
      }
    }
    router.push(targetPath)
    return
  }

  if (stepId === '02') {
    router.push({
      path: '/terminal/screening',
      query: { preset: 'quant_candidate' }
    })
    return
  }

  router.push(targetPath)
}
</script>

<style scoped lang="scss">
.pipeline-card {
  background: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 16px;
  user-select: none;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;

  .pipeline-title-group {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;

    .tag-badge {
      font-size: 11px;
      font-weight: 700;
      color: #175cd3;
      background-color: #eff8ff;
      border: 1px solid #b2ddff;
      padding: 1px 6px;
      border-radius: 4px;
      letter-spacing: 0.04em;
    }

    .pipeline-title {
      font-size: 14px;
      font-weight: 700;
      color: #101828;
      margin: 0;
    }

    .nav-hint {
      font-size: 11px;
      color: #98a2b3;
      font-weight: 500;
    }
  }

  .pipeline-note {
    font-size: 12px;
    color: #667085;
  }
}

.steps-flow-wrapper {
  width: 100%;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.steps-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 8px;
  min-width: 860px;

  .step-box {
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: #f8fafc;
    border: 1px solid #e4e7ec;
    border-radius: 6px;
    padding: 10px 12px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;

    &.clickable {
      cursor: pointer;

      &:hover {
        border-color: #175cd3;
        background: #ffffff;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(23, 92, 211, 0.1);

        .jump-icon {
          color: #175cd3;
          transform: translate(2px, -2px);
        }

        .step-name {
          color: #175cd3;
        }
      }
    }

    .step-top-action {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .step-num {
        font-size: 13px;
        font-weight: 800;
        color: #98a2b3;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1;
      }

      .jump-icon {
        font-size: 12px;
        color: #d0d5dd;
        transition: all 0.2s ease;
      }
    }

    .step-content {
      flex: 1;

      .step-name {
        font-size: 13px;
        font-weight: 700;
        color: #101828;
        line-height: 1.2;
        transition: color 0.15s ease;
      }

      .step-desc {
        font-size: 11px;
        color: #667085;
        margin: 3px 0 6px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .step-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        color: #344054;
        background: #eaecf0;
        padding: 1px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
      }
    }

    &.highlight {
      background: #eff8ff;
      border-color: #84caff;

      .step-num {
        color: #175cd3;
      }

      .step-name {
        color: #175cd3;
      }

      .jump-icon {
        color: #84caff;
      }

      .highlight-badge {
        background: #175cd3;
        color: #ffffff;
      }

      &:hover {
        border-color: #154cbd;
        box-shadow: 0 4px 14px rgba(23, 92, 211, 0.16);
      }
    }

    &.final {
      background: #faf5ff;
      border-color: #d8b4fe;

      .step-num {
        color: #7e22ce;
      }

      .step-name {
        color: #7e22ce;
      }

      .jump-icon {
        color: #d8b4fe;
      }

      .final-badge {
        background: #7e22ce;
        color: #ffffff;
      }

      &:hover {
        border-color: #6b21a8;
        box-shadow: 0 4px 14px rgba(126, 34, 206, 0.16);

        .jump-icon {
          color: #6b21a8;
        }

        .step-name {
          color: #6b21a8;
        }
      }
    }
  }

  .step-arrow {
    font-size: 14px;
    color: #98a2b3;
    font-weight: 700;
  }
}
</style>
