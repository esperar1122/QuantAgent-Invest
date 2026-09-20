<template>
  <div class="terminal-screening-wrapper">
    <StockPoolView />
  </div>
</template>

<script setup lang="ts">
import StockPoolView from '@/views/StockPool/index.vue'
</script>

<style scoped lang="scss">
.terminal-screening-wrapper {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
