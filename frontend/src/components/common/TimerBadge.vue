<template>
  <span
    class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-mono font-semibold select-none"
    :class="colorClass"
  >
    <span v-if="urgent" class="w-1.5 h-1.5 rounded-full bg-current animate-ping opacity-75"></span>
    {{ formatted }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ seconds: number }>()

const urgent = computed(() => props.seconds > 0 && props.seconds <= 30)

const colorClass = computed(() => {
  if (props.seconds <= 0) return 'bg-gray-100 text-gray-400'
  if (props.seconds <= 30) return 'bg-red-100 text-red-600'
  if (props.seconds <= 60) return 'bg-yellow-100 text-yellow-700'
  return 'bg-green-100 text-green-700'
})

const formatted = computed(() => {
  const s = Math.max(0, props.seconds)
  const m = Math.floor(s / 60)
  const ss = s % 60
  return `${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
})
</script>
