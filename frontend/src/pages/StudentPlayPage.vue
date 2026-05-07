<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div v-if="!sessionData" class="flex justify-center py-20">
      <p class="text-gray-500">Загрузка...</p>
    </div>

    <div v-else class="max-w-xl mx-auto">

      <!-- ── PHONE MODE ─────────────────────────────────────────────── -->
      <template v-if="isPhoneMode">

        <!-- Waiting for next question -->
        <div v-if="phonePhase === 'waiting'" class="flex flex-col items-center justify-center min-h-screen pb-20">
          <div class="text-5xl mb-6">⏳</div>
          <h2 class="text-xl font-bold text-gray-700">Ожидайте следующего вопроса</h2>
          <p class="text-gray-400 mt-2 text-sm">Ответ отправлен</p>
          <div class="mt-6 flex gap-2">
            <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0s"></div>
            <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0.15s"></div>
            <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay:0.3s"></div>
          </div>
        </div>

        <!-- Answering current question -->
        <div v-else-if="phonePhase === 'answering' && currentQuestion && !finished">
          <div class="text-center mb-5 pt-4">
            <p class="text-xs text-gray-400 font-medium">Вопрос {{ questionIndex + 1 }} / {{ questions.length }}</p>
          </div>

          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-5">
            <span
              class="inline-block px-2 py-0.5 rounded text-xs font-medium mb-3 capitalize"
              :class="{
                'bg-green-100 text-green-700': currentQuestion.level === 'easy',
                'bg-yellow-100 text-yellow-700': currentQuestion.level === 'medium',
                'bg-red-100 text-red-700': currentQuestion.level === 'hard',
              }"
            >{{ currentQuestion.level }}</span>
            <p class="text-lg font-semibold text-gray-900 leading-snug">{{ currentQuestion.question }}</p>
          </div>

          <div class="space-y-3">
            <button
              v-for="(answer, i) in currentQuestion.answers"
              :key="i"
              class="w-full text-left p-4 rounded-2xl border-2 transition-all font-medium text-base"
              :class="selectedAnswer === (i as number)
                ? 'border-blue-500 bg-blue-50 text-blue-900'
                : 'border-gray-200 bg-white hover:border-gray-300 text-gray-800'"
              @click="selectedAnswer = (i as number)"
            >
              <span class="font-bold text-gray-400 mr-2">{{ ['A','B','C','D'][i as number] }}.</span>
              {{ answer.text }}
            </button>
          </div>

          <button
            class="w-full mt-6 py-4 rounded-2xl font-bold text-lg transition-colors"
            :class="selectedAnswer !== null && !submitting
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
            :disabled="selectedAnswer === null || submitting"
            @click="submitPhoneAnswer"
          >
            {{ submitting ? 'Отправляем...' : 'Ответить' }}
          </button>
        </div>

        <!-- Phone mode finished: personal results -->
        <div v-if="finished" class="py-8">
          <div class="text-center mb-8">
            <span class="text-6xl">{{ myScore >= 80 ? '🏆' : myScore >= 50 ? '👍' : '💪' }}</span>
            <h2 class="text-2xl font-bold mt-4 text-gray-900">Тест завершён!</h2>
            <p class="text-gray-500 mt-1 text-sm">{{ finishedReason === 'teacher' ? 'Учитель завершил тест' : 'Все вопросы пройдены' }}</p>
          </div>

          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6 text-center">
            <p class="text-sm text-gray-500 mb-1">Ваш результат</p>
            <p class="text-5xl font-black" :class="myScore >= 80 ? 'text-green-500' : myScore >= 50 ? 'text-yellow-500' : 'text-red-500'">
              {{ myScore }}%
            </p>
            <p class="text-gray-500 mt-2">{{ myAnswers.filter(a => a.isCorrect).length }} из {{ myAnswers.length }} правильно</p>
          </div>

          <div class="space-y-2">
            <div
              v-for="(res, i) in myAnswers"
              :key="i"
              class="bg-white rounded-xl border px-4 py-3 flex items-center gap-3"
              :class="res.isCorrect ? 'border-green-200' : 'border-red-200'"
            >
              <span class="text-lg flex-shrink-0">{{ res.isCorrect ? '✅' : '❌' }}</span>
              <span class="text-sm text-gray-700 leading-snug">{{ questions[res.questionIndex]?.question }}</span>
            </div>
          </div>
        </div>

      </template>

      <!-- ── STANDARD (NON-PHONE) MODES ────────────────────────────── -->
      <template v-else>

        <!-- Header -->
        <div class="text-center mb-6">
          <span class="text-3xl">{{ typeIcon }}</span>
          <h1 class="text-xl font-bold mt-2">{{ typeLabel }}</h1>
          <p class="text-gray-500 text-sm">Привет, {{ sessionData.student_name }}!</p>

          <div v-if="!finished && timeLeft > 0" class="mt-3 flex justify-center">
            <TimerBadge :seconds="timeLeft" />
          </div>
        </div>

        <!-- TEST MODE -->
        <div v-if="sessionData.assignment_type === 'test' && currentQuestion && !finished">
          <div class="card mb-4">
            <div class="flex justify-between text-xs text-gray-400 mb-3">
              <span>Вопрос {{ questionIndex + 1 }} / {{ questions.length }}</span>
              <span
                class="capitalize px-2 py-0.5 rounded"
                :class="{
                  'bg-green-100 text-green-700': currentQuestion.level === 'easy',
                  'bg-yellow-100 text-yellow-700': currentQuestion.level === 'medium',
                  'bg-red-100 text-red-700': currentQuestion.level === 'hard',
                }"
              >{{ currentQuestion.level }}</span>
            </div>
            <p class="text-lg font-medium">{{ currentQuestion.question }}</p>
          </div>

          <div class="space-y-3">
            <button
              v-for="(answer, i) in currentQuestion.answers"
              :key="i"
              class="w-full text-left p-4 border-2 rounded-xl transition-all"
              :class="selectedAnswer === (i as number)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'"
              @click="selectedAnswer = (i as number)"
            >
              <span class="font-medium text-gray-600 mr-2">{{ ['A','B','C','D'][i as number] }}.</span>
              {{ answer.text }}
            </button>
          </div>

          <button
            class="btn-primary w-full mt-6 py-3"
            :disabled="selectedAnswer === null || submitting"
            @click="submitTestAnswer"
          >
            {{ submitting ? 'Отправляем...' : 'Ответить' }}
          </button>
        </div>

        <!-- CARDS MODE -->
        <div v-else-if="sessionData.assignment_type === 'cards' && currentCard && !finished">
          <div
            class="card min-h-48 flex flex-col items-center justify-center cursor-pointer select-none"
            @click="cardFlipped = !cardFlipped"
          >
            <p class="text-xs text-gray-400 mb-2">{{ cardFlipped ? 'Определение' : 'Термин' }}</p>
            <p class="text-2xl font-bold text-center">
              {{ cardFlipped ? currentCard.definition : currentCard.term }}
            </p>
            <p class="text-xs text-gray-400 mt-4">Нажмите чтобы {{ cardFlipped ? 'скрыть' : 'показать' }}</p>
          </div>

          <div class="flex gap-3 mt-4">
            <button
              class="flex-1 py-3 bg-red-100 text-red-700 rounded-xl font-medium hover:bg-red-200 transition-colors"
              @click="nextCard(false)"
            >
              ❌ Не знал
            </button>
            <button
              class="flex-1 py-3 bg-green-100 text-green-700 rounded-xl font-medium hover:bg-green-200 transition-colors"
              @click="nextCard(true)"
            >
              ✅ Знал
            </button>
          </div>

          <p class="text-center text-sm text-gray-400 mt-3">{{ cardIndex + 1 }} / {{ cards.length }}</p>
        </div>

        <!-- RETELLING / ANALYSIS / BATTLE -->
        <div v-else-if="['retelling','analysis','battle'].includes(sessionData.assignment_type) && !finished">
          <div class="card mb-4">
            <div v-if="sessionData.questions_data?.cases?.[0]">
              <h2 class="font-semibold mb-2">{{ sessionData.questions_data.cases[0].title }}</h2>
              <p class="text-gray-700">{{ sessionData.questions_data.cases[0].description }}</p>
              <p v-if="sessionData.questions_data.cases[0].question" class="mt-3 font-medium text-blue-700">
                {{ sessionData.questions_data.cases[0].question }}
              </p>
            </div>
            <div v-else>
              <p class="text-gray-500 text-sm mb-2">Перескажи материал своими словами:</p>
              <p class="text-gray-400 text-xs">Эталон скрыт до оценки учителем</p>
            </div>
          </div>

          <div class="card">
            <label class="block text-sm font-medium text-gray-700 mb-2">Ваш ответ:</label>
            <textarea
              v-model="textAnswer"
              class="input-field"
              rows="6"
              placeholder="Напишите здесь..."
            ></textarea>
            <button
              class="btn-primary w-full mt-4"
              :disabled="!textAnswer.trim() || submitting"
              @click="submitTextAnswer"
            >
              {{ submitting ? 'Отправляем...' : 'Отправить ответ' }}
            </button>
          </div>
        </div>

        <!-- FINISHED (standard) -->
        <div v-if="finished" class="text-center py-12">
          <span class="text-6xl">{{ finishedReason === 'teacher' ? '🛑' : '🎉' }}</span>
          <h2 class="text-2xl font-bold mt-4">
            {{ finishedReason === 'teacher' ? 'Задание завершено учителем' : 'Готово!' }}
          </h2>
          <p class="text-gray-500 mt-2">
            {{
              finishedReason === 'timer'
                ? 'Время вышло. Ваши ответы сохранены.'
                : 'Ваши ответы сохранены. Ожидайте результатов от учителя.'
            }}
          </p>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/services/api'
