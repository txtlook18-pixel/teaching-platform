<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex flex-col">

    <!-- Top bar -->
    <div class="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 shadow-sm">
      <router-link :to="`/lessons/${lessonId}`" class="text-gray-400 hover:text-gray-700 text-sm transition-colors">
        ← Выйти
      </router-link>

      <div class="flex items-center gap-2">
        <span class="text-xl">⚔️</span>
        <span class="font-semibold text-gray-800">Баттл: Дискуссия</span>
      </div>

      <!-- Timer -->
      <div
        class="flex items-center gap-2 px-5 py-2 rounded-xl font-mono text-2xl font-bold transition-colors"
        :class="timeLeft <= 30 && timeLeft > 0
          ? 'bg-red-500 text-white'
          : timeLeft === 0
            ? 'bg-gray-200 text-gray-500'
            : 'bg-blue-50 text-blue-700 border border-blue-200'"
      >
        ⏱ {{ String(Math.floor(timeLeft / 60)).padStart(2, '0') }}:{{ String(timeLeft % 60).padStart(2, '0') }}
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-14 w-14 border-b-2 border-blue-600"></div>
    </div>

    <!-- Main content -->
    <div v-else class="flex-1 flex flex-col px-8 py-8 max-w-7xl mx-auto w-full">

      <!-- Two sides -->
      <div class="grid grid-cols-2 gap-6 flex-1">

        <!-- Side A -->
        <div class="flex flex-col bg-white rounded-2xl border-2 border-blue-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 bg-blue-600 flex items-center gap-3">
            <span class="w-10 h-10 rounded-full bg-white text-blue-600 font-bold text-xl flex items-center justify-center flex-shrink-0">А</span>
            <h2 class="text-white font-bold text-lg leading-tight">{{ caseA?.title }}</h2>
          </div>
          <div class="flex-1 px-6 py-5 flex flex-col gap-5">
            <p class="text-gray-700 text-base leading-relaxed">{{ caseA?.description }}</p>

            <div>
              <p class="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-2">Аргументы</p>
              <ul class="space-y-2">
                <li
                  v-for="(arg, i) in caseA?.key_arguments"
                  :key="i"
                  class="flex items-start gap-2 text-sm text-gray-800"
                >
                  <span class="mt-0.5 w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center flex-shrink-0">{{ i + 1 }}</span>
                  {{ arg }}
                </li>
              </ul>
            </div>

            <div v-if="caseA?.nuance" class="mt-auto bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              <p class="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-1">Нюанс</p>
              <p class="text-sm text-amber-800">{{ caseA.nuance }}</p>
            </div>
          </div>
        </div>

        <!-- Side B -->
        <div class="flex flex-col bg-white rounded-2xl border-2 border-rose-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 bg-rose-600 flex items-center gap-3">
            <span class="w-10 h-10 rounded-full bg-white text-rose-600 font-bold text-xl flex items-center justify-center flex-shrink-0">Б</span>
            <h2 class="text-white font-bold text-lg leading-tight">{{ caseB?.title }}</h2>
          </div>
          <div class="flex-1 px-6 py-5 flex flex-col gap-5">
            <p class="text-gray-700 text-base leading-relaxed">{{ caseB?.description }}</p>

            <div>
              <p class="text-xs font-semibold text-rose-600 uppercase tracking-wider mb-2">Аргументы</p>
              <ul class="space-y-2">
                <li
                  v-for="(arg, i) in caseB?.key_arguments"
                  :key="i"
                  class="flex items-start gap-2 text-sm text-gray-800"
                >
                  <span class="mt-0.5 w-5 h-5 rounded-full bg-rose-100 text-rose-700 text-xs font-bold flex items-center justify-center flex-shrink-0">{{ i + 1 }}</span>
                  {{ arg }}
                </li>
              </ul>
            </div>

            <div v-if="caseB?.nuance" class="mt-auto bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              <p class="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-1">Нюанс</p>
              <p class="text-sm text-amber-800">{{ caseB.nuance }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom zone: show solution / synthesis -->
      <div class="mt-8 flex flex-col items-center gap-5">

        <!-- Timer expired — show solution button -->
        <div v-if="timeLeft === 0 && !synthesisVisible" class="text-center">
          <p class="text-gray-400 text-sm mb-3">Время вышло — обсуждение завершено</p>
          <button
            class="px-10 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-lg transition-colors shadow-sm"
            @click="synthesisVisible = true"
          >
            Показать решение
          </button>
        </div>

        <!-- Synthesis block -->
        <div
          v-if="synthesisVisible && synthesis"
          class="w-full max-w-3xl bg-white border-2 border-green-200 rounded-2xl px-8 py-6 shadow-sm"
        >
          <p class="text-xs font-semibold text-green-600 uppercase tracking-wider mb-3">💡 Вывод</p>
          <p class="text-gray-800 text-base leading-relaxed">{{ synthesis }}</p>
        </div>

        <router-link
          v-if="synthesisVisible"
          :to="`/lessons/${lessonId}`"
          class="px-10 py-3 border-2 border-gray-300 hover:border-gray-400 text-gray-600 rounded-xl font-semibold transition-colors"
        >
          Вернуться к уроку
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/services/api'

interface BattleCase {
  side: string
  title?: string
  description?: string
  key_arguments?: string[]
  nuance?: string
  text?: string
}

const route = useRoute()
const lessonId = route.params.id as string
const assignmentId = route.params.assignmentId as string

const loading = ref(true)
const cases = ref<BattleCase[]>([])
const timeLeft = ref(0)
const synthesisVisible = ref(false)

const caseA = computed(() => cases.value.find(c => c.side === 'A'))
const caseB = computed(() => cases.value.find(c => c.side === 'B'))
const synthesis = computed(() => cases.value.find(c => c.side === 'synthesis')?.text ?? '')

let timerId: ReturnType<typeof setInterval> | null = null

function startTimer(seconds: number) {
  timeLeft.value = seconds
  if (seconds === 0) return
  timerId = setInterval(() => {
    if (timeLeft.value <= 1) {
      timeLeft.value = 0
      if (timerId) { clearInterval(timerId); timerId = null }
    } else {
      timeLeft.value--
    }
  }, 1000)
}

onUnmounted(() => {
  if (timerId) clearInterval(timerId)
})

async function load() {
  try {
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    cases.value = res.data.questions_data?.cases ?? []
    startTimer(res.data.timer_seconds ?? 0)
  } finally {
    loading.value = false
  }
}

load()
</script>
