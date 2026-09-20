<template>
  <div class="evidence-aggregator-card">
    <!-- 头部统计与仲裁决议 -->
    <div class="aggregator-header">
      <div class="header-main">
        <div class="title-cluster">
          <span class="section-title">证据汇总与多智能体仲裁 (Evidence Aggregator)</span>
          <span class="code-badge">{{ stockCode }} {{ stockName }}</span>
        </div>
        <div class="arbitration-result">
          <span class="arb-label">综合仲裁裁决:</span>
          <span class="arb-conclusion bullish">偏多配置 / 逢低增持</span>
          <span class="arb-score tabular-nums">综合置信分: <strong>82.4</strong> / 100</span>
        </div>
      </div>

      <!-- 4 大指标微型矩阵 -->
      <div class="stats-grid">
        <div class="stat-pill">
          <span class="pill-k">支撑证据</span>
          <span class="pill-v up tabular-nums">8 项 (权重 72%)</span>
        </div>
        <div class="stat-pill">
          <span class="pill-k">风险因子</span>
          <span class="pill-v down tabular-nums">3 项 (权重 28%)</span>
        </div>
        <div class="stat-pill">
          <span class="pill-k">Agent分歧度</span>
          <span class="pill-v warning">中度 (1项争议)</span>
        </div>
        <div class="stat-pill">
          <span class="pill-k">决策建议仓位</span>
          <span class="pill-v tabular-nums">15% - 20%</span>
        </div>
      </div>
    </div>

    <!-- 证据内容分栏 -->
    <div class="evidence-body">
      <!-- 支撑证据池 -->
      <div class="evidence-column support-col">
        <div class="column-header">
          <div class="col-title-left">
            <span class="dot up-dot"></span>
            <span class="col-title">多头支撑证据池 (Supporting Evidence)</span>
          </div>
          <span class="col-count tabular-nums">8 条强事实</span>
        </div>

        <div class="evidence-list">
          <div 
            v-for="(item, idx) in supportList" 
            :key="'supp-' + idx" 
            class="evidence-item"
          >
            <div class="item-top">
              <span class="agent-tag" :class="item.agentClass">{{ item.agent }}</span>
              <span class="confidence-tag tabular-nums">置信度 {{ item.confidence }}%</span>
              <span class="time-tag">{{ item.time }}</span>
            </div>
            <div class="item-title">{{ item.title }}</div>
            <div class="item-desc">{{ item.desc }}</div>
            <div class="item-source">
              <span class="src-label">数据源穿透:</span>
              <span class="src-text">{{ item.source }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 风险预警池 -->
      <div class="evidence-column risk-col">
        <div class="column-header">
          <div class="col-title-left">
            <span class="dot down-dot"></span>
            <span class="col-title">空头与风险证据池 (Risk Points)</span>
          </div>
          <span class="col-count tabular-nums">3 条预警</span>
        </div>

        <div class="evidence-list">
          <div 
            v-for="(item, idx) in riskList" 
            :key="'risk-' + idx" 
            class="evidence-item risk-item"
          >
            <div class="item-top">
              <span class="agent-tag" :class="item.agentClass">{{ item.agent }}</span>
              <span class="confidence-tag tabular-nums">风险级别 {{ item.level }}</span>
              <span class="time-tag">{{ item.time }}</span>
            </div>
            <div class="item-title">{{ item.title }}</div>
            <div class="item-desc">{{ item.desc }}</div>
            <div class="item-source">
              <span class="src-label">防线建议:</span>
              <span class="src-text warning-text">{{ item.hedging }}</span>
            </div>
          </div>

          <!-- 分歧仲裁卡片 -->
          <div class="arbitration-box">
            <div class="arb-header">
              <el-icon><WarningFilled /></el-icon>
              <span class="arb-title">核心分歧与仲裁机制 (Conflict & Arbitration)</span>
            </div>
            <div class="arb-content">
              <p><strong>争议焦点：</strong> 基本面智能体看好 {{ targetName }} ({{ targetCode }}) 行业周期复苏与业绩成长（维持看多），但风险控制智能体提示短期股价偏离 60 日均线，估值 PE 处于历史偏高分位数。</p>
              <p><strong>仲裁决议：</strong> 采纳量化动量与基本面中长期向好逻辑，但不建议追高激进建仓；策略调优为「回踩短期均线支撑位分批介入，单票仓位控制在 15-20%，严格执行动态防线纪律」。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  stockCode?: string
  stockName?: string
}>()

