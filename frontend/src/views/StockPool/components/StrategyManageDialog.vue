<template>
  <el-dialog
    v-model="dialogVisible"
    title="我的量化策略库 (Custom Quant Strategies)"
    width="840px"
    destroy-on-close
    class="strategy-manage-dialog"
    append-to-body
  >
    <!-- 顶部操作条 -->
    <div class="manage-toolbar">
      <div class="toolbar-left">
        <span class="total-text">共管理 <strong>{{ strategies.length }}</strong> 套量化选股策略</span>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKw"
          placeholder="搜索策略名称 / 描述..."
          size="small"
          clearable
          style="width: 200px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button
          type="warning"
          plain
          size="small"
          @click="handleResetDefaults"
        >
          <el-icon><RefreshRight /></el-icon>
          恢复系统推荐预设
        </el-button>
        <el-button type="primary" size="small" @click="$emit('create')">
          <el-icon><Plus /></el-icon>
          新建量化策略
        </el-button>
      </div>
    </div>

    <!-- 策略列表 -->
    <div v-if="filteredStrategies.length > 0" class="strategy-cards-list">
      <div
        v-for="item in filteredStrategies"
        :key="item.id"
        class="strategy-card-item"
        :class="{ 'is-core': item.cannot_delete }"
      >
        <div class="card-main">
          <div class="card-title-row">
            <el-tag :type="item.tag_type || 'primary'" effect="dark" size="small" class="strategy-badge">
              {{ item.icon || '🎯' }} {{ item.name }}
            </el-tag>
            <el-tag v-if="item.cannot_delete" type="warning" effect="dark" size="small" class="core-badge">
              ⭐ 系统核心驱动 · 不可删除
            </el-tag>
            <el-tag v-else-if="item.is_system" type="info" effect="plain" size="small" class="preset-badge">
              经典推荐
            </el-tag>
            <span class="update-time">更新于 {{ formatDate(item.updated_at) }}</span>
          </div>

          <p class="card-desc">{{ item.description || '暂无投资逻辑描述' }}</p>

          <!-- 规则芯片 -->
          <div class="rule-chips">
            <span class="chips-label">生效因子:</span>
            <el-tag
              v-for="(rule, idx) in formatRules(item.params)"
              :key="idx"
              size="small"
              effect="plain"
              class="rule-chip"
            >
              {{ rule }}
            </el-tag>
            <span v-if="formatRules(item.params).length === 0" class="empty-rules">全市场无门槛</span>
          </div>
        </div>

        <div class="card-actions">
          <el-button
            type="success"
            size="small"
            @click="handleApply(item)"
          >
            <el-icon><Check /></el-icon>
            立即应用选股
          </el-button>
          <el-button
            type="primary"
            plain
            size="small"
            @click="$emit('edit', item)"
          >
            <el-icon><Edit /></el-icon>
            修改
          </el-button>
          <el-tooltip
            v-if="item.cannot_delete"
            content="系统核心候选池驱动策略不可删除，但支持自由修改指标"
            placement="top"
          >
            <span>
              <el-button
                type="danger"
                plain
                size="small"
                disabled
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </span>
          </el-tooltip>
          <el-button
            v-else
            type="danger"
            plain
            size="small"
            @click="handleDelete(item)"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else
      description="暂无匹配的自定义量化策略"
      :image-size="80"
    >
      <el-button type="primary" @click="$emit('create')">
        <el-icon><Plus /></el-icon>
        立即新建第一套量化策略
      </el-button>
    </el-empty>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, Search, Check, Edit, Delete, RefreshRight } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import type { CustomQuantStrategy, StockPoolParams } from '@/api/stocks'

const props = defineProps<{
  visible: boolean
  strategies: CustomQuantStrategy[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'apply', strategy: CustomQuantStrategy): void
  (e: 'create'): void
  (e: 'edit', strategy: CustomQuantStrategy): void
  (e: 'delete', id: string): void
  (e: 'reset-defaults'): void
}>()

const searchKw = ref('')

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const filteredStrategies = computed(() => {
  if (!searchKw.value.trim()) return props.strategies
  const kw = searchKw.value.toLowerCase().trim()
  return props.strategies.filter(s =>
    s.name.toLowerCase().includes(kw) ||
    (s.description && s.description.toLowerCase().includes(kw))
  )
})

const formatDate = (isoStr?: string) => {
  if (!isoStr) return '--'
  try {
    const d = new Date(isoStr)
    return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  } catch {
    return isoStr
  }
}

