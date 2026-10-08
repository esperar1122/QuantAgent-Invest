<template>
  <el-dialog
    v-model="dialogVisible"
    title="🎯 我的回测策略库 (Custom Backtest Strategies)"
    width="860px"
    destroy-on-close
    class="backtest-strategy-manage-dialog"
    append-to-body
  >
    <!-- 顶部操作条 -->
    <div class="manage-toolbar">
      <div class="toolbar-left">
        <span class="total-text">共管理 <strong>{{ strategies.length }}</strong> 套专业量化回测策略</span>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchKw"
          placeholder="搜索回测策略名称 / 标的 / 描述..."
          size="small"
          clearable
          style="width: 220px"
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
          新建回测策略
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

          <p class="card-desc">{{ item.description || '暂无回测投资逻辑描述' }}</p>

          <!-- 规则与参数芯片 -->
          <div class="rule-chips">
            <span class="chips-label">参数配置:</span>
            <el-tag
              v-for="(chip, idx) in formatStrategyChips(item.config)"
              :key="idx"
              size="small"
              effect="plain"
              class="rule-chip"
            >
              {{ chip }}
            </el-tag>
          </div>
        </div>

        <div class="card-actions">
          <el-button
            type="success"
            size="small"
            @click="handleApply(item)"
          >
            <el-icon><Check /></el-icon>
            立即套用回测
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
            content="系统核心策略不可删除，但支持修改参数"
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
      description="暂无匹配的回测策略"
      :image-size="80"
    >
      <el-button type="primary" @click="$emit('create')">
        <el-icon><Plus /></el-icon>
        立即新建第一套自定义回测策略
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
import type { CustomBacktestStrategy, BacktestStrategyConfig } from '@/api/quant'

const props = defineProps<{
  visible: boolean
  strategies: CustomBacktestStrategy[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'apply', strategy: CustomBacktestStrategy): void
  (e: 'create'): void
  (e: 'edit', strategy: CustomBacktestStrategy): void
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
    (s.description && s.description.toLowerCase().includes(kw)) ||
    (s.config?.symbol && s.config.symbol.toLowerCase().includes(kw))
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

const formatStrategyChips = (cfg?: BacktestStrategyConfig): string[] => {
  if (!cfg) return ['默认配置']
  const chips: string[] = []

  // 1. 标的
  const syms = (cfg.symbol || '').replace(/，/g, ',').split(',').map(s => s.trim()).filter(Boolean)
  if (syms.length > 1) {
    chips.push(`组合: ${syms.length}只标的`)
  } else if (syms.length === 1) {
    chips.push(`标的: ${syms[0]}`)
  }

  // 2. 策略模型
  const stratMap: Record<string, string> = {
    custom_rule: '🌟 自定义多指标',
    dual_ma: '📈 双均线趋势',
    macd: '🌊 MACD动量',
    bollinger: '🎯 布林带回归'
  }
  chips.push(stratMap[cfg.strategy_name] || cfg.strategy_name)

  // 3. 初始本金
  if (cfg.initial_capital) {
    chips.push(`本金: ¥${(cfg.initial_capital / 10000).toFixed(0)}万`)
  }

  // 4. 风控与仓位
  if (cfg.risk_params) {
    const { stop_loss_pct, take_profit_pct, max_holding_days, position_ratio } = cfg.risk_params
    if (stop_loss_pct) chips.push(`止损 -${stop_loss_pct}%`)
    if (take_profit_pct) chips.push(`止盈 +${take_profit_pct}%`)
    if (max_holding_days) chips.push(`最长持仓 ${max_holding_days}日`)
    if (position_ratio) chips.push(`仓位 ${position_ratio}%`)
  }

  // 5. 摩擦机制
  if (cfg.friction_params) {
    const { friction_preset, slippage_type } = cfg.friction_params
    if (friction_preset === 'etf') chips.push('场内ETF费率')
    else if (friction_preset === 'custom') chips.push('自定义摩擦费率')
    else chips.push('标准A股费率')

    if (slippage_type === 'none') chips.push('零滑点')
    else if (slippage_type === 'volume_impact') chips.push('冲击成本模型')
  }

  return chips
}

const handleApply = (strategy: CustomBacktestStrategy) => {
  emit('apply', strategy)
  dialogVisible.value = false
}

const handleDelete = async (strategy: CustomBacktestStrategy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除回测策略【${strategy.name}】吗？此操作无法撤销。`,
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
      '确定要恢复系统推荐的经典回测策略预设吗？您自建的策略仍会保留。',
      '恢复默认预设确认',
      {
        confirmButtonText: '确定恢复',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    emit('reset-defaults')
  } catch {
    // 取消
  }
}
</script>

<style scoped>
.manage-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-wrap: wrap;
  gap: 10px;
}

.total-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.total-text strong {
  color: var(--el-color-primary);
  font-size: 15px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.strategy-cards-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.strategy-card-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-blank);
  transition: all 0.2s ease;
  gap: 16px;
}

.strategy-card-item:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.strategy-card-item.is-core {
  background: var(--el-fill-color-light);
  border-left: 3px solid var(--el-color-warning);
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.strategy-badge {
  font-weight: 600;
  font-size: 13px;
  padding: 3px 8px;
}

.core-badge, .preset-badge {
  font-size: 11px;
}

.update-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-left: auto;
}

.card-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin: 0 0 8px 0;
}

.rule-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.chips-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.rule-chip {
  font-size: 11px;
  padding: 1px 6px;
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-light);
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

@media (min-width: 640px) {
  .card-actions {
    flex-direction: row;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
