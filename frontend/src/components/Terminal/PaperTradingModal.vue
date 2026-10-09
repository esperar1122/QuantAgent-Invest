<template>
  <el-dialog
    v-model="visible"
    title="🎮 虚拟模拟盘交易终端 (Paper Trading · 10万本金)"
    width="min(920px, 94vw)"
    class="paper-trading-dialog"
    :destroy-on-close="false"
  >
    <div class="paper-trading-container">
      <!-- 1. 账户资产全景看板 -->
      <div class="account-overview-card" v-loading="loading">
        <div class="ov-item highlight">
          <span class="ov-lbl">总资产规模 (NAV)</span>
          <span class="ov-val font-mono tabular-nums">¥{{ formatMoney(account?.total_equity) }}</span>
          <span class="ov-sub">初始本金: ¥{{ formatMoney(account?.initial_capital || 100000) }}</span>
        </div>

        <div class="ov-item">
          <span class="ov-lbl">可用流动现金</span>
          <span class="ov-val font-mono tabular-nums text-cash">¥{{ formatMoney(account?.cash) }}</span>
          <span class="ov-sub">冻结现金: ¥{{ formatMoney(account?.frozen_cash || 0) }}</span>
        </div>

        <div class="ov-item">
          <span class="ov-lbl">证券持仓市值</span>
          <span class="ov-val font-mono tabular-nums">¥{{ formatMoney(account?.holdings_value) }}</span>
          <span class="ov-sub">持有标的: {{ account?.holdings?.length || 0 }} 只</span>
        </div>

        <div class="ov-item">
          <span class="ov-lbl">累计盈亏与收益率</span>
          <div class="pnl-group font-mono tabular-nums" :class="(account?.total_pnl || 0) >= 0 ? 'color-up' : 'color-down'">
            <span class="ov-val">{{ (account?.total_pnl || 0) >= 0 ? '+' : '' }}¥{{ formatMoney(account?.total_pnl) }}</span>
            <span class="ov-pct">({{ (account?.total_return_pct || 0) >= 0 ? '+' : '' }}{{ (account?.total_return_pct || 0).toFixed(2) }}%)</span>
          </div>
          <span class="ov-sub">当日浮动: ¥{{ formatMoney(account?.today_pnl || 0) }}</span>
        </div>
      </div>

      <!-- 2. 操作工具栏 -->
      <div class="paper-toolbar">
        <el-radio-group v-model="activeTab" size="small">
          <el-radio-button label="holdings">当前持仓 ({{ account?.holdings?.length || 0 }})</el-radio-button>
          <el-radio-button label="trade">模拟委托下单</el-radio-button>
          <el-radio-button label="pending">排队挂单 ({{ account?.pending_orders?.length || 0 }})</el-radio-button>
          <el-radio-button label="history">历史成交明细</el-radio-button>
        </el-radio-group>

        <div class="tb-actions">
          <el-button size="small" type="success" plain :loading="wechatTesting" @click="testWechatNotice">
            <el-icon><Bell /></el-icon>
            <span>测试微信信号直推</span>
          </el-button>
          <el-button size="small" :loading="loading" @click="fetchAccount">
            <el-icon><RefreshRight /></el-icon>
            <span>刷新账户</span>
          </el-button>
        </div>
      </div>

      <!-- 3. 标签内容区 -->
      <!-- TAB 1: 持仓明细 -->
      <div v-if="activeTab === 'holdings'" class="tab-pane">
        <el-table
          :data="account?.holdings || []"
          v-loading="loading"
          size="small"
          style="width: 100%"
          max-height="360"
        >
          <el-table-column prop="symbol" label="代码" width="90" />
          <el-table-column prop="name" label="标的名称" width="110" />
          <el-table-column prop="shares" label="持股数量" width="95" align="right">
            <template #default="{ row }">
              <span class="font-mono">{{ row.shares }} 股</span>
            </template>
          </el-table-column>
          <el-table-column prop="available_shares" label="可用股数 (T+1)" width="110" align="right">
            <template #default="{ row }">
              <span class="font-mono text-avail">{{ row.available_shares }} 股</span>
            </template>
          </el-table-column>
          <el-table-column prop="cost_price" label="成本均价" width="90" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥{{ row.cost_price.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="current_price" label="最新市价" width="90" align="right">
            <template #default="{ row }">
              <span class="font-mono font-bold">¥{{ row.current_price.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="floating_pnl" label="浮动盈亏" width="120" align="right">
            <template #default="{ row }">
              <span class="font-mono tabular-nums" :class="row.floating_pnl >= 0 ? 'color-up' : 'color-down'">
                {{ row.floating_pnl >= 0 ? '+' : '' }}¥{{ row.floating_pnl.toFixed(2) }}
                ({{ row.floating_pnl_pct >= 0 ? '+' : '' }}{{ row.floating_pnl_pct.toFixed(2) }}%)
              </span>
            </template>
          </el-table-column>
          <el-table-column label="快捷操作" width="90" align="center">
            <template #default="{ row }">
              <el-button
                size="small"
                type="danger"
                link
                :disabled="row.available_shares <= 0"
                @click="quickSell(row)"
              >
                平仓卖出
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="!loading && (!account?.holdings || account.holdings.length === 0)" class="empty-hint">
          <span>暂无任何模拟持仓，点击上方「模拟委托下单」即可开始构建投资组合！</span>
        </div>
      </div>

      <!-- TAB 2: 委托下单 -->
      <div v-if="activeTab === 'trade'" class="tab-pane trade-pane">
        <el-card shadow="never" class="trade-box">
          <el-form label-width="100px" size="small" class="order-form">
            <el-form-item label="交易方向">
              <el-radio-group v-model="orderForm.action" size="default">
                <el-radio-button label="BUY">买入 (BUY)</el-radio-button>
                <el-radio-button label="SELL">卖出 (SELL)</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="撮合模式">
              <el-radio-group v-model="orderForm.order_mode" size="small">
                <el-radio-button label="MARKET">五档即时撮合</el-radio-button>
                <el-radio-button label="LIMIT">限价排队撮合</el-radio-button>
              </el-radio-group>
              <div class="form-hint" v-if="orderForm.order_mode === 'MARKET'">
                ⚡ 基于实时五档盘口深度穿透吃单，超出深度叠加流动性冲击滑点
              </div>
              <div class="form-hint" v-else>
                ⏳ 限价劣于对手方最优价时进入买卖盘队列等待行情击穿撮合，支持随时主动撤单
              </div>
            </el-form-item>

            <el-form-item label="标的代码">
              <el-input
                v-model="orderForm.symbol"
                placeholder="如 600519、000001、510300"
                style="max-width: 260px;"
                @blur="onSymbolBlur"
              />
              <span class="form-tag" v-if="orderForm.name">{{ orderForm.name }}</span>
            </el-form-item>

            <el-form-item label="委托价格 (元)">
              <el-input-number
                v-model="orderForm.price"
                :min="0.01"
                :max="10000"
                :step="0.01"
                :precision="2"
                style="max-width: 260px;"
              />
              <span class="form-hint">留空或填写0将以当前市场极速快照价撮合</span>
            </el-form-item>

            <el-form-item label="委托股数">
              <el-input-number
                v-model="orderForm.shares"
                :min="100"
                :max="1000000"
                :step="100"
                style="max-width: 260px;"
              />
              <div class="quick-lot-chips">
                <el-button size="small" @click="setShares(100)">1手 (100股)</el-button>
                <el-button size="small" @click="setShares(300)">3手</el-button>
                <el-button size="small" @click="setShares(500)">5手</el-button>
                <el-button size="small" @click="setShares(1000)">10手</el-button>
                <el-button size="small" type="primary" plain @click="calcMaxShares(0.5)">半仓 (50%)</el-button>
                <el-button size="small" type="primary" plain @click="calcMaxShares(0.95)">满仓 (95%)</el-button>
              </div>
            </el-form-item>

            <el-form-item label="预估成交金额">
              <span class="est-amount font-mono tabular-nums">¥{{ formatMoney(estimatedAmount) }}</span>
              <span class="friction-note">
                (已仿真 券商佣金万0.876最低0.5元起(免5)，卖出印花税{{ isOrderETF ? '0%(ETF免征)' : '万5' }}，过户费万0.1)
              </span>
            </el-form-item>

            <el-form-item label="投资逻辑/备注">
              <el-input
                v-model="orderForm.reason"
                placeholder="如: 双均线金叉放量突破建仓 / ATR 头寸管理建议点位"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                :type="orderForm.action === 'BUY' ? 'danger' : 'success'"
                size="default"
                :loading="submitting"
                @click="handleSubmitOrder"
                style="min-width: 200px; font-weight: 700;"
              >
                {{ orderForm.action === 'BUY' ? '🔥 确认提交模拟买入' : '💰 确认提交模拟卖出' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- TAB 3: 排队挂单 -->
      <div v-if="activeTab === 'pending'" class="tab-pane">
        <el-table
          :data="account?.pending_orders || []"
          size="small"
          style="width: 100%"
          max-height="360"
        >
          <el-table-column prop="trade_time" label="委托时间" width="145" />
          <el-table-column prop="symbol" label="代码" width="85" />
          <el-table-column prop="name" label="标的名称" width="100" />
          <el-table-column prop="action" label="方向" width="70">
            <template #default="{ row }">
              <el-tag size="small" :type="row.action === 'BUY' ? 'danger' : 'success'">
                {{ row.action === 'BUY' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="委托限价" width="85" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥{{ row.price?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="shares" label="委托股数" width="85" align="right">
            <template #default="{ row }">
              <span class="font-mono">{{ row.shares }} 股</span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="委托/冻结金额" width="105" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥{{ formatMoney(row.amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="details" label="排队状态/撮合说明" min-width="160">
            <template #default="{ row }">
              <span class="text-hint-sub">{{ row.details || '挂单排队中' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button
                size="small"
                type="danger"
                plain
                :loading="cancellingOrderId === row.order_id"
                @click="handleCancelOrder(row.order_id)"
              >
                撤单
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!account?.pending_orders || account.pending_orders.length === 0" class="empty-hint">
          <span>暂无排队中的委托挂单，当限价未被盘口击穿时将在此显示并支持随时撤单</span>
        </div>
      </div>

      <!-- TAB 4: 历史成交明细 -->
      <div v-if="activeTab === 'history'" class="tab-pane">
        <el-table
          :data="account?.recent_trades || []"
          size="small"
          style="width: 100%"
          max-height="360"
        >
          <el-table-column prop="trade_time" label="成交时间" width="145" />
          <el-table-column prop="symbol" label="标的代码" width="85" />
          <el-table-column prop="name" label="标的名称" width="95" />
          <el-table-column prop="action" label="方向" width="75">
            <template #default="{ row }">
              <el-tag size="small" :type="row.action === 'BUY' ? 'danger' : 'success'">
                {{ row.action === 'BUY' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="成交价" width="85" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥{{ row.price?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="shares" label="成交股数" width="85" align="right">
            <template #default="{ row }">
              <span class="font-mono">{{ row.shares }} 股</span>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="成交金额" width="105" align="right">
            <template #default="{ row }">
              <span class="font-mono">¥{{ formatMoney(row.amount) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="fee" label="费用" width="75" align="right">
            <template #default="{ row }">
              <span class="font-mono text-fee">¥{{ row.fee?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="slippage_cost" label="滑点" width="75" align="right">
            <template #default="{ row }">
              <span class="font-mono text-fee">¥{{ (row.slippage_cost || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="realized_pnl" label="已实现盈亏" width="105" align="right">
            <template #default="{ row }">
              <span v-if="row.action === 'SELL'" class="font-mono" :class="row.realized_pnl >= 0 ? 'color-up' : 'color-down'">
                {{ row.realized_pnl >= 0 ? '+' : '' }}¥{{ row.realized_pnl?.toFixed(2) }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="details" label="撮合详情" min-width="140" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { quantApi, type PaperAccount } from '@/api/quant'
import { Bell, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  presetOrder?: {
    symbol: string
    name?: string
    price?: number
    shares?: number
    action?: 'BUY' | 'SELL'
  } | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val)
})

const activeTab = ref<'holdings' | 'trade' | 'pending' | 'history'>('holdings')
const loading = ref(false)
const submitting = ref(false)
const cancellingOrderId = ref<string | null>(null)
const wechatTesting = ref(false)
const account = ref<PaperAccount | null>(null)

const orderForm = ref({
  action: 'BUY' as 'BUY' | 'SELL',
  symbol: '600519',
  name: '',
  price: 0,
  shares: 100,
  order_mode: 'MARKET' as 'MARKET' | 'LIMIT',
  reason: ''
})

const estimatedAmount = computed(() => {
  const p = orderForm.value.price || 10
  return +(p * orderForm.value.shares).toFixed(2)
})

const isOrderETF = computed(() => {
  const sym = (orderForm.value.symbol || '').toLowerCase().replace(/^(sh|sz|bj)/, '')
  const name = (orderForm.value.name || '').toLowerCase()
  return (
    sym.startsWith('51') ||
    sym.startsWith('56') ||
    sym.startsWith('58') ||
    sym.startsWith('50') ||
    sym.startsWith('15') ||
    sym.startsWith('16') ||
    name.includes('etf')
  )
})

function formatMoney(val: number | undefined) {
  if (val === undefined || val === null) return '0.00'
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function setShares(cnt: number) {
  orderForm.value.shares = cnt
}

function calcMaxShares(ratio: number) {
  const availableCash = (account.value?.cash || 100000) * ratio
  const px = orderForm.value.price || 10
  const maxRaw = Math.floor(availableCash / px)
  const lots = Math.floor(maxRaw / 100)
  orderForm.value.shares = Math.max(100, lots * 100)
}

function quickSell(holding: any) {
  activeTab.value = 'trade'
  orderForm.value.action = 'SELL'
  orderForm.value.symbol = holding.symbol
  orderForm.value.name = holding.name
  orderForm.value.price = holding.current_price
  orderForm.value.shares = holding.available_shares
}

function onSymbolBlur() {
  if (!orderForm.value.symbol) return
  // 如果当前持仓有，则自动填充名称
  const found = account.value?.holdings?.find(h => h.symbol.toLowerCase() === orderForm.value.symbol.toLowerCase())
  if (found) {
    orderForm.value.name = found.name
    if (!orderForm.value.price) orderForm.value.price = found.current_price
  }
}

async function fetchAccount() {
  loading.value = true
  try {
    const res = await quantApi.getPaperAccount(true)
    account.value = ((res as any)?.data || res) as PaperAccount
  } catch (err: any) {
    console.error('获取模拟账户失败:', err)
  } finally {
    loading.value = false
  }
}

async function handleCancelOrder(orderId: string) {
  cancellingOrderId.value = orderId
  try {
    const res = await quantApi.cancelPaperOrder({ order_id: orderId })
    const resAny = res as any
    const isSuccess = resAny?.success === true || resAny?.data?.success === true
    if (isSuccess) {
      ElMessage.success(resAny?.message || resAny?.data?.message || '委托挂单已成功撤销')
      await fetchAccount()
    } else {
      ElMessage.error(resAny?.message || resAny?.data?.message || '撤单失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '撤单请求异常')
  } finally {
    cancellingOrderId.value = null
  }
}

async function handleSubmitOrder() {
  if (!orderForm.value.symbol) {
    ElMessage.warning('请输入标的代码')
    return
  }
  if (!orderForm.value.shares || orderForm.value.shares <= 0) {
    ElMessage.warning('委托数量必须大于0')
    return
  }

  submitting.value = true
  try {
    const isLimit = orderForm.value.order_mode === 'LIMIT'
    const res = await quantApi.submitPaperOrder({
      symbol: orderForm.value.symbol,
      action: orderForm.value.action,
      shares: orderForm.value.shares,
      price: orderForm.value.price > 0 ? orderForm.value.price : undefined,
      order_type: isLimit ? 'LIMIT' : 'MARKET',
      allow_queue: isLimit,
      reason: orderForm.value.reason
    })

    const resAny = res as any
    const isSuccess = resAny?.success === true || resAny?.data?.success === true
    if (isSuccess) {
      ElMessage.success(resAny?.message || resAny?.data?.message || '模拟委托提交成功！')
      await fetchAccount()
      if (isLimit) {
        activeTab.value = 'pending'
      } else {
        activeTab.value = 'holdings'
      }
    } else {
      ElMessage.error(resAny?.message || resAny?.data?.message || '委托失败')
    }
  } catch (err: any) {
    console.error('模拟下单失败:', err)
    ElMessage.error(err.message || '模拟下单失败')
  } finally {
    submitting.value = false
  }
}

async function testWechatNotice() {
  wechatTesting.value = true
  try {
    const res = await quantApi.testWechat()
    const data = (res as any)?.data || res
    ElMessage.success(data?.message || '微信机器人交易信号测试发送成功！')
  } catch (err: any) {
    ElMessage.error(err.message || '微信发送失败')
  } finally {
    wechatTesting.value = false
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      fetchAccount()
    }
  }
)

watch(
  () => props.presetOrder,
  (order) => {
    if (order) {
      activeTab.value = 'trade'
      orderForm.value.symbol = order.symbol
      orderForm.value.name = order.name || ''
      orderForm.value.price = order.price || 0
      orderForm.value.shares = order.shares || 100
      orderForm.value.action = order.action || 'BUY'
    }
  },
  { deep: true }
)

onMounted(() => {
  fetchAccount()
})
</script>

<style scoped lang="scss">
.paper-trading-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.account-overview-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;

  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }

  .ov-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    &.highlight {
      background: #eff6ff;
      padding: 8px 10px;
      border-radius: 6px;
      .ov-val {
        color: #2563eb;
      }
    }

    .ov-lbl {
      font-size: 11px;
      color: #64748b;
    }
    .ov-val {
      font-size: 18px;
      font-weight: 800;
      color: #0f172a;
    }
    .ov-sub {
      font-size: 11px;
      color: #94a3b8;
    }
    .text-cash {
      color: #059669;
    }
  }

  .pnl-group {
    display: flex;
    align-items: baseline;
    gap: 6px;
    .ov-val {
      font-size: 16px;
    }
    .ov-pct {
      font-size: 12px;
      font-weight: 700;
    }
  }
}

.paper-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .tb-actions {
    display: flex;
    gap: 8px;
  }
}

.tab-pane {
  min-height: 280px;
}

.empty-hint {
  text-align: center;
  padding: 40px 10px;
  color: #94a3b8;
  font-size: 13px;
}

.trade-box {
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.order-form {
  .form-tag {
    margin-left: 10px;
    font-weight: 600;
    color: #3b82f6;
  }
  .form-hint {
    margin-left: 10px;
    font-size: 11px;
    color: #94a3b8;
  }
  .quick-lot-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }
  .est-amount {
    font-size: 20px;
    font-weight: 800;
    color: #d97706;
  }
  .friction-note {
    margin-left: 10px;
    font-size: 11px;
    color: #64748b;
  }
}

.text-avail {
  color: #059669;
  font-weight: 600;
}
.text-fee {
  color: #94a3b8;
}

.color-up {
  color: #ef4444;
}
.color-down {
  color: #10b981;
}
</style>
