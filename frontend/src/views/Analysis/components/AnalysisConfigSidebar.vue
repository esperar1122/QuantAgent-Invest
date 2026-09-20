<template>
  <el-card class="config-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <h3>高级配置</h3>
        <el-tag type="warning" size="small">可选设置</el-tag>
      </div>
    </template>

    <div class="config-content">
      <!-- AI模型配置 -->
      <div class="config-section">
        <h4 class="config-title">🤖 AI模型配置</h4>
        <div class="model-config">
          <div class="model-item">
            <div class="model-label">
              <span>快速分析模型</span>
              <el-tooltip content="用于市场分析、新闻分析、基本面分析等" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <el-select v-model="modelSettings.quickAnalysisModel" size="small" style="width: 100%" filterable>
              <el-option
                v-for="model in availableModels"
                :key="`quick-${model.provider}/${model.model_name}`"
                :label="model.model_display_name || model.model_name"
                :value="model.model_name"
              >
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                  <span style="flex: 1;">{{ model.model_display_name || model.model_name }}</span>
                  <div style="display: flex; align-items: center; gap: 4px;">
                    <el-tag
                      v-if="model.capability_level"
                      :type="getCapabilityTagType(model.capability_level)"
                      size="small"
                      effect="plain"
                    >
                      {{ getCapabilityText(model.capability_level) }}
                    </el-tag>
                    <el-tag
                      v-if="isQuickAnalysisRole(model.suitable_roles)"
                      type="success"
                      size="small"
                      effect="plain"
                    >
                      ⚡快速
                    </el-tag>
                    <span style="font-size: 12px; color: #909399;">{{ model.provider }}</span>
                  </div>
                </div>
              </el-option>
            </el-select>
          </div>

          <div class="model-item">
            <div class="model-label">
              <span>深度决策模型</span>
              <el-tooltip content="用于研究管理者综合决策、风险管理者最终评估" placement="top">
                <el-icon class="help-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </div>
            <DeepModelSelector v-model="modelSettings.deepAnalysisModel" :available-models="availableModels" type="deep" size="small" width="100%" />
          </div>
        </div>

        <!-- 模型推荐提示 -->
        <el-alert
          v-if="modelRecommendation"
          :title="modelRecommendation.title"
          :type="modelRecommendation.type"
          :closable="false"
          style="margin-top: 12px;"
        >
          <template #default>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
              <div style="font-size: 13px; line-height: 1.8; flex: 1; white-space: pre-line;">
                {{ modelRecommendation.message }}
              </div>
              <el-button
                v-if="modelRecommendation.quickModel && modelRecommendation.deepModel"
                type="primary"
                size="small"
                @click="$emit('apply-recommended')"
                style="flex-shrink: 0;"
              >
                应用推荐
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 分析选项 -->
      <div class="config-section">
        <h4 class="config-title">⚙️ 分析选项</h4>
        <div class="option-list">
          <div class="option-item">
            <div class="option-info">
              <span class="option-name">情绪分析</span>
              <span class="option-desc">分析市场情绪和投资者心理</span>
            </div>
            <el-switch v-model="analysisForm.includeSentiment" />
          </div>

          <div class="option-item">
            <div class="option-info">
              <span class="option-name">风险评估</span>
              <span class="option-desc">包含详细的风险因素分析</span>
            </div>
            <el-switch v-model="analysisForm.includeRisk" />
          </div>

          <div class="option-item">
            <div class="option-info">
              <span class="option-name">语言偏好</span>
            </div>
            <el-select v-model="analysisForm.language" size="small" style="width: 100px">
              <el-option label="中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { InfoFilled } from '@element-plus/icons-vue'
import DeepModelSelector from '@/components/DeepModelSelector.vue'

defineProps<{
  modelSettings: {
    quickAnalysisModel: string
    deepAnalysisModel: string
  }
  analysisForm: {
    includeSentiment: boolean
    includeRisk: boolean
    language: string
  }
  availableModels: any[]
  modelRecommendation: any
}>()

defineEmits<{
  (e: 'apply-recommended'): void
}>()

const getCapabilityText = (level: number): string => {
  const texts: Record<number, string> = {
    1: '⚡基础',
    2: '📊标准',
    3: '🎯高级',
    4: '🔥专业',
    5: '👑旗舰'
  }
  return texts[level] || '📊标准'
}

const getCapabilityTagType = (level: number): 'success' | 'info' | 'warning' | 'danger' => {
  if (level >= 4) return 'danger'
  if (level >= 3) return 'warning'
  if (level >= 2) return 'success'
  return 'info'
}

const isQuickAnalysisRole = (roles: string[] | undefined): boolean => {
  if (!roles || !Array.isArray(roles)) return false
  return roles.includes('quick_analysis') || roles.includes('both')
}
</script>

<style scoped lang="scss">
.config-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

  :deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 16px 20px;
    border-radius: 16px 16px 0 0;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
  }

  .config-content {
    padding: 8px 0;

    .config-section {
      margin-bottom: 24px;

      &:last-child {
        margin-bottom: 0;
      }

      .config-title {
        font-size: 14px;
        font-weight: 600;
        color: #2d3748;
        margin: 0 0 12px 0;
      }

      .model-config {
        display: flex;
        flex-direction: column;
        gap: 16px;

        .model-item {
          .model-label {
            display: flex;
            align-items: center;
            font-size: 13px;
            color: #4a5568;
            margin-bottom: 6px;

            .help-icon {
              margin-left: 4px;
              color: #a0aec0;
              cursor: help;
            }
          }
        }
      }

      .option-list {
        display: flex;
        flex-direction: column;
        gap: 12px;

        .option-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f7fafc;

          &:last-child {
            border-bottom: none;
          }

          .option-info {
            display: flex;
            flex-direction: column;

            .option-name {
              font-size: 13px;
              color: #2d3748;
              font-weight: 500;
            }

            .option-desc {
              font-size: 11px;
              color: #a0aec0;
              margin-top: 2px;
            }
          }
        }
      }
    }
  }
}
</style>
