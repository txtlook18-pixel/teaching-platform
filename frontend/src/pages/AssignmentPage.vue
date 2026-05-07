<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="assignment">
      <!-- Header -->
      <div class="mb-6 flex justify-between items-center flex-wrap gap-3">
        <div>
          <router-link :to="`/lessons/${route.params.id}`" class="text-blue-600 hover:underline text-sm">
            ← Назад к уроку
          </router-link>
          <h1 class="text-2xl font-bold mt-1 flex items-center gap-3 flex-wrap">
            {{ typeLabel }} — {{ statusLabel }}
            <LiveBadge v-if="assignment.status === 'active'" :connected="wsConnected" />
          </h1>
        </div>
        <button v-if="assignment.status === 'active'" class="btn-danger" @click="handleFinish">
          Завершить
        </button>
      </div>

      <!-- Active: QR + students panel -->
      <div v-if="assignment.status === 'active'" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- QR block -->
        <div class="card text-center">
          <h2 class="font-semibold text-gray-700 mb-4">QR для студентов</h2>
          <div v-if="qrDataUrl" class="flex justify-center mb-4">
            <img :src="qrDataUrl" alt="QR Code" class="w-48 h-48 border-4 border-white shadow-md rounded-lg" />
          </div>
          <p class="text-sm text-gray-500 mb-2">Или ссылка:</p>
          <code class="text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ joinUrl }}</code>
          <p class="text-xs text-amber-600 mt-3">
            Истекает:
            {{ assignment.session_expires_at
              ? new Date(assignment.session_expires_at).toLocaleTimeString('ru-RU')
              : '—' }}
          </p>
        </div>

        <!-- Students list -->
        <div class="card flex flex-col">
          <h2 class="font-semibold text-gray-700 mb-4">
            Студенты
            <span class="ml-1 text-blue-600 font-bold">{{ onlineCount }}</span>
            онлайн / {{ sessions.length }} зашли
          </h2>

          <div v-if="sessions.length === 0" class="text-center py-8 text-gray-400 flex-1">
            Ждём студентов...
          </div>
          <ul v-else class="space-y-2 max-h-52 overflow-y-auto pr-1 flex-1">
            <li v-for="s in sessions" :key="s.id" class="flex items-center gap-2">
              <span
                class="w-2 h-2 rounded-full flex-shrink-0 transition-colors"
                :class="onlineIds.has(s.id) ? 'bg-green-400' : 'bg-gray-300'"
              ></span>
              <span class="text-sm">{{ s.student_name }}</span>
            </li>
          </ul>

          <!-- Phone mode: start button -->
          <div v-if="isPhoneMode" class="mt-4 space-y-2">
            <button
              v-if="!testStarted"
              class="btn-primary w-full py-3 text-base font-semibold"
              :disabled="sessions.length === 0"
              @click="handleStart"
            >
              🚀 Начать тест ({{ sessions.length }} {{ sessions.length === 1 ? 'студент' : sessions.length < 5 ? 'студента' : 'студентов' }})
            </button>
            <div v-else class="text-center py-2 text-green-600 font-medium text-sm">
              ✅ Тест запущен — студенты проходят
            </div>
            <button class="btn-secondary w-full text-sm" @click="fetchResults">Обновить</button>
          </div>
          <button v-else class="btn-secondary w-full mt-4 text-sm" @click="fetchResults">
            Обновить
          </button>
        </div>
      </div>

      <!-- Responses table -->
      <div v-if="responses.length > 0" class="card">
        <h2 class="font-semibold text-gray-700 mb-4">Ответы студентов ({{ responses.length }})</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-gray-400 text-left">
                <th class="pb-2 pr-3">Студент</th>
                <th class="pb-2 pr-3">Вопрос</th>
                <th class="pb-2 pr-3">Сложность</th>
                <th class="pb-2 pr-3">Ответ</th>
                <th class="pb-2 pr-3">Итог</th>
                <th class="pb-2">Время</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in responses" :key="r.id" class="border-b hover:bg-gray-50">
                <td class="py-2 pr-3 font-medium">{{ getStudentName(r.student_session_id) }}</td>
                <td class="py-2 pr-3 text-gray-500">{{ r.question_index }}</td>
                <td class="py-2 pr-3">
                  <span
                    v-if="r.question_difficulty"
                    class="px-2 py-0.5 rounded text-xs"
                    :class="{
                      'bg-green-100 text-green-700': r.question_difficulty === 'easy',
                      'bg-yellow-100 text-yellow-700': r.question_difficulty === 'medium',
                      'bg-red-100 text-red-700': r.question_difficulty === 'hard',
                    }"
                  >{{ r.question_difficulty }}</span>
                  <span v-else class="text-gray-300">—</span>
                </td>
                <td class="py-2 pr-3 max-w-xs truncate text-gray-700">{{ formatAnswer(r.answer_data) }}</td>
                <td class="py-2 pr-3">
                  <span v-if="r.is_correct === true" class="text-green-600 font-semibold">✓</span>
                  <span v-else-if="r.is_correct === false" class="text-red-500 font-semibold">✗</span>
                  <span v-else class="text-gray-300">—</span>
                </td>
                <td class="py-2 text-gray-400 whitespace-nowrap">
                  {{ new Date(r.answered_at).toLocaleTimeString('ru-RU') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Finished / no results yet -->
      <div v-else-if="assignment.status !== 'active'" class="card text-center py-12 text-gray-400">
        Ответов пока нет.
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import LiveBadge from '@/components/common/LiveBadge.vue'
import { apiClient } from '@/services/api'
import { useTeacherWS } from '@/services/websocket'
import type { Assignment, StudentSession, StudentResponse } from '@/types'
import QRCode from 'qrcode'

const route  = useRoute()
const router = useRouter()

const assignmentId = route.params.assignmentId as string

const loading    = ref(true)
const assignment = ref<Assignment | null>(null)
const sessions   = ref<StudentSession[]>([])
const responses  = ref<StudentResponse[]>([])
const qrDataUrl  = ref('')
const testStarted = ref(false)

// Track which session IDs are currently online (via WS events)
const onlineIds  = reactive(new Set<string>())
const onlineCount = ref(0)

let refreshTimer: ReturnType<typeof setTimeout> | null = null

// ── WebSocket (teacher) ───────────────────────────────────────────────────────
// Called at setup level so Vue lifecycle hooks inside the composable work.
const { connected: wsConnected, connect: wsConnect, send: wsSend } = useTeacherWS(assignmentId, {
  onStudentJoined(e) {
    onlineIds.add(e.session_id)
    onlineCount.value = e.online_count ?? onlineIds.size
    if (!sessions.value.find((s) => s.id === e.session_id)) {
      sessions.value.push({
        id: e.session_id,
        assignment_id: assignmentId,
        student_name: e.student_name,
        joined_at: new Date().toISOString(),
      })
    }
  },
  onStudentLeft(e) {
    onlineIds.delete(e.session_id)
    onlineCount.value = e.online_count ?? onlineIds.size
  },
  onStudentAnswered() {
    scheduleRefresh()
  },
})

// ── Helpers ───────────────────────────────────────────────────────────────────

const joinUrl = computed(() =>
  assignment.value?.session_token
    ? `${window.location.origin}/join?token=${assignment.value.session_token}`
    : '',
)

const isPhoneMode = computed(() =>
  assignment.value?.assignment_type === 'test' &&
  assignment.value?.settings_data?.mode === 'individual'
)

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    test: '🧪 Тест', battle: '⚔️ Баттл', analysis: '🔍 Анализ',
    cards: '🎴 Карточки', retelling: '📝 Пересказ',
  }
  return map[assignment.value?.assignment_type ?? ''] ?? ''
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    draft: 'Черновик', active: 'Активно', finished: 'Завершено', archived: 'Архив',
  }
  return map[assignment.value?.status ?? ''] ?? ''
})

