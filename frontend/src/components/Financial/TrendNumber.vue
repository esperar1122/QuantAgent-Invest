<template>
  <span
    :class="[
      badge ? badgeClass : textClass,
      'num-tabular',
      { 'bold': bold },
      sizeClass
    ]"
  >
    <template v-if="isValid">
      {{ displayPrefix }}{{ formattedValue }}{{ displaySuffix }}
    </template>
    <template v-else>
      <span class="text-flat">--</span>
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value?: number | string | null
    precision?: number
    percent?: boolean
    prefix?: string
    suffix?: string
    showSign?: boolean
    badge?: boolean
    bold?: boolean
    size?: 'xs' | 'small' | 'default' | 'large' | 'xl'
  }>(),
  {
    value: null,
    precision: 2,
    percent: false,
    prefix: '',
    suffix: '',
    showSign: undefined,
    badge: false,
    bold: false,
    size: 'default'
  }
)

const numValue = computed<number | null>(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return null
  }
  const n = Number(props.value)
  return isNaN(n) ? null : n
})

const isValid = computed(() => numValue.value !== null)

const sign = computed<string>(() => {
  if (!isValid.value || numValue.value === null) return ''
  const shouldSign = props.showSign ?? props.percent
  if (shouldSign && numValue.value > 0) return '+'
  return ''
})

const textClass = computed(() => {
  if (!isValid.value || numValue.value === null) return 'trend-flat'
  if (numValue.value > 0) return 'trend-up'
  if (numValue.value < 0) return 'trend-down'
  return 'trend-flat'
})

const badgeClass = computed(() => {
  if (!isValid.value || numValue.value === null) return 'trend-badge-flat'
  if (numValue.value > 0) return 'trend-badge-up'
  if (numValue.value < 0) return 'trend-badge-down'
  return 'trend-badge-flat'
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'xs': return 'size-xs'
    case 'small': return 'size-sm'
    case 'large': return 'size-lg'
    case 'xl': return 'size-xl'
    default: return ''
  }
})

const displayPrefix = computed(() => {
  return props.prefix || ''
})

const displaySuffix = computed(() => {
  if (props.percent) return '%'
  return props.suffix || ''
})

const formattedValue = computed(() => {
  if (!isValid.value || numValue.value === null) return '--'
  const v = numValue.value.toFixed(props.precision)
  return `${sign.value}${v}`
})
</script>

<style scoped lang="scss">
.size-xs { font-size: 11px; }
.size-sm { font-size: 12px; }
.size-lg { font-size: 18px; }
.size-xl { font-size: 22px; }
.bold { font-weight: 700; }
</style>
