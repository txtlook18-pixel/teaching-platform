<template>
  <div class="min-h-screen bg-gray-50 p-4">
    <div v-if="!sessionData" class="flex justify-center py-20">
      <p class="text-gray-500">Загрузка...</p>
    </div>

    <div v-else class="max-w-xl mx-auto">
      <div class="text-center mb-6">
        <span class="text-3xl">{{ typeIcon }}</span>
        <h1 class="text-xl font-bold mt-2">{{ typeLabel }}</h1>
        <p class="text-gray-500 text-sm">Привет, {{ sessionData.assignment_type ? studentName : '' }}!</p>
      </div>

      <!-- TEST MODE -->
      <div v-if="sessionData.assignment_type === 'test' && currentQuestion">
        <div class="card mb-4">
          <div class="flex justify-between text-xs text-gray-400 mb-3">
            <span>Вопрос {{ questionIndex + 1 }}</span>
            <span class="capitalize px-2 py-0.5 rounded"
              :class="{
                'bg-green-100 text-green-700': currentQuestion.level === 'easy',
                'bg-yellow-100 text-yellow-700': currentQuestion.level === 'medium',
                'bg-red-100 text-red-700': currentQuestion.level === 'hard',
              }">{{ currentQuestion.level }}</span>
          </div>
          <p class="text-lg font-medium">{{ currentQuestion.question }}</p>
        </div>

        <div class="space-y-3">
          <button
            v-for="(answer, i) in currentQuestion.answers"
            :key="i"
            class="w-full text-left p-4 border-2 rounded-xl transition-all"
            :class="selectedAnswer === i
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'"
            @click="selectedAnswer = i"
          >
            <span class="font-medium text-gray-600 mr-2">{{ ['A','B','C','D'][i] }}.</span>
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
      <div v-else-if="sessionData.assignment_type === 'cards' && currentCard">
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
          <button class="flex-1 py-3 bg-red-100 text-red-700 rounded-xl font-medium" @click="nextCard(false)">
            ❌ Не знал
          </button>
          <button class="flex-1 py-3 bg-green-100 text-green-700 rounded-xl font-medium" @click="nextCard(true)">
            ✅ Знал
          </button>
        </div>

        <p class="text-center text-sm text-gray-400 mt-3">{{ cardIndex + 1 }} / {{ cards.length }}</p>
      </div>

      <!-- RETELLING / ANALYSIS / BATTLE -->
      <div v-else-if="['retelling','analysis','battle'].includes(sessionData.assignment_type)">
        <div class="card mb-4">
          <div v-if="sessionData.questions_data?.cases?.[0]">
            <h2 class="font-semibold mb-2">{{ sessionData.questions_data.cases[0].title }}</h2>
            <p class="text-gray-700">{{ sessionData.questions_data.cases[0].description }}</p>
            <p v-if="sessionData.questions_data.cases[0].question" class="mt-3 font-medium text-blue-700">
              {{ sessionData.questions_data.cases[0].question }}
            </p>
          </div>
          <div v-else-if="sessionData.questions_data?.reference">
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
          <button class="btn-primary w-full mt-4" :disabled="!textAnswer || submitting" @click="submitTextAnswer">
            {{ submitting ? 'Отправляем...' : 'Отправить ответ' }}
          </button>
        </div>
      </div>

      <!-- FINISHED -->
      <div v-if="finished" class="text-center py-12">
        <span class="text-6xl">🎉</span>
        <h2 class="text-2xl font-bold mt-4">Готово!</h2>
        <p class="text-gray-500 mt-2">Ваши ответы сохранены. Ожидайте результатов от учителя.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/services/api'

const route = useRoute()

const sessionData = ref<any>(null)
const studentName = ref('')
const questionIndex = ref(0)
const selectedAnswer = ref<number | null>(null)
const submitting = ref(false)
const finished = ref(false)
const cardIndex = ref(0)
const cardFlipped = ref(false)
const textAnswer = ref('')

const questions = computed(() => sessionData.value?.questions_data?.questions || [])
const currentQuestion = computed(() => questions.value[questionIndex.value] || null)
const cards = computed(() => sessionData.value?.questions_data?.cards || [])
const currentCard = computed(() => cards.value[cardIndex.value] || null)

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    test: 'Адаптивный тест', battle: 'Баттл', analysis: 'Анализ', cards: 'Карточки', retelling: 'Пересказ',
  }
  return map[sessionData.value?.assignment_type || ''] || ''
})

const typeIcon = computed(() => {
  const map: Record<string, string> = {
    test: '🧪', battle: '⚔️', analysis: '🔍', cards: '🎴', retelling: '📝',
  }
  return map[sessionData.value?.assignment_type || ''] || ''
})

onMounted(() => {
  const saved = localStorage.getItem('student_session')
  if (saved) {
    sessionData.value = JSON.parse(saved)
    studentName.value = sessionData.value?.student_name || ''
  }
})

async function submitTestAnswer() {
  if (selectedAnswer.value === null || !currentQuestion.value) return
  submitting.value = true
  try {
    await apiClient.post('/assignments/answer', {
      session_id: route.params.sessionId,
      question_index: String(questionIndex.value),
      question_difficulty: currentQuestion.value.level,
      answer_data: {
        answer_index: selectedAnswer.value,
        answer_text: currentQuestion.value.answers[selectedAnswer.value].text,
        is_correct: currentQuestion.value.answers[selectedAnswer.value].correct,
      },
    })

    if (questionIndex.value < questions.value.length - 1) {
      questionIndex.value++
      selectedAnswer.value = null
    } else {
      finished.value = true
    }
  } finally {
    submitting.value = false
  }
}

async function nextCard(knew: boolean) {
  await apiClient.post('/assignments/answer', {
    session_id: route.params.sessionId,
    question_index: String(cardIndex.value),
    answer_data: { knew, term: currentCard.value?.term },
  })
  if (cardIndex.value < cards.value.length - 1) {
    cardIndex.value++
    cardFlipped.value = false
  } else {
    finished.value = true
  }
}

async function submitTextAnswer() {
  submitting.value = true
  try {
    await apiClient.post('/assignments/answer', {
      session_id: route.params.sessionId,
      question_index: '0',
      answer_data: { text: textAnswer.value },
    })
    finished.value = true
  } finally {
    submitting.value = false
  }
}
</script>
