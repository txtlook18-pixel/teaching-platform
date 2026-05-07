<template>
  <span
    class="inline-flex items-center gap-1.5 text-sm font-medium"
    :class="connected ? 'text-green-600' : 'text-gray-400'"
  >
    <span
      class="w-2 h-2 rounded-full flex-shrink-0"
      :class="connected ? 'bg-green-400 animate-pulse' : 'bg-gray-300'"
    ></span>
    <slot>{{ connected ? 'Live' : 'Offline' }}</slot>
  </span>
</template>

<script setup lang="ts">
defineProps<{ connected: boolean }>()
</script>