function getStudentName(sessionId: string) {
  return sessions.value.find((s) => s.id === sessionId)?.student_name ?? sessionId
}

function formatAnswer(data: any): string {
  if (!data) return '—'
  if (typeof data.text === 'string')         return data.text.slice(0, 120)
  if (typeof data.answer_text === 'string')  return data.answer_text
  if ('knew' in data)                        return `${data.knew ? '✓' : '✗'} ${data.term ?? ''}`
  return JSON.stringify(data)
}

// ── Data fetching ─────────────────────────────────────────────────────────────

async function fetchResults() {
  const res = await apiClient.get(`/assignments/${assignmentId}/results`)
  sessions.value  = res.data.sessions
  responses.value = res.data.responses
  // Sync online count with actual session list on manual refresh
  onlineCount.value = Math.max(onlineCount.value, sessions.value.length)
}

function scheduleRefresh() {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(fetchResults, 600)
}

function handleStart() {
  wsSend({ action: 'start' })
  router.push(`/lessons/${route.params.id}/phone-test/${assignmentId}`)
}

async function handleFinish() {
  if (!confirm('Завершить задание для всех студентов?')) return
  await apiClient.post(`/assignments/${assignmentId}/finish`)
  if (assignment.value) assignment.value.status = 'finished'
  // Also signal via WS so students who are still connected get the event immediately
  wsSend({ action: 'finish' })
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const aRes = await apiClient.get(`/assignments/lessons/${route.params.id}/assignments`)
    const all: Assignment[] = aRes.data
    assignment.value = all.find((a) => a.id === assignmentId) ?? null

    if (!assignment.value) {
      router.push(`/lessons/${route.params.id}`)
      return
    }

    if (assignment.value.session_token && joinUrl.value) {
      qrDataUrl.value = await QRCode.toDataURL(joinUrl.value, { width: 200 })
    }

    await fetchResults()

    if (assignment.value.status === 'active') {
      wsConnect()
    }
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (refreshTimer) clearTimeout(refreshTimer)
})
</script>
