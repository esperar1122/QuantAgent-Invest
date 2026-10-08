<template>
  <aside 
    class="terminal-sidebar" 
    :class="{ 'is-collapsed': isCollapsed, 'is-resizing': isResizing }"
    :style="{ width: `${currentWidth}px` }"
  >
    <!-- 1. 顶部：终端标识与折叠/展开按钮 -->
    <div class="sidebar-top-header">
      <div v-if="!isCollapsed" class="brand-group">
        <span class="pulse-indicator"></span>
        <span class="brand-title">QUANT TERMINAL</span>
      </div>
      <el-tooltip 
        :content="isCollapsed ? '展开导航栏' : '收起导航栏'" 
        placement="right" 
        :show-after="300"
      >
        <button class="collapse-toggle-btn" @click="toggleCollapse">
          <el-icon :size="15">
            <Expand v-if="isCollapsed" />
            <Fold v-else />
          </el-icon>
        </button>
      </el-tooltip>
    </div>

    <!-- 2. 中间：导航菜单滚动区域 -->
    <div class="nav-scroll-area">
      <!-- 投研核心分组 (RESEARCH) -->
      <div class="nav-group">
        <div v-if="!isCollapsed" class="group-title">RESEARCH · 投研核心</div>
        <div v-else class="group-divider"></div>

        <el-tooltip content="系统仪表盘" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/dashboard" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Odometer /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">系统仪表盘</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="市场总览" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/overview" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><DataBoard /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">市场总览</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="A股股票池" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/screening" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Collection /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">A股股票池</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="场内ETF专区" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/etf" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Coin /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">场内ETF专区</span>
            <span v-if="!isCollapsed" class="badge-hot">ETF</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="个股与指数研究" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/stock" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><TrendCharts /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">个股与指数研究</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="策略历史回测" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/backtest" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Odometer /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">策略历史回测</span>
            <span v-if="!isCollapsed" class="badge-hot">回测</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="我的自选股" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/favorites" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Star /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">我的自选股</span>
          </router-link>
        </el-tooltip>
      </div>

      <!-- 智能体与大模型分组 (INTELLIGENCE) -->
      <div class="nav-group">
        <div v-if="!isCollapsed" class="group-title">INTELLIGENCE · 智能体与AI</div>
        <div v-else class="group-divider"></div>

        <el-tooltip content="Agent 工作流" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/workflow" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Connection /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">Agent 工作流</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="单股深度分析" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/analysis/single" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Cpu /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">单股深度分析</span>
            <span v-if="!isCollapsed" class="badge-ai">LLM</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="批量并发分析" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/analysis/batch" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Files /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">批量并发分析</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="全息投研研报" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/report" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Document /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">全息投研研报</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="分析报告库" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/reports" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Reading /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">分析报告库</span>
          </router-link>
        </el-tooltip>
      </div>

      <!-- 调度与系统运维 (SYSTEM & OPS) -->
      <div class="nav-group">
        <div v-if="!isCollapsed" class="group-title">OPERATIONS · 调度与系统</div>
        <div v-else class="group-divider"></div>

        <el-tooltip content="任务中心" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/tasks" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><List /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">任务中心</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="多源数据同步" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/system/sync" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Refresh /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">多源数据同步</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="系统设置与模型" placement="right" :disabled="!isCollapsed" :show-after="150">
          <router-link to="/terminal/settings/config" class="nav-item" active-class="active">
            <el-icon class="nav-icon"><Setting /></el-icon>
            <span v-if="!isCollapsed" class="nav-label">系统设置与模型</span>
          </router-link>
        </el-tooltip>
      </div>
    </div>

    <!-- 3. 底部：用户身份与系统终端徽标 -->
    <div class="sidebar-footer">
      <!-- 展开状态：完整用户卡片 -->
      <div v-if="!isCollapsed" class="user-card">
        <div class="user-avatar-wrap">
          <el-avatar :size="28" :src="userAvatar">
            <el-icon :size="14"><User /></el-icon>
          </el-avatar>
        </div>
        <div class="user-meta">
          <span class="user-name">{{ userName }}</span>
          <span class="user-role">{{ userRole }}</span>
        </div>
        <el-tooltip content="退出登录" placement="top">
          <button class="logout-btn" @click="handleLogout">
            <el-icon :size="14"><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <!-- 折叠状态：紧凑图标头像与退出按钮 -->
      <div v-else class="collapsed-user-card">
        <el-tooltip :content="`${userName} (${userRole})`" placement="right">
          <el-avatar :size="30" :src="userAvatar" class="mini-avatar">
            <el-icon :size="15"><User /></el-icon>
          </el-avatar>
        </el-tooltip>
        <el-tooltip content="退出登录" placement="right">
          <button class="logout-btn mini" @click="handleLogout">
            <el-icon :size="14"><SwitchButton /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <!-- 展开状态系统徽标 -->
      <div v-if="!isCollapsed" class="terminal-badge">
        <div class="badge-header">
          <span class="pulse-indicator"></span>
          <span class="badge-title">QuantAgent-Invest</span>
        </div>
        <p class="badge-desc">AI 智能多智能体自主投研系统</p>
      </div>
    </div>

    <!-- 4. 右侧边缘：可左右拖拽调整宽度的分隔线 (最大限制 228px) -->
    <div 
      class="sidebar-resizer" 
      :class="{ 'is-resizing': isResizing, 'is-collapsed-resizer': isCollapsed }" 
      @mousedown="startResize"
      title="左右拖动调整宽度"
    >
      <div class="resizer-handle-line"></div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  DataBoard,
  Collection,
  Coin,
  TrendCharts,
  Star,
  Connection,
  Cpu,
  Files,
  Document,
  Reading,
  List,
  Refresh,
  Setting,
  User,
  SwitchButton,
  Fold,
  Expand
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 用户身份信息
const userName = computed(() => authStore.user?.username || '投研研究员')
const userAvatar = computed(() => authStore.user?.avatar || undefined)
const userRole = computed(() => (authStore.user?.is_admin ? '系统管理员' : '量化研究员'))

