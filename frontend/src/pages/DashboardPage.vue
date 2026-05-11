<template>
  <AppLayout>
    <div>
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">{{ t('dashboard.title') }}</h1>
          <p class="text-gray-500 mt-1">{{ t('dashboard.subtitle') }}</p>
        </div>
        <router-link to="/lessons/create" class="btn-primary">
          {{ t('dashboard.newLesson') }}
        </router-link>
      </div>

      <div v-if="lessonStore.loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <div v-else-if="lessonStore.lessons.length === 0" class="text-center py-20">
        <span class="text-6xl">📚</span>
        <h2 class="text-xl font-semibold text-gray-700 mt-4">{{ t('dashboard.empty.title') }}</h2>
        <p class="text-gray-500 mt-2">{{ t('dashboard.empty.subtitle') }}</p>
        <router-link to="/lessons/create" class="btn-primary inline-block mt-6">
          {{ t('dashboard.empty.cta') }}
        </router-link>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="lesson in lessonStore.lessons"
          :key="lesson.id"
          class="card hover:shadow-md transition-shadow cursor-pointer"
          @click="router.push(`/lessons/${lesson.id}`)"
        >
          <div class="flex justify-between items-start mb-3">
            <h3 class="text-lg font-semibold text-gray-900 leading-snug">{{ lesson.title }}</h3>
            <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full ml-2 shrink-0">
              {{ lesson.language.toUpperCase() }}
            </span>
          </div>

          <div v-if="lesson.cluster_data" class="mb-3">
            <p class="text-sm text-gray-500">
              {{ t('dashboard.topic') }}
              <span class="font-medium text-gray-700">{{ lesson.cluster_data.main_topic }}</span>
            </p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="concept in lesson.cluster_data.key_concepts?.slice(0, 3)"
                :key="concept"
                class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              >
                {{ concept }}
              </span>
            </div>
          </div>
          <div v-else class="mb-3">
            <span class="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              {{ t('dashboard.notAnalyzed') }}
            </span>
          </div>

          <p class="text-xs text-gray-400">
            {{ new Date(lesson.created_at).toLocaleDateString(locale) }}
          </p>

          <div class="flex gap-2 mt-4" @click.stop>
            <button
              class="flex-1 btn-secondary text-sm py-1.5"
              @click="router.push(`/lessons/${lesson.id}`)"
            >
              {{ t('common.open') }}
            </button>
            <button
              class="text-sm text-red-500 hover:text-red-700 px-2"
              @click="handleDelete(lesson.id)"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'

const { t, locale } = useI18n()
const router = useRouter()
const lessonStore = useLessonStore()

onMounted(() => lessonStore.fetchLessons())

async function handleDelete(id: string) {
  if (!confirm(t('dashboard.deleteConfirm'))) return
  await lessonStore.deleteLesson(id)
}
</script>
