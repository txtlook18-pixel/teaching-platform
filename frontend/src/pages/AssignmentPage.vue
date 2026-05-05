<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="assignment">
      <div class="mb-6 flex justify-between items-center">
        <div>
          <router-link :to="`/lessons/${route.params.id}`" class="text-blue-600 hover:underline text-sm">← Назад к уроку</router-link>
          <h1 class="text-2xl font-bold mt-1">
            {{ typeLabel }} — {{ statusLabel }}
          </h1>
        </div>
        <button v-if="assignment.status === 'active'" class="btn-danger" @click="handleFinish">
          Завершить
        </button>
      </div>

      <!-- QR Code block -->
      <div v-if="assignment.status === 'active'" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="card text-center">
          <h2 class="font-semibold text-gray-700 mb-4">QR для студентов</h2>
          <div v-if="qrDataUrl" class="flex justify-center mb-4">
            <img :src="qrDataUrl" alt="QR Code" class="w-48 h-48 border-4 border-white shadow-md rounded-lg" />
          </div>
          <p class="text-sm text-gray-500 mb-2">Или ссылка:</p>
          <code class="text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ joinUrl }}</code>
          <p class="text-xs text-amber-600 mt-3">
            Истекает: {{ assignment.session_expires_at ? new Date(assignment.session_expires_at).toLocaleTimeString('ru-RU') : '—' }}
          </p>
        </div>

        <div class="card">
          <h2 class="font-semibold text-gray-700 mb-4">Студенты ({{ sessions.length }})</h2>
          <div v-if="sessions.length === 0" class="text-center py-8 text-gray-400">
            Ждём студентов...
          </div>
          <ul v-else class="space-y-2">
            <li v-for="s in sessions" :key="s.id" class="flex items-center gap-2">
              <span class="w-2 h-2 bg-green-400 rounded-full"></span>
              <span class="text-sm">{{ s.student_name }}</span>
            </li>
          </ul>
          <button class="btn-secondary w-full mt-4 text-sm" @click="fetchResults">Обновить</button>
        </div>
      </div>

      <!-- Results block -->
      <div v-if="responses.length > 0" class="card">
        <h2 class="font-semibold text-gray-700 mb-4">Ответы студентов ({{ responses.length }})</h2>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-gray-400">
                <th class="text-left pb-2">Студент</th>
                <th class="text-left pb-2">Вопрос</th>
                <th class="text-left pb-2">Сложность</th>
                <th class="text-left pb-2">Ответ</th>
                <th class="text-left pb-2">Время</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in responses" :key="r.id" class="border-b hover:bg-gray-50">
                <td class="py-2">{{ getStudentName(r.student_session_id) }}</td>
                <td class="py-2">{{ r.question_index }}</td>
                <td class="py-2">
                  <span
                    class="px-2 py-0.5 rounded text-xs"
                    :class="{
                      'bg-green-100 text-green-700': r.question_difficulty === 'easy',
                      'bg-yellow-100 text-yellow-700': r.question_difficulty === 'medium',
                      'bg-red-100 text-red-700': r.question_difficulty === 'hard',
                    }"
                  >{{ r.question_difficulty || '—' }}</span>
                </td>
                <td class="py-2 max-w-xs truncate">{{ JSON.stringify(r.answer_data) }}</td>
                <td class="py-2 text-gray-400">{{ new Date(r.answered_at).toLocaleTimeString('ru-RU') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiClient } from '@/services/api'
import type { Assignment, StudentSession, StudentResponse } from '@/types'
import QRCode from 'qrcode'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const assignment = ref<Assignment | null>(null)
const sessions = ref<StudentSession[]>([])
const responses = ref<StudentResponse[]>([])
const qrDataUrl = ref('')

const joinUrl = computed(() =>
  assignment.value?.session_token
    ? `${window.location.origin}/join?token=${assignment.value.session_token}`
    : ''
)

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    test: '🧪 Тест', battle: '⚔️ Баттл', analysis: '🔍 Анализ',
    cards: '🎴 Карточки', retelling: '📝 Пересказ',
  }
  return map[assignment.value?.assignment_type || ''] || ''
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    draft: 'Черновик', active: 'Активно', finished: 'Завершено', archived: 'Архив',
  }
  return map[assignment.value?.status || ''] || ''
})

function getStudentName(sessionId: string) {
  return sessions.value.find((s) => s.id === sessionId)?.student_name || sessionId
}

async function fetchResults() {
  const res = await apiClient.get(`/assignments/${route.params.assignmentId}/results`)
  sessions.value = res.data.sessions
  responses.value = res.data.responses
}

async function handleFinish() {
  if (!confirm('Завершить задание?')) return
  await apiClient.post(`/assignments/${route.params.assignmentId}/finish`)
  if (assignment.value) assignment.value.status = 'finished'
}

onMounted(async () => {
  try {
    const aRes = await apiClient.get(`/assignments/lessons/${route.params.id}/assignments`)
    const all: Assignment[] = aRes.data
    assignment.value = all.find((a) => a.id === route.params.assignmentId) || null

    if (!assignment.value) {
      router.push(`/lessons/${route.params.id}`)
      return
    }

    if (assignment.value.session_token && joinUrl.value) {
      qrDataUrl.value = await QRCode.toDataURL(joinUrl.value, { width: 200 })
    }

    await fetchResults()
  } finally {
    loading.value = false
  }
})
</script>