async function handleLogout() {
  await authStore.logout()
  ElMessage.success('已安全退出登录')
  router.push('/login')
}

// ================= 折叠与宽度调整系统 =================
// 宽度规范：最大限制 228px，展开最小 160px，折叠后 60px
const MAX_WIDTH = 228
const MIN_EXPANDED_WIDTH = 160
const COLLAPSED_WIDTH = 60

const isCollapsed = ref<boolean>(localStorage.getItem('terminal_sidebar_collapsed') === 'true')
const initialSavedWidth = Number(localStorage.getItem('terminal_sidebar_width')) || MAX_WIDTH
const savedWidth = ref<number>(Math.min(MAX_WIDTH, Math.max(MIN_EXPANDED_WIDTH, initialSavedWidth)))
const isResizing = ref(false)

const currentWidth = computed(() => {
  return isCollapsed.value ? COLLAPSED_WIDTH : savedWidth.value
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('terminal_sidebar_collapsed', String(isCollapsed.value))
  
  // 触发全局 resize 事件以通知图表自适应重排
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'))
  }, 220)
}

// 拖拽调整宽度逻辑
let dragStartX = 0
let dragStartWidth = 0

function startResize(e: MouseEvent) {
  e.preventDefault()
  isResizing.value = true
  dragStartX = e.clientX
  dragStartWidth = currentWidth.value

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'

  window.addEventListener('mousemove', handleResizeMove)
  window.addEventListener('mouseup', handleResizeEnd)
}

function handleResizeMove(e: MouseEvent) {
  if (!isResizing.value) return
  e.preventDefault()

  const deltaX = e.clientX - dragStartX
  let targetWidth = dragStartWidth + deltaX

  // 如果处于折叠状态向右拖拽超过 100px，则自动触发展开
  if (isCollapsed.value) {
    if (e.clientX > 110) {
      isCollapsed.value = false
      localStorage.setItem('terminal_sidebar_collapsed', 'false')
      dragStartX = e.clientX
      dragStartWidth = MIN_EXPANDED_WIDTH
      savedWidth.value = Math.min(MAX_WIDTH, Math.max(MIN_EXPANDED_WIDTH, e.clientX))
    }
    return
  }

  // 展开状态下：如果拖拽至小于 110px，自动吸附折叠
  if (targetWidth < 110) {
    isCollapsed.value = true
    localStorage.setItem('terminal_sidebar_collapsed', 'true')
    window.dispatchEvent(new Event('resize'))
    return
  }

  // 严格限制最大宽度不超过 228px
  const clampedWidth = Math.min(MAX_WIDTH, Math.max(MIN_EXPANDED_WIDTH, targetWidth))
  savedWidth.value = clampedWidth
  localStorage.setItem('terminal_sidebar_width', String(clampedWidth))

  // 实时通知右侧主工作区及图表适应
  window.dispatchEvent(new Event('resize'))
}

function handleResizeEnd() {
  if (!isResizing.value) return
  isResizing.value = false

  document.body.style.cursor = ''
  document.body.style.userSelect = ''

  window.removeEventListener('mousemove', handleResizeMove)
  window.removeEventListener('mouseup', handleResizeEnd)

  setTimeout(() => {
    window.dispatchEvent(new Event('resize'))
  }, 50)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', handleResizeMove)
  window.removeEventListener('mouseup', handleResizeEnd)
})
</script>

<style scoped lang="scss">
.terminal-sidebar {
  position: relative;
  height: 100%;
  background-color: #ffffff;
  border-right: 1px solid #e4e7ec;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 10px 12px;
  user-select: none;
  flex-shrink: 0;
  transition: width 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;

  &.is-resizing {
    transition: none; // 拖拽时关闭 transition，确保零延迟跟手动效
  }

  &.is-collapsed {
    padding: 12px 6px 12px;
  }
}

