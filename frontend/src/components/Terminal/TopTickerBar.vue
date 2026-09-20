<template>
  <header class="terminal-top-bar">
    <!-- 左侧系统标识 -->
    <div class="brand-section">
      <div class="brand-badge">A股</div>
      <div class="brand-text">
        <div class="brand-title">A股 AI 投研终端</div>
        <div class="brand-sub">Multi-Agent Quant Research System</div>
      </div>
    </div>

    <!-- 中间四大核心指数行情条 -->
    <div class="index-ticker-strip">
      <div
        v-for="index in indices"
        :key="index.code"
        class="index-item clickable"
        :class="index.changePercent >= 0 ? 'up' : 'down'"
        @click="goToIndexResearch(index.fullCode || index.code)"
        title="点击穿透至个股研究·指数深度全景研判"
      >
        <span class="index-name">{{ index.name }}</span>
        <span class="index-price tabular-nums">{{ index.price.toFixed(2) }}</span>
        <span class="index-change tabular-nums">
          {{ index.changePercent >= 0 ? '+' : '' }}{{ index.changePercent.toFixed(2) }}%
        </span>
      </div>
    </div>

    <!-- 右侧交易状态、主题切换与返回工作台 -->
    <div class="status-section">
      <div class="market-status-pill">
        <span class="pulse-dot" :class="marketStatusClass"></span>
        <span class="status-text">{{ marketStatusText }}</span>
        <span class="live-clock tabular-nums">{{ currentTime }}</span>
      </div>

      <div class="top-bar-divider"></div>

      <!-- 终端操作按钮组：通知中心、全屏、深浅主题、系统设置 -->
      <div class="top-actions">
        <!-- 消息通知 -->
        <el-tooltip content="消息通知中心" placement="bottom">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notif-badge">
            <button class="top-action-btn" @click="openDrawer">
              <el-icon :size="15"><Bell /></el-icon>
            </button>
          </el-badge>
        </el-tooltip>

        <!-- 全屏切换 -->
        <el-tooltip content="全屏切换" placement="bottom">
          <button class="top-action-btn" @click="toggleFullscreen">
            <el-icon :size="15"><FullScreen /></el-icon>
          </button>
        </el-tooltip>

        <!-- 深浅主题切换 -->
        <el-tooltip :content="isDark ? '切换为浅色日间模式' : '切换为专业深色终端'" placement="bottom">
          <button class="top-action-btn" @click="toggleTheme">
            <el-icon :size="15"><Sunny v-if="isDark" /><Moon v-else /></el-icon>
          </button>
        </el-tooltip>

        <!-- 系统设置 -->
        <el-tooltip content="系统设置与大模型配置" placement="bottom">
          <button class="top-action-btn" @click="goToSettings">
            <el-icon :size="15"><Setting /></el-icon>
          </button>
        </el-tooltip>
      </div>
    </div>
  </header>

  <!-- 消息通知抽屉 -->
  <el-drawer v-model="drawerVisible" direction="rtl" size="360px" :with-header="true" title="消息中心">
    <div class="notif-toolbar">
      <el-segmented v-model="filter" :options="[{label: '全部', value: 'all'}, {label: '未读', value: 'unread'}]" size="small" />
      <el-button size="small" text type="primary" @click="onMarkAllRead" :disabled="unreadCount===0">全部已读</el-button>
    </div>
    <el-scrollbar max-height="calc(100vh - 160px)">
      <el-empty v-if="items.length===0" description="暂无通知" />
      <div v-else class="notif-list">
        <div v-for="n in items" :key="n.id" class="notif-item" :class="{unread: n.status==='unread'}">
          <div class="row">
            <el-tag :type="tagType(n.type)" size="small">{{ typeLabel(n.type) }}</el-tag>
            <span class="time">{{ toLocal(n.created_at) }}</span>
          </div>
          <div class="title" @click="go(n)">{{ n.title }}</div>
          <div class="content" v-if="n.content">{{ n.content }}</div>
          <div class="ops">
            <el-button size="small" text type="primary" @click="go(n)" :disabled="!n.link">查看</el-button>
            <el-button size="small" text @click="onMarkRead(n)" v-if="n.status==='unread'">标记已读</el-button>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { Sunny, Moon, FullScreen, Bell, Setting } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'