import { useStudentWS } from '@/services/websocket'
import TimerBadge from '@/components/common/TimerBadge.vue'

const route     = useRoute()
const sessionId = route.params.sessionId as string

// ── State ─────────────────────────────────────────────────────────────────────

const sessionData    = ref<any>(null)
const questionIndex  = ref(0)
const selectedAnswer = ref<number | null>(null)
const submitting     = ref(false)
const finished       = ref(false)
const finishedReason = ref<'self' | 'teacher' | 'timer'>('self')
const cardIndex      = ref(0)
const cardFlipped    = ref(false)
const textAnswer     = ref('')

// Phone mode state
const phonePhase = ref<'answering' | 'waiting'>('answering')
const myAnswers  = ref<{ questionIndex: number; isCorrect: boolean }[]>([])

// ── Timer (standard mode only) ────────────────────────────────────────────────

const timeLeft = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

function startTimer(seconds: number) {
  if (seconds <= 0) return
  timeLeft.value = seconds
  timerInterval = setInterval(() => {
    if (timeLeft.value <= 1) {
      clearInterval(timerInterval!)
      timerInterval = null
      timeLeft.value = 0
      handleTimerExpired()
    } else {
      timeLeft.value--
    }
  }, 1000)
}

async function handleTimerExpired() {
  if (finished.value) return
  const type = sessionData.value?.assignment_type
  if (type === 'test' && selectedAnswer.value !== null) {
    await submitTestAnswer()
  } else if (type === 'cards') {
    markFinished('timer')
  } else if (['retelling','analysis','battle'].includes(type) && textAnswer.value.trim()) {
    await submitTextAnswer()
  } else {
    markFinished('timer')
  }
}

