<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex flex-col">

    <!-- Top bar -->
    <div class="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 shadow-sm">
      <router-link :to="`/lessons/${lessonId}`" class="text-gray-400 hover:text-gray-700 text-sm transition-colors">
        ← Выйти
      </router-link>

      <div class="flex items-center gap-6">
        <span class="text-gray-500 text-sm">
          Вопрос <span class="text-gray-900 font-bold">{{ currentIndex + 1 }}</span> / {{ questions.length }}
        </span>

        <!-- Timer -->
        <div
          v-if="timerSeconds > 0"
          class="flex items-center gap-2 px-4 py-1.5 rounded-lg font-mono text-lg font-bold"
          :class="timeLeft <= 5 ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-800'"
        >
          ⏱ {{ String(Math.floor(timeLeft / 60)).padStart(2,'0') }}:{{ String(timeLeft % 60).padStart(2,'0') }}
        </div>
      </div>

      <!-- Progress dots -->
      <div class="flex gap-1.5">
        <div
          v-for="(_, i) in questions"
          :key="i"
          class="w-2.5 h-2.5 rounded-full transition-colors"
          :class="i < currentIndex ? 'bg-blue-500' : i === currentIndex ? 'bg-gray-800' : 'bg-gray-300'"
        ></div>
      </div>
    </div>

    <!-- Main content -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-14 w-14 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="finished" class="flex-1 flex flex-col items-center justify-center gap-6 px-8">
      <div class="text-8xl">{{ correctCount >= questions.length / 2 ? '🎉' : '📚' }}</div>
      <h2 class="text-4xl font-bold text-gray-900">Тест завершён!</h2>

      <div class="grid grid-cols-2 gap-6 mt-2">
        <div class="bg-green-50 border border-green-200 rounded-2xl px-12 py-8 text-center">
          <p class="text-6xl font-bold text-green-600">{{ correctCount }}</p>
          <p class="text-green-700 mt-2 text-lg">Правильных</p>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-2xl px-12 py-8 text-center">
          <p class="text-6xl font-bold text-red-600">{{ incorrectCount }}</p>
          <p class="text-red-700 mt-2 text-lg">Неправильных</p>
        </div>
      </div>

      <div class="text-2xl font-semibold text-gray-600">
        {{ Math.round((correctCount / questions.length) * 100) }}% правильных ответов
      </div>

      <div class="flex gap-4 mt-2">
        <button
          class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-colors flex items-center gap-2"
          :disabled="retrying"
          @click="retryTest"
        >
          <span v-if="retrying" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          {{ retrying ? 'Генерируем...' : '🔄 Пройти ещё раз' }}
        </button>
        <router-link :to="`/lessons/${lessonId}`" class="px-8 py-3 border-2 border-gray-300 hover:border-gray-400 text-gray-600 rounded-xl font-semibold transition-colors">
          Вернуться к уроку
        </router-link>
      </div>
    </div>

    <div v-else-if="currentQ" class="flex-1 flex flex-col px-8 py-8 max-w-5xl mx-auto w-full">

      <!-- Difficulty badge -->
      <div class="mb-4">
        <span
          class="text-sm font-medium px-3 py-1 rounded-full uppercase tracking-wide"
          :class="{
            'bg-green-100 text-green-700': currentQ.level === 'easy',
            'bg-yellow-100 text-yellow-700': currentQ.level === 'medium',
            'bg-red-100 text-red-700': currentQ.level === 'hard',
          }"
        >{{ { easy: 'Лёгкий', medium: 'Средний', hard: 'Сложный' }[currentQ.level] ?? currentQ.level }}</span>
      </div>

      <!-- Question text -->
      <h1 class="text-3xl font-bold leading-snug mb-10 text-gray-900">{{ currentQ.question }}</h1>

      <!-- Answer options -->
      <div class="grid grid-cols-2 gap-4 flex-1">
        <button
          v-for="(ans, i) in currentQ.answers"
          :key="i"
          class="relative flex items-center gap-4 rounded-2xl p-6 text-left text-xl font-medium border-2 transition-all duration-300"
          :class="answerClass(ans, i)"
          :disabled="revealed"
          @click="selectedAnswer = i"
        >
          <span
            class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg border-2 transition-all"
            :class="labelClass(ans, i)"
          >{{ ['A','B','C','D'][i] }}</span>
          <span>{{ ans.text }}</span>
          <span v-if="revealed" class="absolute right-5 top-1/2 -translate-y-1/2 text-2xl">
            {{ ans.correct ? '✅' : i === selectedAnswer ? '❌' : '' }}
          </span>
        </button>
      </div>

      <!-- Explanation (shown after check) -->
      <div v-if="revealed && currentQ.explanation" class="mt-6 bg-blue-50 border border-blue-200 rounded-xl px-6 py-4 text-blue-800 text-base">
        💡 {{ currentQ.explanation }}
      </div>

      <!-- Bottom controls -->
      <div class="flex items-center justify-end mt-8">
        <button
          v-if="!revealed"
          class="px-10 py-3 rounded-xl font-semibold text-lg transition-colors"
          :class="selectedAnswer !== null
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
          :disabled="selectedAnswer === null"
          @click="check"
        >
          Проверить
        </button>
        <button
          v-else
          class="px-10 py-3 rounded-xl font-semibold text-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          @click="next"
        >
          {{ currentIndex < questions.length - 1 ? 'Вперёд →' : 'Результаты →' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/services/api'

interface Answer { text: string; correct: boolean }
interface Question { question: string; level: string; answers: Answer[]; explanation?: string }

const route = useRoute()
const router = useRouter()
const lessonId = route.params.id as string
const assignmentId = route.params.assignmentId as string

const loading = ref(true)
const questions = ref<Question[]>([])
const timerSeconds = ref(0)
const currentIndex = ref(0)
const timeLeft = ref(0)
const selectedAnswer = ref<number | null>(null)
const revealed = ref(false)
const correctCount = ref(0)
const incorrectCount = ref(0)
const finished = ref(false)
const retrying = ref(false)

let timerId: ReturnType<typeof setInterval> | null = null

const currentQ = computed(() => questions.value[currentIndex.value] ?? null)

function answerClass(ans: Answer, i: number) {
  if (!revealed.value) {
    if (selectedAnswer.value === i) return 'border-blue-500 bg-blue-50 cursor-pointer'
    return 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50 cursor-pointer shadow-sm'
  }
  if (ans.correct) return 'border-green-500 bg-green-50 cursor-default'
  if (i === selectedAnswer.value) return 'border-red-400 bg-red-50 cursor-default'
  return 'border-gray-200 bg-white opacity-50 cursor-default'
}

function labelClass(ans: Answer, i: number) {
  if (!revealed.value) {
    if (selectedAnswer.value === i) return 'border-blue-500 text-blue-600 bg-blue-100'
    return 'border-gray-300 text-gray-500'
  }
  if (ans.correct) return 'border-green-500 text-green-600 bg-green-100'
  if (i === selectedAnswer.value) return 'border-red-400 text-red-500 bg-red-100'
  return 'border-gray-300 text-gray-400'
}

function check() {
  if (selectedAnswer.value === null || !currentQ.value) return
  stopTimer()
  revealed.value = true
  if (currentQ.value.answers[selectedAnswer.value]?.correct) correctCount.value++
  else incorrectCount.value++
}

function next() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    selectedAnswer.value = null
    revealed.value = false
    startTimer()
  } else {
    finished.value = true
  }
}

function startTimer() {
  if (timerSeconds.value === 0) return
  stopTimer()
  timeLeft.value = timerSeconds.value
  timerId = setInterval(() => {
    if (timeLeft.value <= 1) {
      check()
    } else {
      timeLeft.value--
    }
  }, 1000)
}

function stopTimer() {
  if (timerId) { clearInterval(timerId); timerId = null }
}

onUnmounted(stopTimer)

// Reset timer when question changes
watch(currentIndex, startTimer)

async function retryTest() {
  retrying.value = true
  try {
    await apiClient.post(`/assignments/${assignmentId}/generate`)
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    questions.value = res.data.questions_data?.questions ?? []
    currentIndex.value = 0
    selectedAnswer.value = null
    revealed.value = false
    correctCount.value = 0
    incorrectCount.value = 0
    finished.value = false
    startTimer()
  } finally {
    retrying.value = false
  }
}

async function load() {
  try {
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    const data = res.data
    questions.value = data.questions_data?.questions ?? []
    timerSeconds.value = data.timer_seconds ?? 0
    timeLeft.value = timerSeconds.value
    startTimer()
  } finally {
    loading.value = false
  }
}

load()
</script>