// 顶部品牌栏与折叠切换按钮
.sidebar-top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px 10px;
  border-bottom: 1px solid #f2f4f7;
  margin-bottom: 8px;
  flex-shrink: 0;
  min-height: 28px;

  .brand-group {
    display: flex;
    align-items: center;
    gap: 6px;
    overflow: hidden;
    white-space: nowrap;

    .pulse-indicator {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: #12b76a;
      box-shadow: 0 0 0 2px rgba(18, 183, 106, 0.2);
      flex-shrink: 0;
    }

    .brand-text {
      font-size: 11px;
      font-weight: 700;
      color: #344054;
      letter-spacing: 0.05em;
    }
  }

  .collapse-toggle-btn {
    border: none;
    background: transparent;
    padding: 4px;
    border-radius: 4px;
    color: #667085;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
    margin-left: auto;

    &:hover {
      background-color: #f2f4f7;
      color: #175cd3;
    }
  }
}

.is-collapsed .sidebar-top-header {
  justify-content: center;
  .collapse-toggle-btn {
    margin-left: 0;
  }
}

// 导航菜单区域
.nav-scroll-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
  display: flex;
  flex-direction: column;
  gap: 12px;

  &::-webkit-scrollbar {
    width: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: #eaecf0;
    border-radius: 2px;
  }
}

.nav-group {
  .group-title {
    font-size: 10px;
    font-weight: 700;
    color: #98a2b3;
    letter-spacing: 0.05em;
    padding: 0 8px;
    margin-bottom: 4px;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .group-divider {
    height: 1px;
    background-color: #f2f4f7;
    margin: 6px 4px;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 9px;
    border-radius: 6px;
    text-decoration: none;
    color: #344054;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.15s ease;
    margin-bottom: 2px;
    position: relative;
    white-space: nowrap;

    .nav-icon {
      font-size: 15px;
      color: #667085;
      transition: color 0.15s ease;
      flex-shrink: 0;
    }

    .nav-label {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .badge-ai {
      font-size: 9px;
      font-weight: 700;
      color: #175cd3;
      background: #eff8ff;
      border: 1px solid #b2ddff;
      padding: 0 4px;
      border-radius: 3px;
      line-height: 14px;
      flex-shrink: 0;
    }

    .badge-hot {
      font-size: 9px;
      font-weight: 700;
      color: #ea580c;
      background: #fff7ed;
      border: 1px solid #fed7aa;
      padding: 0 4px;
      border-radius: 3px;
      line-height: 14px;
      flex-shrink: 0;
    }

    &:hover {
      background-color: #f8fafc;
      color: #101828;
      .nav-icon {
        color: #175cd3;
      }
    }

    &.active {
      background-color: #eff8ff;
      color: #175cd3;
      font-weight: 600;

      .nav-icon {
        color: #175cd3;
      }
    }
  }
}

// 折叠状态下的导航居中
.is-collapsed .nav-group .nav-item {
  justify-content: center;
  padding: 8px 0;
}

// 底部用户卡片与徽章
.sidebar-footer {
  border-top: 1px solid #f2f4f7;
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;

  .user-card {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background-color: #f8fafc;
    border: 1px solid #eaecf0;
    border-radius: 6px;

    .user-avatar-wrap {
      flex-shrink: 0;
    }

    .user-meta {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;

      .user-name {
        font-size: 12px;
        font-weight: 600;
        color: #101828;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .user-role {
        font-size: 10px;
        color: #667085;
      }
    }

    .logout-btn {
      background: none;
      border: none;
      padding: 4px;
      border-radius: 4px;
      color: #98a2b3;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;

      &:hover {
        background-color: #fee4e2;
        color: #d92d20;
      }
    }
  }

  .collapsed-user-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;

    .mini-avatar {
      cursor: pointer;
      box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
    }

    .logout-btn.mini {
      background: none;
      border: none;
      padding: 4px;
      border-radius: 4px;
      color: #98a2b3;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;

      &:hover {
        background-color: #fee4e2;
        color: #d92d20;
      }
    }
  }

  .terminal-badge {
    background-color: #f8fafc;
    border: 1px solid #eaecf0;
    border-radius: 6px;
    padding: 6px 8px;

    .badge-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 2px;

      .pulse-indicator {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background-color: #12b76a;
      }

      .badge-title {
        font-size: 11px;
        font-weight: 700;
        color: #1d2939;
        letter-spacing: -0.01em;
      }
    }

    .badge-desc {
      font-size: 9px;
      color: #98a2b3;
      margin: 0;
      line-height: 1.3;
    }
  }
}

// 导航栏右侧可拖拽的分隔线
.sidebar-resizer {
  position: absolute;
  top: 0;
  right: -3px;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease;

  .resizer-handle-line {
    width: 2px;
    height: 100%;
    background-color: transparent;
    transition: background-color 0.15s ease;
  }

  &:hover .resizer-handle-line,
  &.is-resizing .resizer-handle-line {
    background-color: #175cd3;
  }

  &:hover,
  &.is-resizing {
    background-color: rgba(23, 92, 211, 0.08);
  }

  &.is-collapsed-resizer {
    cursor: e-resize;
  }
}
</style>