// ── WebSocket ─────────────────────────────────────────────────────────────────

const { connect: wsConnect } = useStudentWS(sessionId, {
  onFinished() {
    if (finished.value) return
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
    markFinished('teacher')
  },
  onNextQuestion(e) {
    if (!isPhoneMode.value || finished.value) return
    questionIndex.value  = e.question_index
    selectedAnswer.value = null
    phonePhase.value     = 'answering'
  },
  onTestStarted() {
    // Already on /play — no action needed here
  },
})

// ── Computed ──────────────────────────────────────────────────────────────────

const isPhoneMode = computed(() => sessionData.value?.settings_data?.mode === 'individual')

const questions       = computed(() => sessionData.value?.questions_data?.questions ?? [])
const currentQuestion = computed(() => questions.value[questionIndex.value] ?? null)

const cards       = computed(() => sessionData.value?.questions_data?.cards ?? [])
const currentCard = computed(() => cards.value[cardIndex.value] ?? null)

const myScore = computed(() => {
  if (!myAnswers.value.length) return 0
  return Math.round((myAnswers.value.filter((a) => a.isCorrect).length / myAnswers.value.length) * 100)
})

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    test: 'Адаптивный тест', battle: 'Баттл', analysis: 'Анализ',
    cards: 'Карточки', retelling: 'Пересказ',
  }
  return map[sessionData.value?.assignment_type ?? ''] ?? ''
})

