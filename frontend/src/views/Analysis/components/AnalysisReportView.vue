<template>
  <div v-if="results" class="results-section">
    <el-card class="results-card" shadow="hover">
      <template #header>
        <div class="results-header">
          <h3>📊 分析结果与智能研报</h3>
          <div class="result-meta">
            <el-tag type="success">{{ results.symbol || results.stock_symbol || form?.symbol || form?.stockCode }}</el-tag>
            <el-tag>{{ results.analysis_date }}</el-tag>
            <el-tag v-if="results.model_info && results.model_info !== 'Unknown'" type="info">
              <el-icon><Cpu /></el-icon>
              {{ results.model_info }}
            </el-tag>
          </div>
        </div>
      </template>

      <div class="results-content">
        <!-- 风险提示 -->
        <div class="risk-disclaimer">
          <el-alert
            type="warning"
            :closable="false"
            show-icon
          >
            <template #title>
              <div class="disclaimer-content">
                <el-icon class="disclaimer-icon"><WarningFilled /></el-icon>
                <div class="disclaimer-text">
                  <p style="margin: 0 0 8px 0;"><strong>⚠️ 重要风险提示与免责声明</strong></p>
                  <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>工具性质：</strong>本系统为股票量化分析辅助工具，基于多智能体与公开数据分析，不构成投资咨询建议。</li>
                    <li><strong>非投资建议：</strong>所有评级、置信度及测算结论仅供技术研讨，不构成任何买卖邀约。</li>
                    <li><strong>独立决策：</strong>金融市场具有不确定性与风险，投资者须基于独立审慎思考自主做出投资决策。</li>
                  </ul>
                </div>
              </div>
            </template>
          </el-alert>
        </div>

        <!-- 最终决策 -->
        <div v-if="results.decision" class="decision-section">
          <h4>🎯 分析决策参考</h4>
          <div class="decision-card">
            <div class="decision-main">
              <div class="decision-action">
                <span class="label">分析倾向:</span>
                <el-tag
                  :type="getActionTagType(results.decision.action)"
                  size="large"
                >
                  {{ results.decision.action }}
                </el-tag>
                <el-tag type="info" size="small" style="margin-left: 8px;">仅供参考</el-tag>
              </div>

              <div class="decision-metrics">
                <div class="metric-item">
                  <span class="label">参考价格:</span>
                  <span class="value num-tabular">{{ results.decision.target_price }}</span>
                </div>
                <div class="metric-item">
                  <span class="label">模型置信度:</span>
                  <span class="value num-tabular">{{ (results.decision.confidence * 100).toFixed(1) }}%</span>
                  <el-tooltip content="基于AI模型多方辩论计算的综合置信度" placement="top">
                    <el-icon style="margin-left: 4px; cursor: help;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
                <div class="metric-item">
                  <span class="label">风险评分:</span>
                  <span class="value num-tabular">{{ (results.decision.risk_score * 100).toFixed(1) }}%</span>
                  <el-tooltip content="多头/空头及风险控制智能体综合风险评级" placement="top">
                    <el-icon style="margin-left: 4px; cursor: help;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>

            <div class="decision-reasoning">
              <h5>分析依据与逻辑:</h5>
              <p>{{ results.decision.reasoning }}</p>
            </div>
          </div>
        </div>

        <!-- 分析概览 -->
        <div class="overview-section">
          <h4>📊 研判概览</h4>
          <div class="overview-card">
            <div v-if="results.summary" class="overview-summary">
              <h5>分析摘要:</h5>
              <p>{{ results.summary }}</p>
            </div>

            <div v-if="results.recommendation" class="overview-recommendation">
              <h5>综合建议:</h5>
              <p>{{ results.recommendation }}</p>
            </div>
          </div>
        </div>

        <!-- 五维量化因子特征评估卡片 -->
        <div v-if="quantFactors && quantFactors.length > 0" class="quant-factors-section">
          <div class="quant-section-header">
            <div class="header-left">
              <h4>📐 五维量化因子特征评估 (Quant Factors Assessment)</h4>
              <el-tag size="small" type="info" effect="plain" style="margin-left: 8px;">多智能体决策数据底座</el-tag>
            </div>
            <span class="quant-badge">量化因子与多智能体融合</span>
          </div>
          <div class="quant-factors-grid">
            <div class="quant-factor-card" v-for="factor in quantFactors" :key="factor.key">
              <div class="factor-header">
                <span class="factor-icon">{{ factor.icon }}</span>
                <span class="factor-name">{{ factor.name }}</span>
                <el-tag :type="factor.statusType" size="small" effect="plain">{{ factor.status }}</el-tag>
              </div>
              <div class="factor-score-row">
                <span class="factor-score num-tabular">{{ factor.score }}</span>
                <span class="factor-score-max">/100</span>
                <el-progress 
                  :percentage="factor.score" 
                  :color="factor.progressColor" 
                  :show-text="false" 
                  :stroke-width="6" 
                  class="factor-progress"
                />
              </div>
              <div class="factor-desc">{{ factor.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 详细分析报告 -->
        <div v-if="results.state || results.reports" class="reports-section">
          <h4>📋 详细分项投研报告</h4>

          <div class="analysis-tabs-container">
            <el-tabs
              v-model="activeTab"
              type="card"
              class="analysis-tabs"
              tab-position="top"
            >
              <el-tab-pane
                v-for="(report, index) in reportList"
                :key="index"
                :name="String(index)"
                :label="report.title"
                class="report-tab-pane"
              >
                <div class="report-header">
                  <div class="report-title">
                    <span class="report-icon">{{ getReportIcon(report.title) }}</span>
                    <span class="report-name">{{ getReportName(report.title) }}</span>
                  </div>
                  <div class="report-description">{{ getReportDescription(report.title) }}</div>
                </div>

                <div class="report-content-wrapper">
                  <div
                    class="report-content markdown-body"
                    v-html="renderMarkdown(report.content)"
                    v-if="report.content"
                  ></div>
                  <div v-else class="no-content">
                    <el-empty description="暂无内容" />
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>

        <!-- 操作按钮与报告下载 -->
        <div class="result-actions">
          <el-dropdown trigger="click" @command="(cmd: string) => $emit('download', cmd)">
            <el-button type="primary">
              <el-icon><Download /></el-icon>
              下载报告
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="markdown">
                  <el-icon><Document /></el-icon> Markdown 格式
                </el-dropdown-item>
                <el-dropdown-item command="docx">
                  <el-icon><Document /></el-icon> Word 文档 (.docx)
                </el-dropdown-item>
                <el-dropdown-item command="pdf">
                  <el-icon><Document /></el-icon> PDF 文档
                </el-dropdown-item>
                <el-dropdown-item command="json" divided>
                  <el-icon><Document /></el-icon> JSON 原始研报数据
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Document,
  Download,
  WarningFilled,
  Cpu,
  QuestionFilled,
  ArrowDown
} from '@element-plus/icons-vue'
import { marked } from 'marked'

const props = defineProps<{
  results: any
  form?: any
  quantFactors?: any[]
}>()

defineEmits<{
  (e: 'download', format: string): void
}>()

const activeTab = ref('0')

const getActionTagType = (action: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' => {
  const actionTypes: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    '买入': 'success',
    '持有': 'warning',
    '卖出': 'danger',
    '观望': 'info'
  }
  return actionTypes[action] || 'info'
}

