<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <router-link to="/dashboard" class="flex items-center gap-2">
            <span class="text-2xl">🎓</span>
            <span class="text-xl font-bold text-blue-600">AI Teaching</span>
          </router-link>

          <nav class="flex items-center gap-4">
            <router-link
              to="/dashboard"
              class="text-gray-600 hover:text-blue-600 font-medium transition-colors"
              active-class="text-blue-600"
            >
              Уроки
            </router-link>
            <router-link
              to="/archive"
              class="text-gray-600 hover:text-blue-600 font-medium transition-colors"
              active-class="text-blue-600"
            >
              История
            </router-link>
<router-link
              to="/profile"
              class="flex items-center gap-1.5 ml-2 text-sm text-gray-600 hover:text-blue-600 transition-colors"
              active-class="text-blue-600"
            >
              <span class="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-600">
                {{ initials }}
              </span>
              {{ authStore.user?.username }}
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const initials = computed(() =>
  (authStore.user?.username ?? '').slice(0, 2).toUpperCase() || '?',
)
</script>
