<template>
  <div class="progress-section">
    <el-card class="progress-card" shadow="hover">
      <template #header>
        <div class="progress-header">
          <h4>
            <el-icon class="rotating-icon">
              <Loading />
            </el-icon>
            分析进行中...
          </h4>
        </div>
      </template>

      <div class="progress-content">
        <!-- 总体进度信息 -->
        <div class="overall-progress-info">
          <div class="progress-stats">
            <div class="stat-item">
              <div class="stat-label">已用时间</div>
              <div class="stat-value num-tabular">{{ formatTime(progressInfo.elapsedTime) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">预计剩余</div>
              <div class="stat-value num-tabular">{{ formatTime(progressInfo.remainingTime) }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">预计总时长</div>
              <div class="stat-value num-tabular">{{ formatTime(progressInfo.totalTime) }}</div>
            </div>
          </div>
        </div>

        <!-- 进度条 -->
        <div class="progress-bar-section">
          <el-progress
            :percentage="Math.round(progressInfo.progress)"
            :stroke-width="12"
            :show-text="true"
            :status="getProgressStatus()"
            class="main-progress-bar"
          />
        </div>

        <!-- 当前任务详情 -->
        <div class="current-task-info">
          <div class="task-title">
            <el-icon class="task-icon">
              <Loading />
            </el-icon>
            {{ progressInfo.currentStep || '正在初始化分析引擎...' }}
          </div>
          <div
            class="task-description"
            style="white-space: pre-wrap; line-height: 1.6;"
          >
            {{ progressInfo.currentStepDescription || progressInfo.message || 'AI正在根据您的要求重点分析相关内容' }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

const props = defineProps<{
  progressInfo: {
    progress: number
    currentStep?: string
    currentStepDescription?: string
    message?: string
    elapsedTime?: number
    remainingTime?: number
    totalTime?: number
  }
}>()

const formatTime = (seconds?: number): string => {
  if (!seconds || seconds <= 0) return '0秒'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins > 0) {
    return `${mins}分${secs}秒`
  }
  return `${secs}秒`
}

const getProgressStatus = (): '' | 'success' | 'warning' | 'exception' => {
  if (props.progressInfo.progress >= 100) return 'success'
  return ''
}
</script>

<style scoped lang="scss">
.progress-section {
  margin-top: 24px;

  .progress-card {
    border-radius: 12px;
    border: 1px solid #e2e8f0;

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h4 {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
        color: #1e293b;
        font-size: 16px;
      }
    }

    .progress-content {
      .overall-progress-info {
        margin-bottom: 16px;

        .progress-stats {
          display: flex;
          justify-content: space-around;
          background: #f8fafc;
          padding: 12px;
          border-radius: 8px;

          .stat-item {
            text-align: center;

            .stat-label {
              font-size: 12px;
              color: #64748b;
              margin-bottom: 4px;
            }

            .stat-value {
              font-size: 16px;
              font-weight: 600;
              color: #0f172a;
            }
          }
        }
      }

      .progress-bar-section {
        margin-bottom: 16px;
      }

      .current-task-info {
        background: #f1f5f9;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;

        .task-title {
          font-weight: 600;
          color: #1e293b;
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 6px;
        }

        .task-description {
          font-size: 13px;
          color: #475569;
        }
      }
    }
  }
}

.rotating-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