const targetName = computed(() => props.stockName || '标的资产')
const targetCode = computed(() => props.stockCode || '688981')

const supportList = computed(() => [
  {
    agent: 'Macro Agent',
    agentClass: 'agent-macro',
    confidence: 91,
    time: '10:14:22',
    title: `国家重大战略专项政策催化 & ${targetName.value} 产业链景气上行`,
    desc: `政策端对战略优势产业支持力度充沛，${targetName.value} 处于核心生态位，享受产业专项扶持与长期流动性加持。`,
    source: '国家部委产业规划指导文件 / 行业协会高频追踪库'
  },
  {
    agent: 'Technical Agent',
    agentClass: 'agent-tech',
    confidence: 88,
    time: '10:14:35',
    title: '放量突破横盘整理平台，MACD 零轴上方金叉扩散',
    desc: '日 K 线有效站上 MA5/MA20/MA60 多头均线，近 3 个交易日成交量较前期均量放大超 120%，量价配合健康。',
    source: 'Level-2 Tick 级成交明细 / 历史形态量化匹配'
  },
  {
    agent: 'Fundamental Agent',
    agentClass: 'agent-fund',
    confidence: 85,
    time: '10:14:48',
    title: `${targetName.value} 产能利用率与核心产品毛利率环比回升`,
    desc: '下游订单需求回补带动核心产线稼动率稳步攀升，产品盈利质量向好，季度经营指引超越市场一致预期。',
    source: '定期财报披露数据 / 行业上下游供应链交叉验证'
  },
  {
    agent: 'Sentiment Agent',
    agentClass: 'agent-sent',
    confidence: 82,
    time: '10:15:02',
    title: '机构大单席位与北向资金呈持续净流入态势',
    desc: '机构大单席位连续数日净买入，龙虎榜及大单资金占比稳步抬升，未见异常主力资金派发迹象。',
    source: '交易所大单交易席位流向统计'
  }
])

const riskList = computed(() => [
  {
    agent: 'Risk Agent',
    agentClass: 'agent-risk',
    level: '中风险',
    time: '10:15:15',
    title: '静态 PE 升至历史偏高分位数，短期存在估值消化压力',
    desc: '当前估值已经反映了一定程度的成长预期，若后续业绩释放节奏不及预期可能引发高估值短期波动。',
    hedging: '建议单笔建仓上限不超总资产 15-20%，杜绝追高。'
  },
  {
    agent: 'Sentiment Agent',
    agentClass: 'agent-sent',
    level: '低风险',
    time: '10:15:24',
    title: '杠杆融资资金连续加仓，市场短期情绪较为亢奋',
    desc: '融资买入额占全天总成交比重处于相对高位，若遭遇大盘系统性回调可能加大短线波动。',
    hedging: '严格设置 20 日生命线止损防线，跌破无条件离场。'
  },
  {
    agent: 'Macro Agent',
    agentClass: 'agent-macro',
    level: '中风险',
    time: '10:15:30',
    title: '外部宏观利率环境与国际贸易政策潜在变动',
    desc: '需持续关注海外宏观经济数据及地缘贸易审查动态，跟踪核心供应链自主化替代进展。',
    hedging: '保持灵活仓位，关注防御性对冲工具。'
  }
])
</script>