const reportList = computed(() => {
  const data = props.results
  if (!data) return []
  const reports: Array<{ title: string; content: any }> = []
  const reportsData = data.reports || data.state || {}

  const reportMappings = [
    { key: 'market_report', title: '📈 市场技术分析' },
    { key: 'sentiment_report', title: '💭 市场情绪分析' },
    { key: 'news_report', title: '📰 新闻事件分析' },
    { key: 'fundamentals_report', title: '💰 基本面分析' },
    { key: 'bull_researcher', title: '🐂 多头研究员' },
    { key: 'bear_researcher', title: '🐻 空头研究员' },
    { key: 'research_team_decision', title: '🔬 研究经理决策' },
    { key: 'trader_investment_plan', title: '💼 交易员计划' },
    { key: 'risky_analyst', title: '⚡ 激进分析师' },
    { key: 'safe_analyst', title: '🛡️ 保守分析师' },
    { key: 'neutral_analyst', title: '⚖️ 中性分析师' },
    { key: 'risk_management_decision', title: '👔 投资组合经理' },
    { key: 'final_trade_decision', title: '🎯 最终交易决策' },
    { key: 'investment_plan', title: '📋 投资建议' }
  ]

  reportMappings.forEach(mapping => {
    const content = reportsData[mapping.key]
    if (content) {
      reports.push({
        title: mapping.title,
        content
      })
    }
  })

  return reports
})

const getReportName = (title: string) => title.replace(/^[^\s]+\s/, '')

