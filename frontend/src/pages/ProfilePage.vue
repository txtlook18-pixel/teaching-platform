<template>
  <AppLayout>
    <div class="max-w-2xl">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">{{ t('profile.title') }}</h1>

      <!-- User card -->
      <div class="card mb-6">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-2xl font-bold text-blue-600">
            {{ initials }}
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900">{{ authStore.user?.username }}</h2>
            <p class="text-gray-500">{{ authStore.user?.email }}</p>
            <p v-if="authStore.user?.telegram_username" class="text-sm text-blue-500 mt-0.5">
              @{{ authStore.user.telegram_username }}
            </p>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-400">
          {{ t('profile.createdAt') }}
          {{ authStore.user?.created_at
            ? new Date(authStore.user.created_at).toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
            : '—' }}
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <template v-if="statsLoading">
          <div v-for="i in 4" :key="i" class="card animate-pulse">
            <div class="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div class="h-4 bg-gray-100 rounded w-3/4"></div>
          </div>
        </template>

        <template v-else>
          <div class="card text-center">
            <p class="text-4xl font-bold text-blue-600">{{ stats.total_lessons }}</p>
            <p class="text-gray-500 mt-1">{{ t('profile.stats.lessons') }}</p>
          </div>
          <div class="card text-center">
            <p class="text-4xl font-bold text-purple-600">{{ stats.total_assignments }}</p>
            <p class="text-gray-500 mt-1">{{ t('profile.stats.assignments') }}</p>
          </div>
          <div class="card text-center">
            <p class="text-4xl font-bold text-green-600">{{ stats.total_student_sessions }}</p>
            <p class="text-gray-500 mt-1">{{ t('profile.stats.students') }}</p>
          </div>
          <div class="card text-center">
            <p class="text-4xl font-bold text-amber-500">{{ stats.total_responses }}</p>
            <p class="text-gray-500 mt-1">{{ t('profile.stats.answers') }}</p>
          </div>
        </template>
      </div>

      <!-- Logout -->
      <div class="card">
        <h3 class="font-semibold text-gray-700 mb-3">{{ t('profile.session') }}</h3>
        <button class="btn-danger" @click="handleLogout">
          {{ t('profile.logout') }}
        </button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/services/api'
import type { TeacherStats } from '@/types'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const router = useRouter()

const statsLoading = ref(true)
const stats = ref<TeacherStats>({
  total_lessons: 0,
  total_assignments: 0,
  total_student_sessions: 0,
  total_responses: 0,
})

const initials = computed(() => {
  const name = authStore.user?.username ?? ''
  return name.slice(0, 2).toUpperCase() || '?'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  try {
    const res = await apiClient.get<TeacherStats>('/auth/stats')
    stats.value = res.data
  } finally {
    statsLoading.value = false
  }
})
</script>
