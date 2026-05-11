<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex flex-col">

    <!-- ── LOADING ──────────────────────────────────────────────────── -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    </div>

    <!-- ── EMPTY ─────────────────────────────────────────────────────── -->
    <div v-else-if="cases.length === 0" class="flex-1 flex flex-col items-center justify-center p-8 text-center">
      <div class="text-5xl mb-4">⚠️</div>
      <h2 class="text-xl font-bold text-gray-800 mb-2">Кейсы не найдены</h2>
      <p class="text-gray-500 mb-6">Попробуйте пересоздать задание.</p>
      <router-link :to="`/lessons/${lessonId}`" class="px-6 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium">
        Назад к уроку
      </router-link>
    </div>

    <!-- ── FINISHED ──────────────────────────────────────────────────── -->
    <div v-else-if="phase === 'finished'" class="flex-1 flex flex-col items-center justify-center p-8">
      <div class="text-6xl mb-5">✅</div>
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Разбор завершён!</h2>
      <p class="text-gray-500 mb-8">
        {{ cases.length === 1 ? 'Кейс разобран' : `Разобрано ${cases.length} кейса` }}
      </p>

      <div class="w-full max-w-2xl space-y-3 mb-8">
        <div
          v-for="(c, i) in cases"
          :key="i"
          class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
        >
          <div class="flex items-start gap-3">
            <span class="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-sm font-bold flex items-center justify-center flex-shrink-0">
              {{ i + 1 }}
            </span>
            <div>
              <p class="font-semibold text-gray-900">{{ c.title }}</p>
              <p class="text-sm text-green-700 mt-1">✓ {{ c.correct_answer }}</p>
            </div>
          </div>
        </div>
      </div>

      <router-link
        :to="`/lessons/${lessonId}`"
        class="px-8 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 font-semibold transition-colors"
      >
        Вернуться к уроку
      </router-link>
    </div>

    <!-- ── ACTIVE ─────────────────────────────────────────────────────── -->
    <template v-else>

      <!-- Header -->
      <div class="bg-white border-b border-gray-200 shadow-sm px-8 py-4">
        <div class="flex items-center justify-between max-w-5xl mx-auto">
          <router-link :to="`/lessons/${lessonId}`" class="text-gray-500 hover:text-gray-800 text-sm">
            ← Урок
          </router-link>
          <!-- Timer -->
          <div
            v-if="initialTimer > 0"
            class="flex items-center gap-2 px-4 py-1.5 rounded-xl font-mono font-bold text-lg"
            :class="timeLeft > 10 ? 'bg-gray-100 text-gray-800' : 'bg-red-100 text-red-600'"
          >
            ⏱ {{ formatTime(timeLeft) }}
          </div>
        </div>
      </div>

      <!-- Case content -->
      <div class="flex-1 flex flex-col items-center px-8 py-8 max-w-4xl mx-auto w-full">

        <!-- Case card -->
        <div class="w-full bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-6">
          <div class="flex items-center gap-3 mb-5">
            <span class="text-2xl">🔍</span>
            <h2 class="text-2xl font-bold text-gray-900">{{ currentCase.title }}</h2>
          </div>

          <p class="text-gray-700 leading-relaxed text-base mb-6 whitespace-pre-line">{{ currentCase.description }}</p>

          <!-- Question box -->
          <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <p class="text-xs font-semibold text-blue-500 uppercase tracking-wide mb-1">Задание</p>
            <p class="text-blue-900 font-medium">{{ currentCase.question }}</p>
          </div>
        </div>

        <!-- Revealed answer -->
        <div
          v-if="revealed"
          class="w-full bg-green-50 border border-green-200 rounded-2xl p-6 mb-6"
        >
          <p class="text-xs font-semibold text-green-600 uppercase tracking-wide mb-2">✅ Правильный ответ</p>
          <p class="text-gray-800 leading-relaxed text-base whitespace-pre-line">{{ currentCase.correct_answer }}</p>
        </div>

        <!-- Action buttons -->
        <div class="flex gap-4">
          <button
            v-if="!revealed"
            class="px-10 py-3 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 active:scale-95 transition-all"
            @click="revealAnswer"
          >
            Раскрыть ответ
          </button>
          <template v-else>
            <button
              v-if="currentIndex < cases.length - 1"
              class="px-10 py-3 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 active:scale-95 transition-all"
              @click="nextCase"
            >
              Следующий кейс →
            </button>
            <button
              v-else
              class="px-10 py-3 bg-green-600 text-white rounded-xl font-semibold text-lg hover:bg-green-700 active:scale-95 transition-all"
              @click="router.push(`/lessons/${lessonId}`)"
            >
              Завершить разбор ✓
            </button>
          </template>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/services/api'

interface AnalysisCase {
  title: string
  description: string
  question: string
  correct_answer: string
}

const route = useRoute()
const router = useRouter()
const lessonId = route.params.id as string
const assignmentId = route.params.assignmentId as string

const loading = ref(true)
const cases = ref<AnalysisCase[]>([])
const currentIndex = ref(0)
const revealed = ref(false)
const phase = ref<'active' | 'finished'>('active')
const initialTimer = ref(0)
const timeLeft = ref(0)

let timerInterval: ReturnType<typeof setInterval> | null = null

const currentCase = computed(() => cases.value[currentIndex.value])

function formatTime(s: number) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
}

function startTimer() {
  if (initialTimer.value === 0) return
  timeLeft.value = initialTimer.value
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      clearInterval(timerInterval!)
      timerInterval = null
      revealAnswer()
    }
  }, 1000)
}

function revealAnswer() {
  revealed.value = true
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function nextCase() {
  currentIndex.value++
  revealed.value = false
  startTimer()
}

onMounted(async () => {
  try {
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    const data = res.data
    cases.value = data.questions_data?.cases ?? []
    initialTimer.value = data.timer_seconds ?? 0
    timeLeft.value = initialTimer.value
    startTimer()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>
