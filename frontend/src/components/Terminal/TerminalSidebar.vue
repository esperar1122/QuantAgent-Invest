<template>
  <aside class="terminal-sidebar">
    <div class="nav-scroll-area">
      <!-- 投研核心分组 (RESEARCH) -->
      <div class="nav-group">
        <div class="group-title">RESEARCH · 投研核心</div>
        <router-link to="/terminal/dashboard" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Odometer /></el-icon>
          <span class="nav-label">系统仪表盘</span>
        </router-link>
        <router-link to="/terminal/overview" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><DataBoard /></el-icon>
          <span class="nav-label">市场总览</span>
        </router-link>
        <router-link to="/terminal/screening" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Collection /></el-icon>
          <span class="nav-label">A股股票池</span>
        </router-link>
        <router-link to="/terminal/stock" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><TrendCharts /></el-icon>
          <span class="nav-label">个股与指数研究</span>
        </router-link>
        <router-link to="/terminal/favorites" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Star /></el-icon>
          <span class="nav-label">我的自选股</span>
        </router-link>
      </div>

      <!-- 智能体与大模型分组 (INTELLIGENCE) -->
      <div class="nav-group">
        <div class="group-title">INTELLIGENCE · 智能体与AI</div>
        <router-link to="/terminal/workflow" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Connection /></el-icon>
          <span class="nav-label">Agent 工作流</span>
        </router-link>
        <router-link to="/terminal/analysis/single" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Cpu /></el-icon>
          <span class="nav-label">单股深度分析</span>
          <span class="badge-ai">LLM</span>
        </router-link>
        <router-link to="/terminal/analysis/batch" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Files /></el-icon>
          <span class="nav-label">批量并发分析</span>
        </router-link>
        <router-link to="/terminal/report" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Document /></el-icon>
          <span class="nav-label">全息投研研报</span>
        </router-link>
        <router-link to="/terminal/reports" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Reading /></el-icon>
          <span class="nav-label">分析报告库</span>
        </router-link>
      </div>

      <!-- 调度与系统运维 (SYSTEM & OPS) -->
      <div class="nav-group">
        <div class="group-title">OPERATIONS · 调度与系统</div>
        <router-link to="/terminal/tasks" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><List /></el-icon>
          <span class="nav-label">任务中心</span>
        </router-link>
        <router-link to="/terminal/system/sync" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Refresh /></el-icon>
          <span class="nav-label">多源数据同步</span>
        </router-link>
        <router-link to="/terminal/settings/config" class="nav-item" active-class="active">
          <el-icon class="nav-icon"><Setting /></el-icon>
          <span class="nav-label">系统设置与模型</span>
        </router-link>
      </div>
    </div>

    <!-- 底部：用户身份与终端信息 -->
    <div class="sidebar-footer">
      <div class="user-card">
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

      <div class="terminal-badge">
        <div class="badge-header">
          <span class="pulse-indicator"></span>
          <span class="badge-title">QuantAgent-Invest</span>
        </div>
        <p class="badge-desc">AI 智能多智能体自主投研决策系统</p>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  DataBoard,
  Collection,
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
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const userName = computed(() => authStore.user?.username || '投研研究员')
const userAvatar = computed(() => authStore.user?.avatar || undefined)
const userRole = computed(() => (authStore.user?.is_admin ? '系统管理员' : '量化研究员'))

async function handleLogout() {
  await authStore.logout()
  ElMessage.success('已安全退出登录')
  router.push('/login')
}
</script>

<style scoped lang="scss">
.terminal-sidebar {
  width: 228px;
  height: calc(100vh - 66px);
  background-color: #ffffff;
  border-right: 1px solid #e4e7ec;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 14px 12px 12px;
  user-select: none;
  flex-shrink: 0;
}

.nav-scroll-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
  display: flex;
  flex-direction: column;
  gap: 16px;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background-color: #e4e7ec;
    border-radius: 2px;
  }
}

.nav-group {
  .group-title {
    font-size: 10px;
    font-weight: 700;
    color: #98a2b3;
    letter-spacing: 0.06em;
    padding: 0 8px;
    margin-bottom: 5px;
    text-transform: uppercase;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 7px 10px;
    border-radius: 6px;
    text-decoration: none;
    color: #344054;
    font-size: 12.5px;
    font-weight: 500;
    transition: all 0.15s ease;
    margin-bottom: 2px;
    position: relative;

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

  .terminal-badge {
    background-color: #f8fafc;
    border: 1px solid #eaecf0;
    border-radius: 6px;
    padding: 7px 10px;

    .badge-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 2px;

      .pulse-indicator {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #12b76a;
        box-shadow: 0 0 0 2px rgba(18, 183, 106, 0.2);
      }

      .badge-title {
        font-size: 11px;
        font-weight: 700;
        color: #1d2939;
        letter-spacing: -0.01em;
      }
    }

    .badge-desc {
      font-size: 10px;
      color: #98a2b3;
      margin: 0;
      line-height: 1.3;
    }
  }
}
</style>
