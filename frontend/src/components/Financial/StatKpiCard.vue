<template>
  <div
    class="stat-kpi-card quant-card"
    :class="[type, { 'is-active': active }]"
    @click="$emit('click')"
  >
    <div class="kpi-icon-wrapper" :class="type">
      <slot name="icon">
        <el-icon v-if="icon"><component :is="icon" /></el-icon>
      </slot>
    </div>
    <div class="kpi-body">
      <div class="kpi-value num-tabular">{{ value }}</div>
      <div class="kpi-title">{{ title }}</div>
      <div v-if="subValue" class="kpi-sub">{{ subValue }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  value: number | string
  subValue?: string
  icon?: Component | string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'purple' | 'index'
  active?: boolean
}>()

defineEmits<{
  (e: 'click'): void
}>()
</script>

<style scoped lang="scss">
@use "@/styles/variables.scss" as *;

.stat-kpi-card {
  display: flex;
  align-items: center;
  padding: 16px 18px;
  gap: 14px;
  cursor: pointer;
  border-radius: $border-radius-md;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  transition: all 0.22s ease-in-out;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $box-shadow-medium;
    border-color: #cbd5e1;
  }

  &.is-active {
    border-color: $primary-color;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
  }

  .kpi-icon-wrapper {
    width: 44px;
    height: 44px;
    border-radius: $border-radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;

    &.primary { background-color: #eff6ff; color: #2563eb; }
    &.success { background-color: #f0fdf4; color: #16a34a; }
    &.warning { background-color: #fffbeb; color: #d97706; }
    &.danger { background-color: #fef2f2; color: #ef4444; }
    &.purple { background-color: #faf5ff; color: #9333ea; }
    &.index { background-color: #fdf2f8; color: #db2777; }
  }

  .kpi-body {
    flex: 1;
    min-width: 0;

    .kpi-value {
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.2;
    }

    .kpi-title {
      font-size: 13px;
      color: #64748b;
      margin-top: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .kpi-sub {
      font-size: 11px;
      color: #94a3b8;
      margin-top: 2px;
    }
  }
}
</style>
