<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex flex-col">

    <!-- ── FINISHED: student results ─────────────────────────────── -->
    <div v-if="phase === 'finished'" class="flex-1 p-8 max-w-4xl mx-auto w-full">
      <div class="flex items-center gap-4 mb-8">
        <router-link :to="`/lessons/${lessonId}`" class="text-gray-500 hover:text-gray-800 text-sm">← Назад к уроку</router-link>
        <h1 class="text-2xl font-bold text-gray-900">Итоги теста</h1>
        <span class="text-gray-400 text-sm ml-auto">{{ sessions.length }} студентов</span>
      </div>

      <div class="space-y-3">
        <div
          v-for="s in sessionsSorted"
          :key="s.id"
          class="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm"
        >
          <button
            class="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
            @click="toggleStudent(s.id)"
          >
            <div class="flex items-center gap-3">
              <span class="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold">
                {{ s.student_name[0]?.toUpperCase() }}
              </span>
              <span class="font-medium text-gray-900">{{ s.student_name }}</span>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-lg font-bold" :class="scoreColor(s.id)">
                {{ correctCount(s.id) }} / {{ questions.length }}
              </span>
              <span class="text-gray-400 text-sm">
                {{ Math.round((correctCount(s.id) / questions.length) * 100) }}%
              </span>
              <span class="text-gray-400 text-xs transition-transform" :class="expandedStudents.has(s.id) ? 'rotate-180' : ''">▼</span>
            </div>
          </button>

          <div v-if="expandedStudents.has(s.id)" class="border-t border-gray-100 px-6 py-4 space-y-2">
            <div
              v-for="(q, qi) in questions"
              :key="qi"
              class="flex items-start gap-3 text-sm"
            >
              <span class="mt-0.5 flex-shrink-0 text-base" :class="isStudentCorrect(s.id, qi) ? 'text-green-600' : 'text-red-500'">
                {{ isStudentCorrect(s.id, qi) ? '✓' : '✗' }}
              </span>
              <span class="text-gray-600 leading-snug">{{ q.question }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── ACTIVE TEST ────────────────────────────────────────────── -->
    <div v-else class="flex-1 flex flex-col">

      <!-- header -->
      <div class="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 shadow-sm">
        <div class="flex items-center gap-4">
          <router-link :to="`/lessons/${lessonId}`" class="text-gray-500 hover:text-gray-800 text-sm">← Урок</router-link>
          <div class="flex gap-1.5">
            <span
              v-for="(_, qi) in questions"
              :key="qi"
              class="w-2.5 h-2.5 rounded-full transition-colors"
              :class="qi < currentIndex ? 'bg-green-500' : qi === currentIndex ? 'bg-indigo-600' : 'bg-gray-300'"
            ></span>
          </div>
        </div>
        <div class="flex items-center gap-6">
          <span class="text-gray-500 text-sm">
            <span class="text-gray-900 font-bold">{{ answeredCount }}</span> / {{ sessions.length }} ответили
          </span>
          <span class="text-gray-400 text-sm">Вопрос {{ currentIndex + 1 }} / {{ questions.length }}</span>
        </div>
      </div>

      <!-- question -->
      <div class="flex-1 flex flex-col items-center justify-center px-8 py-6">
        <div class="w-full max-w-3xl">

          <div class="mb-2 flex items-center gap-3">
            <span
              class="px-3 py-1 rounded-full text-xs font-semibold capitalize"
              :class="{
                'bg-green-100 text-green-700': currentQuestion?.level === 'easy',
                'bg-yellow-100 text-yellow-700': currentQuestion?.level === 'medium',
                'bg-red-100 text-red-700': currentQuestion?.level === 'hard',
              }"
            >{{ currentQuestion?.level }}</span>
          </div>

          <p class="text-3xl font-bold leading-relaxed mb-10 text-gray-900">
            {{ currentQuestion?.question }}
          </p>

          <!-- ASKING: same-color answer tiles -->
          <div v-if="phase === 'question'" class="grid grid-cols-2 gap-4">
            <div
              v-for="(ans, i) in currentQuestion?.answers"
              :key="i"
              class="bg-indigo-600 rounded-2xl p-5 flex items-center gap-4 text-white"
            >
              <span class="text-2xl font-black opacity-60">{{ ['A','B','C','D'][i as number] }}</span>
              <span class="text-lg font-semibold leading-snug">{{ ans.text }}</span>
            </div>
          </div>

          <!-- CHECKED: bars with % -->
          <div v-else-if="phase === 'checked'" class="space-y-4">
            <div
              v-for="(ans, i) in currentQuestion?.answers"
              :key="i"
              class="rounded-2xl p-5 border-2 transition-all"
              :class="ans.correct
                ? 'bg-green-50 border-green-400'
                : 'bg-gray-100 border-gray-200'"
            >
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-4">
                  <span class="text-2xl font-black text-gray-400">{{ ['A','B','C','D'][i as number] }}</span>
                  <span class="text-lg font-semibold text-gray-900">{{ ans.text }}</span>
                  <span v-if="ans.correct" class="text-green-600 font-bold text-sm">✓ Правильно</span>
                </div>
                <span class="text-2xl font-black text-gray-700">{{ answerStats[i as number] ?? 0 }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-4">
                <div
                  class="h-4 rounded-full transition-all duration-700"
                  :class="ans.correct ? 'bg-green-500' : 'bg-indigo-400'"
                  :style="`width: ${answerStats[i as number] ?? 0}%`"
                ></div>
              </div>
              <div class="mt-1 text-sm text-right text-gray-400">
                {{ answerCounts[i as number] ?? 0 }} чел.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- controls -->
      <div class="flex items-center justify-between px-8 py-5 bg-white border-t border-gray-200 shadow-sm">
        <button class="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors" @click="handleFinish">
          Завершить
        </button>

        <div class="flex gap-3">
          <button
            v-if="phase === 'question'"
            class="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold transition-colors"
            @click="handleCheck"
          >
            Проверить
          </button>
          <button
            v-else-if="phase === 'checked' && currentIndex < questions.length - 1"
            class="px-8 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold transition-colors"
            @click="handleNext"
          >
            Вперёд →
          </button>
          <button
            v-else-if="phase === 'checked'"
            class="px-8 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold transition-colors"
            @click="handleFinish"
          >
            Завершить тест →
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/services/api'
import { useTeacherWS } from '@/services/websocket'
import type { Assignment, StudentSession, StudentResponse } from '@/types'

const route        = useRoute()
const router       = useRouter()
const assignmentId = route.params.assignmentId as string
const lessonId     = route.params.id as string

const loading      = ref(true)
const assignment   = ref<Assignment | null>(null)
const sessions     = ref<StudentSession[]>([])
const responses    = ref<StudentResponse[]>([])
const currentIndex = ref(0)
const phase        = ref<'question' | 'checked' | 'finished'>('question')
const answerStats  = ref<number[]>([])
const answerCounts = ref<number[]>([])
const answeredCount = ref(0)
const expandedStudents = reactive(new Set<string>())


// ── WebSocket ─────────────────────────────────────────────────────────────────

const { connect: wsConnect, send: wsSend } = useTeacherWS(assignmentId, {
  onStudentJoined(e) {
    if (!sessions.value.find((s) => s.id === e.session_id)) {
      sessions.value.push({
        id: e.session_id,
        assignment_id: assignmentId,
        student_name: e.student_name,
        joined_at: new Date().toISOString(),
      })
    }
  },
  onStudentAnswered() {
    answeredCount.value++
  },
})

// ── Computed ──────────────────────────────────────────────────────────────────

const questions       = computed(() => (assignment.value?.questions_data?.questions ?? []) as any[])
const currentQuestion = computed(() => questions.value[currentIndex.value] ?? null)

const sessionsSorted = computed(() =>
  [...sessions.value].sort((a, b) => correctCount(b.id) - correctCount(a.id))
)

function correctCount(sessionId: string) {
  return responses.value.filter((r) => r.student_session_id === sessionId && r.is_correct).length
}

function isStudentCorrect(sessionId: string, qi: number) {
  return responses.value.some(
    (r) => r.student_session_id === sessionId && r.question_index === String(qi) && r.is_correct,
  )
}

function scoreColor(sessionId: string) {
  const pct = (correctCount(sessionId) / (questions.value.length || 1)) * 100
  if (pct >= 80) return 'text-green-600'
  if (pct >= 50) return 'text-yellow-600'
  return 'text-red-500'
}

function toggleStudent(id: string) {
  if (expandedStudents.has(id)) expandedStudents.delete(id)
  else expandedStudents.add(id)
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function handleCheck() {
  const res = await apiClient.get(`/assignments/${assignmentId}/results`)
  sessions.value  = res.data.sessions
  responses.value = res.data.responses

  const forQuestion = (responses.value as StudentResponse[]).filter(
    (r) => r.question_index === String(currentIndex.value),
  )
  const total = forQuestion.length || 1

  answerCounts.value = [0, 1, 2, 3].map((i) =>
    forQuestion.filter((r) => r.answer_data?.answer_index === i).length,
  )
  answerStats.value = answerCounts.value.map((c) => Math.round((c / total) * 100))
  answeredCount.value = forQuestion.length
  phase.value = 'checked'
}

function handleNext() {
  currentIndex.value++
  answeredCount.value = 0
  answerStats.value  = []
  answerCounts.value = []
  phase.value = 'question'
  wsSend({ action: 'next_question', question_index: currentIndex.value })
}

async function handleFinish() {
  if (!confirm('Завершить тест для всех студентов?')) return
  await apiClient.post(`/assignments/${assignmentId}/finish`)
  wsSend({ action: 'finish' })
  if (assignment.value) assignment.value.status = 'finished'

  const res = await apiClient.get(`/assignments/${assignmentId}/results`)
  sessions.value  = res.data.sessions
  responses.value = res.data.responses
  phase.value = 'finished'
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const aRes = await apiClient.get(`/assignments/${assignmentId}`)
    assignment.value = aRes.data as Assignment

    const rRes = await apiClient.get(`/assignments/${assignmentId}/results`)
    sessions.value  = rRes.data.sessions
    responses.value = rRes.data.responses

    wsConnect()
  } finally {
    loading.value = false
  }
})
</script>