const formatRules = (params: Partial<StockPoolParams>): string[] => {
  const list: string[] = []
  if (params.preset === 'quant_candidate') list.push('量化初筛候选池')
  if (params.min_pe != null || params.max_pe != null) list.push(`PE ${params.min_pe ?? 0}~${params.max_pe ?? '∞'}`)
  if (params.min_pb != null || params.max_pb != null) list.push(`PB ${params.min_pb ?? 0}~${params.max_pb ?? '∞'}`)
  if (params.min_ps != null || params.max_ps != null) list.push(`PS ${params.min_ps ?? 0}~${params.max_ps ?? '∞'}`)
  if (params.min_amount != null) {
    const amtWan = params.min_amount / 10000
    list.push(`成交额 ≥${amtWan >= 10000 ? (amtWan / 10000).toFixed(1) + '亿' : amtWan.toFixed(0) + '万'}`)
  }
  if (params.min_close != null || params.max_close != null) list.push(`股价 ¥${params.min_close ?? 0}~${params.max_close ?? '∞'}`)
  if (params.min_pct_chg != null || params.max_pct_chg != null) list.push(`涨跌幅 ${params.min_pct_chg ?? '-∞'}%~${params.max_pct_chg ?? '+∞'}%`)
  if (params.min_turnover_rate != null || params.max_turnover_rate != null) list.push(`换手率 ${params.min_turnover_rate ?? 0}%~${params.max_turnover_rate ?? '∞'}%`)
  if (params.min_volume_ratio != null || params.max_volume_ratio != null) list.push(`量比 ${params.min_volume_ratio ?? 0}~${params.max_volume_ratio ?? '∞'}`)
  if (params.min_roe != null || params.max_roe != null) list.push(`ROE ${params.min_roe ?? 0}%~${params.max_roe ?? '∞'}%`)
  if (params.min_net_profit_growth != null || params.max_net_profit_growth != null) list.push(`净利增速 ${params.min_net_profit_growth ?? '-∞'}%~${params.max_net_profit_growth ?? '+∞'}%`)
  if (params.min_revenue_growth != null || params.max_revenue_growth != null) list.push(`营收增速 ${params.min_revenue_growth ?? '-∞'}%~${params.max_revenue_growth ?? '+∞'}%`)
  if (params.min_gross_margin != null || params.max_gross_margin != null) list.push(`毛利率 ${params.min_gross_margin ?? 0}%~${params.max_gross_margin ?? '∞'}%`)
  if (params.volume_level) {
    const volMap: Record<string, string> = { high: '高活跃(>10亿)', medium: '正常(3-10亿)', low: '清淡(<3亿)' }
    list.push(volMap[params.volume_level] || params.volume_level)
  }
  if (params.market_cap_range) {
    const capMap: Record<string, string> = { small: '小盘(<100亿)', medium: '中盘(100-500亿)', large: '大盘(>500亿)' }
    list.push(capMap[params.market_cap_range] || params.market_cap_range)
  }
  if (params.min_market_cap != null || params.max_market_cap != null) {
    list.push(`市值 ${params.min_market_cap ?? 0}亿~${params.max_market_cap ?? '∞'}亿`)
  }
  if (params.market && params.market !== '全部') list.push(params.market)
  return list
}

const handleApply = (strategy: CustomQuantStrategy) => {
  emit('apply', strategy)
  dialogVisible.value = false
}

const handleDelete = async (strategy: CustomQuantStrategy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除量化策略【${strategy.name}】吗？此操作无法撤销。`,
      '删除策略确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', strategy.id)
  } catch {
    // 取消
  }
}

const handleResetDefaults = async () => {
  try {
    await ElMessageBox.confirm(
      '恢复系统推荐预设将把量化候选池与经典策略恢复为系统标准参数，用户自建策略不受影响。是否继续？',
      '恢复系统推荐预设确认',
      {
        confirmButtonText: '确定恢复',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('reset-defaults')
  } catch {
    // 取消
  }
}
</script>

<style scoped lang="scss">
.manage-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;

  .total-text {
    font-size: 13px;
    color: #64748b;
    strong {
      color: #0f172a;
    }
  }

  .toolbar-right {
    display: flex;
    gap: 10px;
    align-items: center;
  }
}

.strategy-cards-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}

.strategy-card-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  transition: all 0.2s ease;

  &.is-core {
    border-color: #fde047;
    background: linear-gradient(180deg, #fefce8 0%, #ffffff 100%);
    box-shadow: 0 2px 8px rgba(234, 179, 8, 0.08);

    &:hover {
      border-color: #eab308;
      box-shadow: 0 4px 14px rgba(234, 179, 8, 0.15);
    }
  }

  &:hover {
    border-color: #93c5fd;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
  }

  .card-main {
    flex: 1;
    min-width: 0;

    .card-title-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 6px;

      .strategy-badge {
        font-size: 13px;
        font-weight: 600;
        padding: 4px 10px;
      }

      .update-time {
        font-size: 12px;
        color: #94a3b8;
      }
    }

    .card-desc {
      font-size: 12px;
      color: #64748b;
      margin: 0 0 8px 0;
      line-height: 1.4;
    }

    .rule-chips {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;

      .chips-label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 500;
      }

      .rule-chip {
        border-radius: 4px;
        font-size: 11px;
      }

      .empty-rules {
        font-size: 11px;
        color: #94a3b8;
      }
    }
  }

  .card-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 20px;
    flex-shrink: 0;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
