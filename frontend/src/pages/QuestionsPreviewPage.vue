<template>
  <AppLayout>
    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-24 gap-4">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="text-gray-500 text-sm">Генерируем вопросы...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-24">
      <p class="text-4xl mb-4">⚠️</p>
      <p class="text-red-500 mb-6">{{ error }}</p>
      <button class="btn-secondary" @click="$router.back()">← Вернуться к уроку</button>
    </div>

    <!-- Questions -->
    <div v-else>
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Рекомендованные вопросы</h1>
          <p class="text-gray-400 text-sm mt-1">{{ questions.length }} вопросов</p>
        </div>
        <router-link :to="`/lessons/${route.params.id}`" class="btn-secondary">
          ← Вернуться к уроку
        </router-link>
      </div>

      <div class="space-y-5">
        <div v-for="(q, i) in questions" :key="i" class="card">
          <!-- Question -->
          <div class="flex items-start gap-3 mb-4">
            <span class="w-7 h-7 rounded-full bg-blue-600 text-white text-sm flex items-center justify-center font-bold flex-shrink-0">
              {{ i + 1 }}
            </span>
            <div class="flex-1">
              <span
                class="text-xs px-2 py-0.5 rounded-full font-medium mr-2"
                :class="{
                  'bg-green-100 text-green-700': q.level === 'easy',
                  'bg-yellow-100 text-yellow-700': q.level === 'medium',
                  'bg-red-100 text-red-700': q.level === 'hard',
                }"
              >{{ levelLabel(q.level) }}</span>
              <p class="font-medium text-gray-900 mt-1.5">{{ q.question }}</p>
            </div>
          </div>

        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'

interface Answer { text: string; correct: boolean }
interface Question { level: string; question: string; answers: Answer[]; explanation?: string }

const route = useRoute()
const lessonStore = useLessonStore()

const loading = ref(true)
const error = ref('')
const questions = ref<Question[]>([])

function levelLabel(level: string) {
  return ({ easy: 'Лёгкий', medium: 'Средний', hard: 'Сложный' } as Record<string, string>)[level] ?? level
}

onMounted(async () => {
  try {
    const lessonId = route.params.id as string

    // Сначала ищем уже готовые вопросы среди существующих заданий
    const listRes = await apiClient.get(`/assignments/lessons/${lessonId}/assignments`)
    const existing = (listRes.data as any[]).find(
      a => a.assignment_type === 'test' && Array.isArray(a.questions_data?.questions) && a.questions_data.questions.length > 0
    )
    if (existing) {
      questions.value = existing.questions_data.questions
      return
    }

    // Готовых вопросов нет — генерируем
    const lesson = await lessonStore.fetchLesson(lessonId)
    const count = lesson.cluster_data?.suggested_question_count ?? 10

    const createRes = await apiClient.post(`/assignments/lessons/${lessonId}/assignments`, {
      assignment_type: 'test',
      question_count: count,
      timer_seconds: 0,
      settings_data: { mode: 'group' },
    })
    const assignmentId = createRes.data.id

    const genRes = await apiClient.post(`/assignments/${assignmentId}/generate`)
    // Используем ответ generate напрямую если там есть вопросы
    const direct = genRes.data?.questions_data?.questions
    if (Array.isArray(direct) && direct.length > 0) {
      questions.value = direct
      return
    }

    // Иначе перечитываем список
    const listRes2 = await apiClient.get(`/assignments/lessons/${lessonId}/assignments`)
    const assignment = (listRes2.data as any[]).find(a => a.id === assignmentId)
    questions.value = assignment?.questions_data?.questions ?? []

    if (questions.value.length === 0) {
      error.value = 'Не удалось получить вопросы. Попробуйте ещё раз.'
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка генерации вопросов'
  } finally {
    loading.value = false
  }
})
</script>