const getReportDescription = (title: string) => {
  const descMap: Record<string, string> = {
    '📈 市场技术分析': '技术指标、价格趋势、支撑阻力位分析',
    '💰 基本面分析': '财务数据、估值水平、盈利能力分析',
    '📰 新闻事件分析': '相关新闻事件、市场动态影响分析',
    '💭 市场情绪分析': '投资者情绪、社交媒体情绪指标',
    '📋 投资建议': '具体投资策略、仓位管理建议',
    '🔬 研究团队决策': '多头/空头研究员辩论分析，研究经理综合决策',
    '💼 交易团队计划': '专业交易员制定的具体交易执行计划',
    '⚖️ 风险管理团队': '激进/保守/中性分析师风险评估，投资组合经理最终决策',
    '🎯 最终交易决策': '综合所有团队分析后的最终投资决策'
  }
  return descMap[title] || '详细分析报告'
}

const getReportIcon = (title: string) => {
  const iconMap: Record<string, string> = {
    '📈 市场技术分析': '📈',
    '💰 基本面分析': '💰',
    '📰 新闻事件分析': '📰',
    '💭 市场情绪分析': '💭',
    '📋 投资建议': '📋',
    '🔬 研究团队决策': '🔬',
    '💼 交易团队计划': '💼',
    '⚖️ 风险管理团队': '⚖️',
    '🎯 最终交易决策': '🎯'
  }
  return iconMap[title] || '📊'
}

const renderMarkdown = (content: any): string => {
  if (!content) return ''
  let stringContent = ''
  if (typeof content === 'string') {
    stringContent = content
  } else if (typeof content === 'object') {
    stringContent = content.judge_decision || JSON.stringify(content, null, 2)
  } else {
    stringContent = String(content)
  }

  try {
    return marked.parse(stringContent) as string
  } catch {
    return `<pre style="white-space: pre-wrap;">${stringContent}</pre>`
  }
}
</script>

<style scoped lang="scss">
.results-section {
  margin-top: 32px;

  .results-card {
    border-radius: 16px;
    border: none;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

    :deep(.el-card__header) {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: white;
      padding: 20px 24px;
      border-radius: 16px 16px 0 0;

      .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 700;
        }

        .result-meta {
          display: flex;
          gap: 8px;
        }
      }
    }

    .results-content {
      padding: 12px 0;

      .decision-section {
        margin: 24px 0;

        .decision-card {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;

          .decision-main {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 16px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 16px;

            .decision-action {
              display: flex;
              align-items: center;
              gap: 8px;

              .label {
                font-weight: 600;
                color: #334155;
              }
            }

            .decision-metrics {
              display: flex;
              gap: 24px;

              .metric-item {
                display: flex;
                align-items: center;
                gap: 6px;

                .label {
                  font-size: 13px;
                  color: #64748b;
                }

                .value {
                  font-size: 16px;
                  font-weight: 700;
                  color: #0f172a;
                }
              }
            }
          }

          .decision-reasoning {
            h5 {
              margin: 0 0 8px 0;
              font-size: 14px;
              color: #334155;
            }

            p {
              margin: 0;
              color: #475569;
              line-height: 1.6;
              font-size: 14px;
            }
          }
        }
      }

      .quant-factors-section {
        margin: 28px 0;

        .quant-section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;

          .header-left {
            display: flex;
            align-items: center;

            h4 {
              margin: 0;
              font-size: 15px;
              font-weight: 700;
              color: #1e293b;
            }
          }

          .quant-badge {
            font-size: 11px;
            background: #eff6ff;
            color: #2563eb;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
          }
        }

        .quant-factors-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 14px;

          .quant-factor-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);

            .factor-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;

              .factor-icon { margin-right: 6px; font-size: 15px; }
              .factor-name { font-size: 13px; font-weight: 600; color: #1e293b; flex: 1; }
            }

            .factor-score-row {
              display: flex;
              align-items: baseline;
              gap: 4px;
              margin-bottom: 8px;

              .factor-score { font-size: 22px; font-weight: 700; color: #0f172a; }
              .factor-score-max { font-size: 11px; color: #94a3b8; }
              .factor-progress { flex: 1; margin-left: 10px; }
            }

            .factor-desc {
              font-size: 12px;
              color: #64748b;
              line-height: 1.4;
            }
          }
        }
      }

      .reports-section {
        margin: 28px 0;

        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          color: #1e293b;
        }

        .report-header {
          padding: 14px 18px;
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
          border-radius: 8px 8px 0 0;

          .report-title {
            display: flex;
            align-items: center;
            gap: 8px;

            .report-name {
              font-size: 15px;
              font-weight: 600;
              color: #1e293b;
            }
          }

          .report-description {
            font-size: 12px;
            color: #64748b;
            margin-top: 4px;
          }
        }

        .report-content-wrapper {
          padding: 20px;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-top: none;
          border-radius: 0 0 8px 8px;
          min-height: 200px;
        }
      }

      .result-actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 24px;
      }
    }
  }
}
</style>
