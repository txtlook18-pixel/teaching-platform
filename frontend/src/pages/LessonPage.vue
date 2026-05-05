<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="lesson">
      <div class="mb-8">
        <router-link to="/dashboard" class="text-blue-600 hover:underline text-sm">← Все уроки</router-link>
        <div class="flex justify-between items-start mt-2">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ lesson.title }}</h1>
            <p v-if="lesson.cluster_data" class="text-gray-500 mt-1">
              {{ lesson.cluster_data.main_topic }}
            </p>
          </div>
          <span class="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
            {{ lesson.language.toUpperCase() }}
          </span>
        </div>
      </div>

      <!-- Cluster info -->
      <div v-if="lesson.cluster_data" class="card mb-8">
        <h2 class="font-semibold text-gray-700 mb-3">Анализ материала</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-gray-400">Подтемы</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="sub in lesson.cluster_data.subtopics"
                :key="sub"
                class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded"
              >{{ sub }}</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400">Ключевые понятия</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="k in lesson.cluster_data.key_concepts"
                :key="k"
                class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
              >{{ k }}</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400">Сложность</p>
            <p class="font-medium capitalize mt-1">{{ lesson.cluster_data.difficulty_estimate }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-400">Вопросов рекомендовано</p>
            <p class="font-medium mt-1">{{ lesson.cluster_data.suggested_question_count }}</p>
          </div>
        </div>
      </div>

      <!-- Create assignment -->
      <div class="card">
        <h2 class="font-semibold text-gray-800 mb-4 text-lg">Создать задание</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <button
            v-for="atype in assignmentTypes"
            :key="atype.value"
            class="border-2 rounded-xl p-4 text-center transition-all hover:border-blue-400 hover:bg-blue-50"
            :class="selectedType === atype.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'"
            @click="selectedType = atype.value"
          >
            <span class="text-3xl">{{ atype.icon }}</span>
            <p class="text-sm font-medium mt-2">{{ atype.label }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ atype.desc }}</p>
          </button>
        </div>

        <div v-if="selectedType" class="mt-6 flex gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Вопросов</label>
            <input v-model.number="questionCount" type="number" min="3" max="20" class="input-field w-24" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Таймер (сек)</label>
            <select v-model.number="timerSeconds" class="input-field w-28">
              <option :value="30">30 сек</option>
              <option :value="60">60 сек</option>
              <option :value="90">90 сек</option>
              <option :value="120">2 мин</option>
              <option :value="0">Без таймера</option>
            </select>
          </div>
          <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
            {{ creating ? 'Создаём...' : 'Создать и запустить' }}
          </button>
        </div>

        <div v-if="createError" class="mt-4 bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ createError }}</div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'
import type { Lesson } from '@/types'

const route = useRoute()
const router = useRouter()
const lessonStore = useLessonStore()

const loading = ref(true)
const lesson = ref<Lesson | null>(null)
const selectedType = ref('')
const questionCount = ref(10)
const timerSeconds = ref(60)
const creating = ref(false)
const createError = ref('')

const assignmentTypes = [
  { value: 'test', icon: '🧪', label: 'Тест', desc: 'Адаптивный тест' },
  { value: 'battle', icon: '⚔️', label: 'Баттл', desc: 'Дискуссия' },
  { value: 'analysis', icon: '🔍', label: 'Анализ', desc: 'Открытый ответ' },
  { value: 'cards', icon: '🎴', label: 'Карточки', desc: 'Флеш-карты' },
  { value: 'retelling', icon: '📝', label: 'Пересказ', desc: 'Синтез' },
]

onMounted(async () => {
  try {
    lesson.value = await lessonStore.fetchLesson(route.params.id as string)
  } finally {
    loading.value = false
  }
})

async function handleCreateAssignment() {
  if (!selectedType.value || !lesson.value) return
  creating.value = true
  createError.value = ''
  try {
    const res = await apiClient.post(`/assignments/lessons/${lesson.value.id}/assignments`, {
      assignment_type: selectedType.value,
      question_count: questionCount.value,
      timer_seconds: timerSeconds.value,
    })
    const assignmentId = res.data.id
    await apiClient.post(`/assignments/${assignmentId}/generate`)
    await apiClient.post(`/assignments/${assignmentId}/activate`)
    router.push(`/lessons/${lesson.value.id}/assignment/${assignmentId}`)
  } catch (e: any) {
    createError.value = e.response?.data?.detail || 'Ошибка создания задания'
  } finally {
    creating.value = false
  }
}
</script>
