<template>
  <div class="pipeline-card">
    <div class="pipeline-header">
      <div class="pipeline-title-group">
        <span class="tag-badge">SYSTEM PIPELINE</span>
        <h3 class="pipeline-title">系统核心投研全链路：量化因子初筛 ➔ 多智能体深度研判 ➔ 证据仲裁与决策</h3>
      </div>
      <div class="pipeline-note">全流程自动化协同 · 结构化数据支撑 · 杜绝黑盒幻觉</div>
    </div>

    <div class="steps-flow">
      <!-- 01 市场扫描 -->
      <div class="step-box active">
        <div class="step-num">01</div>
        <div class="step-content">
          <div class="step-name">市场扫描</div>
          <div class="step-desc">指数 / 市场宽度 / 成交额 / 行业</div>
          <div class="step-badge">全市场 5,500+</div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 02 Quant Engine -->
      <div class="step-box highlight">
        <div class="step-num">02</div>
        <div class="step-content">
          <div class="step-name">Quant Engine</div>
          <div class="step-desc">趋势 / 量价 / 波动 / 估值</div>
          <div class="step-badge highlight-badge">4,000+ ➔ 126 标的</div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 03 Multi-Agent -->
      <div class="step-box active">
        <div class="step-num">03</div>
        <div class="step-content">
          <div class="step-name">Multi-Agent</div>
          <div class="step-desc">宏观 / 技术 / 基本面 / 风险</div>
          <div class="step-badge">4 类专业智能体</div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 04 Evidence -->
      <div class="step-box active">
        <div class="step-num">04</div>
        <div class="step-content">
          <div class="step-name">Evidence</div>
          <div class="step-desc">支持证据 / 风险证据 / 冲突项</div>
          <div class="step-badge">证据仲裁聚合</div>
        </div>
      </div>

      <div class="step-arrow">➔</div>

      <!-- 05 Decision -->
      <div class="step-box final">
        <div class="step-num">05</div>
        <div class="step-content">
          <div class="step-name">Decision</div>
          <div class="step-desc">综合研究结果 / 研究报告</div>
          <div class="step-badge final-badge">结构化白皮书</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.pipeline-card {
  background: #ffffff;
  border: 1px solid #e4e7ec;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 16px;
  user-select: none;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .pipeline-title-group {
    display: flex;
    align-items: center;
    gap: 10px;

    .tag-badge {
      font-size: 11px;
      font-weight: 700;
      color: #175cd3;
      background-color: #eff8ff;
      border: 1px solid #b2ddff;
      padding: 1px 6px;
      border-radius: 4px;
      letter-spacing: 0.04em;
    }

    .pipeline-title {
      font-size: 14px;
      font-weight: 700;
      color: #101828;
      margin: 0;
    }
  }

  .pipeline-note {
    font-size: 12px;
    color: #667085;
  }
}

.steps-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 8px;

  .step-box {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: #f8fafc;
    border: 1px solid #e4e7ec;
    border-radius: 6px;
    padding: 10px 12px;
    transition: all 0.2s ease;

    .step-num {
      font-size: 14px;
      font-weight: 800;
      color: #98a2b3;
      font-family: 'JetBrains Mono', monospace;
      line-height: 1.2;
    }

    .step-content {
      flex: 1;

      .step-name {
        font-size: 13px;
        font-weight: 700;
        color: #101828;
        line-height: 1.2;
      }

      .step-desc {
        font-size: 11px;
        color: #667085;
        margin: 3px 0 6px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .step-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        color: #344054;
        background: #eaecf0;
        padding: 1px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
      }
    }

    &.highlight {
      background: #eff8ff;
      border-color: #84caff;

      .step-num {
        color: #175cd3;
      }

      .step-name {
        color: #175cd3;
      }

      .highlight-badge {
        background: #175cd3;
        color: #ffffff;
      }
    }

    &.final {
      background: #faf5ff;
      border-color: #d8b4fe;

      .step-num {
        color: #7e22ce;
      }

      .step-name {
        color: #7e22ce;
      }

      .final-badge {
        background: #7e22ce;
        color: #ffffff;
      }
    }
  }

  .step-arrow {
    font-size: 14px;
    color: #98a2b3;
    font-weight: 700;
  }
}
</style>