const typeIcon = computed(() => {
  const map: Record<string, string> = {
    test: '🧪', battle: '⚔️', analysis: '🔍', cards: '🎴', retelling: '📝',
  }
  return map[sessionData.value?.assignment_type ?? ''] ?? ''
})

// ── Helpers ───────────────────────────────────────────────────────────────────

function markFinished(reason: 'self' | 'teacher' | 'timer') {
  finishedReason.value = reason
  finished.value       = true
}

// ── Phone mode submit ─────────────────────────────────────────────────────────

async function submitPhoneAnswer() {
  if (selectedAnswer.value === null || !currentQuestion.value) return
  submitting.value = true
  const isCorrect = currentQuestion.value.answers[selectedAnswer.value].correct as boolean
  try {
    await apiClient.post('/assignments/answer', {
      session_id:          sessionId,
      question_index:      String(questionIndex.value),
      question_difficulty: currentQuestion.value.level,
      answer_data: {
        answer_index: selectedAnswer.value,
        answer_text:  currentQuestion.value.answers[selectedAnswer.value].text,
        is_correct:   isCorrect,
      },
    })
    myAnswers.value.push({ questionIndex: questionIndex.value, isCorrect })

    if (questionIndex.value >= questions.value.length - 1) {
      markFinished('self')
    } else {
      phonePhase.value = 'waiting'
    }
  } finally {
    submitting.value = false
  }
}

// ── Standard answer submission ────────────────────────────────────────────────

async function submitTestAnswer() {
  if (selectedAnswer.value === null || !currentQuestion.value) return
  submitting.value = true
  try {
    await apiClient.post('/assignments/answer', {
      session_id:          sessionId,
      question_index:      String(questionIndex.value),
      question_difficulty: currentQuestion.value.level,
      answer_data: {
        answer_index: selectedAnswer.value,
        answer_text:  currentQuestion.value.answers[selectedAnswer.value].text,
        is_correct:   currentQuestion.value.answers[selectedAnswer.value].correct,
      },
    })
    if (questionIndex.value < questions.value.length - 1) {
      questionIndex.value++
      selectedAnswer.value = null
    } else {
      markFinished('self')
    }
  } finally {
    submitting.value = false
  }
}

async function nextCard(knew: boolean) {
  await apiClient.post('/assignments/answer', {
    session_id:     sessionId,
    question_index: String(cardIndex.value),
    answer_data:    { knew, term: currentCard.value?.term },
  })
  if (cardIndex.value < cards.value.length - 1) {
    cardIndex.value++
    cardFlipped.value = false
  } else {
    markFinished('self')
  }
}

async function submitTextAnswer() {
  submitting.value = true
  try {
    await apiClient.post('/assignments/answer', {
      session_id:     sessionId,
      question_index: '0',
      answer_data:    { text: textAnswer.value },
    })
    markFinished('self')
  } finally {
    submitting.value = false
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(() => {
  const saved = localStorage.getItem('student_session')
  if (saved) {
    sessionData.value = JSON.parse(saved)
    if (!isPhoneMode.value) {
      const timerSecs = sessionData.value?.timer_seconds ?? 0
      if (timerSecs > 0) startTimer(timerSecs)
    }
  }
  wsConnect()
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>