<style scoped lang="scss">
.evidence-aggregator-card {
  background-color: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.aggregator-header {
  padding: 14px 16px;
  background-color: #fafbfc;
  border-bottom: 1px solid #eaecf0;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.title-cluster {
  display: flex;
  align-items: center;
  gap: 10px;

  .section-title {
    font-size: 13px;
    font-weight: 700;
    color: #101828;
  }

  .code-badge {
    background-color: #f2f4f7;
    color: #344054;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
  }
}

.arbitration-result {
  display: flex;
  align-items: center;
  gap: 8px;

  .arb-label {
    font-size: 12px;
    color: #667085;
  }

  .arb-conclusion {
    font-size: 12px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;

    &.bullish {
      background-color: #fef3f2;
      color: #d92d20;
      border: 1px solid #fee4e2;
    }
  }

  .arb-score {
    font-size: 12px;
    color: #475467;
    margin-left: 6px;

    strong {
      color: #175cd3;
      font-size: 14px;
    }
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.stat-pill {
  background-color: #ffffff;
  border: 1px solid #eaecf0;
  border-radius: 4px;
  padding: 6px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .pill-k {
    font-size: 11px;
    color: #667085;
  }

  .pill-v {
    font-size: 12px;
    font-weight: 600;
    color: #101828;

    &.up { color: #d92d20; }
    &.down { color: #039855; }
    &.warning { color: #b54708; }
  }
}

.evidence-body {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  divide-x: 1px solid #eaecf0;
}

.evidence-column {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;

  &.risk-col {
    border-left: 1px solid #eaecf0;
    background-color: #fcfcfd;
  }
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid #f2f4f7;

  .col-title-left {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;

    &.up-dot { background-color: #d92d20; }
    &.down-dot { background-color: #039855; }
  }

  .col-title {
    font-size: 12px;
    font-weight: 700;
    color: #344054;
  }

  .col-count {
    font-size: 11px;
    color: #667085;
    background-color: #f2f4f7;
    padding: 1px 6px;
    border-radius: 3px;
  }
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.evidence-item {
  background-color: #ffffff;
  border: 1px solid #eaecf0;
  border-radius: 5px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: border-color 0.15s ease;

  &:hover {
    border-color: #b2ccff;
  }

  &.risk-item {
    background-color: #ffffff;
    &:hover {
      border-color: #fedf89;
    }
  }

  .item-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .agent-tag {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    text-transform: uppercase;

    &.agent-macro { background-color: #eff8ff; color: #175cd3; }
    &.agent-tech { background-color: #fdf2fa; color: #c11574; }
    &.agent-fund { background-color: #f0f9ff; color: #026aa2; }
    &.agent-sent { background-color: #f4f3ff; color: #5925dc; }
    &.agent-risk { background-color: #fffaeb; color: #b54708; }
  }

  .confidence-tag {
    font-size: 10px;
    color: #475467;
    background-color: #f2f4f7;
    padding: 1px 5px;
    border-radius: 3px;
  }

  .time-tag {
    margin-left: auto;
    font-size: 10px;
    color: #98a2b3;
    font-family: monospace;
  }

  .item-title {
    font-size: 12px;
    font-weight: 600;
    color: #101828;
    line-height: 1.4;
  }

  .item-desc {
    font-size: 11px;
    color: #475467;
    line-height: 1.5;
  }

  .item-source {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10px;
    padding-top: 4px;
    border-top: 1px dashed #f2f4f7;

    .src-label {
      color: #98a2b3;
      font-weight: 600;
    }

    .src-text {
      color: #667085;
    }

    .warning-text {
      color: #b54708;
      font-weight: 600;
    }
  }
}

.arbitration-box {
  margin-top: 4px;
  background-color: #fffaeb;
  border: 1px solid #fedf89;
  border-radius: 5px;
  padding: 10px 12px;

  .arb-header {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #b54708;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 6px;
  }

  .arb-content {
    font-size: 11px;
    color: #713b12;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
    gap: 4px;

    p {
      margin: 0;
    }
  }
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}
</style>
