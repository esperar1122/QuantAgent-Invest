<template>
  <div class="stock-code-badge" :class="{ 'is-clickable': clickable }" @click="handleClick">
    <span class="code-text num-tabular">{{ displayCode }}</span>
    <span :class="['exchange-badge', exchangeClass]">
      {{ exchangeLabel }}
    </span>
    <span v-if="name" class="stock-name-label">{{ name }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    code: string
    name?: string
    clickable?: boolean
  }>(),
  {
    name: '',
    clickable: false
  }
)

const emit = defineEmits<{
  (e: 'click'): void
}>()

const cleanCode = computed(() => (props.code || '').trim())

const displayCode = computed(() => cleanCode.value)

const exchangeLabel = computed(() => {
  const c = cleanCode.value.toLowerCase()
  if (c.startsWith('sh000') || c.startsWith('sz399') || c.startsWith('sz980')) return '指数'
  if (c.startsWith('sh') || c.startsWith('6')) return 'SH'
  if (c.startsWith('sz') || c.startsWith('0') || c.startsWith('3') || c.startsWith('9')) return 'SZ'
  return 'BJ'
})

const exchangeClass = computed(() => {
  const c = cleanCode.value.toLowerCase()
  if (c.startsWith('sh000') || c.startsWith('sz399') || c.startsWith('sz980')) return 'index'
  if (c.startsWith('sh') || c.startsWith('6')) return 'sh'
  if (c.startsWith('sz') || c.startsWith('0') || c.startsWith('3') || c.startsWith('9')) return 'sz'
  return 'bj'
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped lang="scss">
@use "@/styles/variables.scss" as *;

.stock-code-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;

  &.is-clickable {
    cursor: pointer;
    &:hover .code-text {
      color: $primary-color;
      text-decoration: underline;
    }
  }

  .code-text {
    font-weight: 600;
    color: #1e293b;
    font-size: 13px;
  }

  .stock-name-label {
    font-size: 13px;
    color: #475569;
  }
}
</style>
