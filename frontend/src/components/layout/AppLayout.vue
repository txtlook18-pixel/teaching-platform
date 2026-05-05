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
              to="/lessons/create"
              class="btn-primary text-sm"
            >
              + Создать урок
            </router-link>
            <div class="flex items-center gap-2 ml-4">
              <span class="text-sm text-gray-500">{{ authStore.user?.username }}</span>
              <button @click="handleLogout" class="text-sm text-red-500 hover:text-red-700">
                Выйти
              </button>
            </div>
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
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
