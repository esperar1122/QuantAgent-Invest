<template>
  <div class="terminal-layout">
    <!-- 顶部行情栏 -->
    <TopTickerBar />

    <div class="terminal-body">
      <!-- 左侧固定导航 -->
      <TerminalSidebar />

      <!-- 右侧主工作区 -->
      <main class="terminal-main-workspace">
        <router-view v-slot="{ Component, route }">
          <transition name="terminal-fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import TopTickerBar from '@/components/Terminal/TopTickerBar.vue'
import TerminalSidebar from '@/components/Terminal/TerminalSidebar.vue'
</script>

<style scoped lang="scss">
.terminal-layout {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f4f6f8;
  overflow: hidden;
}

.terminal-body {
  display: flex;
  flex: 1;
  height: calc(100vh - 66px);
  overflow: hidden;
}

.terminal-main-workspace {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 20px;
  background-color: #f4f6f8;
}

.terminal-fade-enter-active,
.terminal-fade-leave-active {
  transition: opacity 0.15s ease;
}

.terminal-fade-enter-from,
.terminal-fade-leave-to {
  opacity: 0;
}
</style>
