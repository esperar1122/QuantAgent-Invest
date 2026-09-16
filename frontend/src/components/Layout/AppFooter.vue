<template>
  <div class="app-footer">
    <div class="footer-content">
      <div class="copyright">
        <span>智能投研系统 · 融合量化因子分析与大模型多智能体协同推理</span>
      </div>
      <div class="disclaimer-text">
        本系统为学术研究与毕业设计课题演示系统。平台中的量化因子计算与多智能体研判分析均基于历史公开市场数据生成，仅供学术交流与研究使用，不构成任何投资建议。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Footer组件逻辑
</script>

<style lang="scss" scoped>
.app-footer {
  .footer-content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 6px;
    color: var(--el-text-color-regular);
    font-size: 14px;
    padding: 12px 16px;
    text-align: center;
  }

  .rights {
    margin-left: 4px;
  }

  .disclaimer-text {
    color: var(--el-text-color-secondary);
    font-size: 12px;
    line-height: 1.6;
    max-width: 1100px;
  }
}
</style>