import { stocksApi } from '@/api/stocks'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const notifStore = useNotificationStore()

const { unreadCount, items } = storeToRefs(notifStore)
const drawerVisible = ref(false)
const filter = ref<'all' | 'unread'>('all')
let timerCount: any = null
let timerList: any = null

const isDark = computed(() => appStore.isDarkTheme)

function toggleTheme() {
  appStore.setTheme(isDark.value ? 'light' : 'dark')
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    document.documentElement.requestFullscreen()
  }
}

function goToSettings() {
  router.push('/terminal/settings/config')
}

function openDrawer() {
  drawerVisible.value = true
  notifStore.loadList(filter.value)
}

function onMarkRead(n: any) {
  notifStore.markRead(n.id)
}

function onMarkAllRead() {
  notifStore.markAllRead()
}

function typeLabel(t: string) {
  return t === 'analysis' ? '分析' : t === 'alert' ? '预警' : '系统'
}

function tagType(t: string) {
  return t === 'analysis' ? 'success' : t === 'alert' ? 'warning' : 'info'
}

function toLocal(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function go(n: any) {
  if (n.link) window.open(n.link, '_blank')
}

function goToIndexResearch(code: string) {
  router.push({ path: '/terminal/stock', query: { code } })
}

const indices = ref([
  { code: '000001', fullCode: 'sh000001', name: '上证指数', price: 3911.87, changePercent: 0.94 },
  { code: '399001', fullCode: 'sz399001', name: '深证成指', price: 13640.87, changePercent: 1.72 },
  { code: '399006', fullCode: 'sz399006', name: '创业板指', price: 3372.68, changePercent: 2.25 },
  { code: '000680', fullCode: 'sh000680', name: '科创综指', price: 1948.21, changePercent: 3.23 }
])

async function fetchLiveIndices() {
  await Promise.allSettled(
    indices.value.map(async (idx) => {
      try {
        const res = await stocksApi.getQuote(idx.fullCode)
        const q = (res as any)?.data || res
        if (q && (q.price !== undefined || q.close !== undefined)) {
          idx.price = Number(q.price ?? q.close)
          idx.changePercent = Number(q.change_percent ?? q.pct_chg ?? 0)
        }
      } catch (e) {
        // 保持平滑
      }
    })
  )
}

const currentTime = ref('09:41:26')
const marketStatusText = ref('交易中')
const marketStatusClass = ref('status-open')
let timer: number | null = null
let tickerTimer: number | null = null

function updateMarketStatus(now: Date) {
  const day = now.getDay()
  if (day === 0 || day === 6) {
    marketStatusText.value = '周末休市'
    marketStatusClass.value = 'status-closed'
    return
  }

  const h = now.getHours()
  const m = now.getMinutes()
  const totalM = h * 60 + m

  // 9:15 - 9:30 盘前集合竞价
  if (totalM >= 555 && totalM < 570) {
    marketStatusText.value = '集合竞价'
    marketStatusClass.value = 'status-auction'
  } else if ((totalM >= 570 && totalM <= 690) || (totalM >= 780 && totalM <= 900)) {
    // 9:30 - 11:30 or 13:00 - 15:00
    marketStatusText.value = '交易中'
    marketStatusClass.value = 'status-open'
  } else if (totalM > 690 && totalM < 780) {
    marketStatusText.value = '午间休市'
    marketStatusClass.value = 'status-paused'
  } else {
    marketStatusText.value = '已收盘'
    marketStatusClass.value = 'status-closed'
  }
}

const updateClock = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`
  updateMarketStatus(now)
}

onMounted(() => {
  updateClock()
  timer = window.setInterval(updateClock, 1000)
  fetchLiveIndices()
  tickerTimer = window.setInterval(fetchLiveIndices, 15000)

  // 消息通知初始化
  notifStore.refreshUnreadCount()
  notifStore.connect()
  timerCount = setInterval(() => notifStore.refreshUnreadCount(), 30000)

  watch(
    drawerVisible,
    (v) => {
      if (v) {
        notifStore.loadList(filter.value)
        timerList = setInterval(() => notifStore.loadList(filter.value), 60000)
      } else if (timerList) {
        clearInterval(timerList)
        timerList = null
      }
    },
    { immediate: true }
  )

  watch(filter, () => {
    if (drawerVisible.value) notifStore.loadList(filter.value)
  })

  watch(
    () => authStore.token,
    () => {
      notifStore.connect()
    }
  )
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (tickerTimer) clearInterval(tickerTimer)
  if (timerCount) clearInterval(timerCount)
  if (timerList) clearInterval(timerList)
  notifStore.disconnect()
})
</script>

<style scoped lang="scss">
.terminal-top-bar {
  height: 66px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ec;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 999;
  user-select: none;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 12px;

  .brand-badge {
    background-color: #eff8ff;
    color: #175cd3;
    border: 1px solid #b2ddff;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    line-height: 1.2;
  }

  .brand-text {
    .brand-title {
      font-size: 15px;
      font-weight: 700;
      color: #101828;
      line-height: 1.2;
      letter-spacing: -0.01em;
    }
    .brand-sub {
      font-size: 11px;
      color: #667085;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin-top: 2px;
    }
  }
}

.index-ticker-strip {
  display: flex;
  align-items: center;
  gap: 28px;

  .index-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;

    &.clickable {
      cursor: pointer;
      padding: 3px 8px;
      border-radius: 4px;
      transition: all 0.15s ease;

      &:hover {
        background-color: #f2f4f7;
        transform: translateY(-1px);
      }
    }

    .index-name {
      color: #475467;
      font-weight: 500;
    }

    .index-price {
      font-weight: 600;
    }

    .index-change {
      font-weight: 600;
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 12px;
    }

    &.up {
      .index-price {
        color: #d92d20;
      }
      .index-change {
        color: #d92d20;
        background-color: #fef3f2;
      }
    }

    &.down {
      .index-price {
        color: #039855;
      }
      .index-change {
        color: #039855;
        background-color: #edfcf2;
      }
    }
  }
}

.status-section {
  display: flex;
  align-items: center;

  .market-status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background-color: #f8fafc;
    border: 1px solid #e4e7ec;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;

    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: #12b76a;
      box-shadow: 0 0 0 2px rgba(18, 183, 106, 0.2);

      &.status-open {
        background-color: #12b76a;
        box-shadow: 0 0 0 2px rgba(18, 183, 106, 0.25);
      }
      &.status-auction {
        background-color: #f79009;
        box-shadow: 0 0 0 2px rgba(247, 144, 9, 0.25);
      }
      &.status-paused,
      &.status-closed {
        background-color: #98a2b3;
        box-shadow: none;
      }
    }

    .status-text {
      color: #344054;
      font-weight: 600;
    }

    .live-clock {
      color: #667085;
      font-weight: 500;
      border-left: 1px solid #e4e7ec;
      padding-left: 8px;
    }
  }

  .top-bar-divider {
    width: 1px;
    height: 20px;
    background-color: #e4e7ec;
    margin: 0 12px;
  }

  .top-actions {
    display: flex;
    align-items: center;
    gap: 8px;

    .top-action-btn {
      width: 32px;
      height: 32px;
      border-radius: 6px;
      border: 1px solid #d0d5dd;
      background-color: #ffffff;
      color: #475467;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover {
        background-color: #f8fafc;
        color: #175cd3;
        border-color: #b2ddff;
      }
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
  font-family: 'JetBrains Mono', 'Roboto Mono', Menlo, Consolas, monospace;
}

/* 通知抽屉样式 */
.notif-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.notif-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.notif-item {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e4e7ec;
  background-color: #ffffff;
  transition: all 0.15s ease;

  &.unread {
    background-color: #f8fafc;
    border-color: #b2ddff;
  }

  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    color: #667085;
    margin-bottom: 4px;
  }

  .title {
    font-size: 13px;
    font-weight: 600;
    color: #101828;
    cursor: pointer;
    margin-bottom: 4px;

    &:hover {
      color: #175cd3;
      text-decoration: underline;
    }
  }

  .content {
    font-size: 12px;
    color: #475467;
    line-height: 1.4;
  }

  .ops {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }
}
</style>
