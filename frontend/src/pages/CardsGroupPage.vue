<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="cards.length === 0" class="text-center py-20 text-gray-500">
      Карточки не найдены. Попробуйте пересоздать задание.
    </div>

    <template v-else>
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <router-link :to="`/lessons/${lessonId}`" class="text-blue-600 hover:underline text-sm">← Назад к уроку</router-link>
          <div class="flex items-center gap-3 mt-2">
            <span class="text-2xl">🎴</span>
            <h1 class="text-2xl font-bold text-gray-900">Карточки — Группой</h1>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <!-- Counters -->
          <span class="flex items-center gap-1.5 bg-green-100 text-green-700 px-4 py-2 rounded-xl font-semibold text-lg">
            ✅ {{ knewCount }}
          </span>
          <span class="flex items-center gap-1.5 bg-red-100 text-red-700 px-4 py-2 rounded-xl font-semibold text-lg">
            ❌ {{ didntKnowCount }}
          </span>
        </div>
      </div>

      <!-- Finished screen -->
      <div v-if="finished" class="max-w-lg mx-auto text-center py-16">
        <div class="text-7xl mb-6">🎉</div>
        <h2 class="text-3xl font-bold text-gray-900 mb-2">Готово!</h2>
        <p class="text-gray-500 mb-8">Все {{ cards.length }} карточек пройдены</p>

        <div class="grid grid-cols-2 gap-4 mb-8">
          <div class="bg-green-50 border border-green-200 rounded-2xl p-6">
            <p class="text-4xl font-bold text-green-600">{{ knewCount }}</p>
            <p class="text-sm text-green-700 mt-1">Знали</p>
          </div>
          <div class="bg-red-50 border border-red-200 rounded-2xl p-6">
            <p class="text-4xl font-bold text-red-600">{{ didntKnowCount }}</p>
            <p class="text-sm text-red-700 mt-1">Не знали</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-2xl p-4 mb-8">
          <div class="flex justify-between items-center mb-2">
            <span class="text-sm text-gray-500">Результат группы</span>
            <span class="font-semibold text-gray-800">{{ Math.round((knewCount / cards.length) * 100) }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3">
            <div
              class="bg-green-500 h-3 rounded-full transition-all"
              :style="{ width: `${Math.round((knewCount / cards.length) * 100)}%` }"
            ></div>
          </div>
        </div>

        <div class="flex gap-3 justify-center">
          <button class="btn-primary px-8 py-3 flex items-center gap-2" :disabled="retrying" @click="retry">
            <span v-if="retrying" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            {{ retrying ? 'Генерируем новые...' : '🔄 Попробовать ещё раз' }}
          </button>
          <router-link :to="`/lessons/${lessonId}`" class="px-8 py-3 border-2 border-gray-300 rounded-xl text-gray-700 hover:border-gray-400 transition-colors inline-block">
            Вернуться к уроку
          </router-link>
        </div>
      </div>

      <!-- Active card -->
      <div v-else class="max-w-2xl mx-auto">
        <!-- Progress bar -->
        <div class="flex items-center gap-3 mb-6">
          <span class="text-sm text-gray-500 whitespace-nowrap">{{ currentIndex + 1 }} / {{ cards.length }}</span>
          <div class="flex-1 bg-gray-200 rounded-full h-2">
            <div
              class="bg-blue-500 h-2 rounded-full transition-all"
              :style="{ width: `${((currentIndex) / cards.length) * 100}%` }"
            ></div>
          </div>
        </div>

        <!-- Card -->
        <div
          class="bg-white border-2 border-gray-200 rounded-2xl p-10 text-center cursor-pointer select-none min-h-64 flex flex-col items-center justify-center shadow-sm hover:shadow-md transition-shadow mb-6"
          @click="flipped = !flipped"
        >
          <p class="text-xs font-medium text-gray-400 uppercase tracking-wide mb-4">
            {{ flipped ? 'Определение' : 'Термин' }}
          </p>
          <p class="text-3xl font-bold text-gray-900">
            {{ flipped ? currentCard.definition : currentCard.term }}
          </p>
          <p class="text-xs text-gray-300 mt-6">
            {{ flipped ? 'Нажмите чтобы скрыть' : 'Нажмите чтобы показать определение' }}
          </p>
        </div>

        <!-- Action buttons -->
        <div class="flex gap-4">
          <button
            class="flex-1 py-4 bg-red-100 text-red-700 rounded-2xl font-semibold text-lg hover:bg-red-200 active:scale-95 transition-all"
            @click="answer(false)"
          >
            ❌ Не знали
          </button>
          <button
            class="flex-1 py-4 bg-green-100 text-green-700 rounded-2xl font-semibold text-lg hover:bg-green-200 active:scale-95 transition-all"
            @click="answer(true)"
          >
            ✅ Знали
          </button>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiClient } from '@/services/api'

const route = useRoute()
const lessonId = route.params.id as string
const assignmentId = route.params.assignmentId as string

const loading = ref(true)
const retrying = ref(false)
const cards = ref<{ term: string; definition: string }[]>([])
const usedTerms = ref<Set<string>>(new Set())
const currentIndex = ref(0)
const flipped = ref(false)
const knewCount = ref(0)
const didntKnowCount = ref(0)
const finished = ref(false)

const currentCard = computed(() => cards.value[currentIndex.value])

async function retry() {
  retrying.value = true
  try {
    await apiClient.post(`/assignments/${assignmentId}/generate`, {
      exclude_terms: [...usedTerms.value],
    })
    const updated = await apiClient.get(`/assignments/${assignmentId}`)
    const newCards: { term: string; definition: string }[] = updated.data.questions_data?.cards ?? []
    newCards.forEach(c => usedTerms.value.add(c.term))
    cards.value = newCards
    currentIndex.value = 0
    flipped.value = false
    knewCount.value = 0
    didntKnowCount.value = 0
    finished.value = false
  } finally {
    retrying.value = false
  }
}

function answer(knew: boolean) {
  if (knew) knewCount.value++
  else didntKnowCount.value++

  if (currentIndex.value < cards.value.length - 1) {
    currentIndex.value++
    flipped.value = false
  } else {
    finished.value = true
  }
}

onMounted(async () => {
  try {
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    const loaded: { term: string; definition: string }[] = res.data.questions_data?.cards ?? []
    loaded.forEach(c => usedTerms.value.add(c.term))
    cards.value = loaded
  } finally {
    loading.value = false
  }
})
</script>
