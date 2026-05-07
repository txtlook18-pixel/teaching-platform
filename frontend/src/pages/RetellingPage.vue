<template>
  <AppLayout>
    <div class="mb-6">
      <router-link :to="`/lessons/${lessonId}`" class="text-blue-600 hover:underline text-sm">
        ← Назад к уроку
      </router-link>
      <div class="flex items-center justify-between mt-2">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ topic || 'ИИ-отчёт' }}</h1>
          <p class="text-sm text-gray-500 mt-0.5">Отчёт по материалу урока</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            v-if="!chatOpen"
            class="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all text-sm font-medium"
            @click="openChat"
          >
            <span>💬</span> Открыть чат с ИИ
          </button>
          <button
            class="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-all text-sm font-medium"
            @click="finish"
          >
            Завершить
          </button>
        </div>
      </div>
    </div>

    <div class="flex gap-6 items-start">
      <!-- Report section -->
      <div class="flex-1 card">
        <div class="mb-5">
          <h2 class="font-semibold text-gray-800 text-lg">Отчёт по материалу</h2>
        </div>

        <!-- Skeleton while loading -->
        <div v-if="loading" class="space-y-4 animate-pulse">
          <div class="h-5 bg-gray-200 rounded w-48"></div>
          <div class="space-y-2">
            <div class="h-4 bg-gray-200 rounded w-full"></div>
            <div class="h-4 bg-gray-200 rounded w-5/6"></div>
            <div class="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
          <div class="h-5 bg-gray-200 rounded w-40 mt-4"></div>
          <div class="space-y-2">
            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
            <div class="h-4 bg-gray-200 rounded w-5/6"></div>
            <div class="h-4 bg-gray-200 rounded w-2/3"></div>
            <div class="h-4 bg-gray-200 rounded w-4/5"></div>
          </div>
        </div>

        <!-- Report content -->
        <div v-else-if="report" class="report-body text-sm text-gray-700 leading-relaxed" v-html="reportHtml"></div>
        <div v-else class="text-gray-400 text-sm">Отчёт не найден.</div>
      </div>

      <!-- Chat panel -->
      <div
        v-if="chatOpen"
        class="w-96 flex-shrink-0 card flex flex-col"
        style="height: 600px;"
      >
        <div class="flex items-center justify-between mb-4 flex-shrink-0">
          <h3 class="font-semibold text-gray-800">💬 Чат с ИИ</h3>
          <button
            class="text-gray-400 hover:text-gray-700 text-xl leading-none"
            @click="closeChat"
          >✕</button>
        </div>

        <!-- Messages -->
        <div ref="messagesEl" class="flex-1 overflow-y-auto space-y-3 min-h-0 pr-1">
          <!-- Greeting -->
          <div v-if="messages.length === 0" class="text-center text-gray-400 text-xs py-8">
            Задайте вопрос по материалу урока
          </div>

          <div v-for="(msg, i) in messages" :key="i">
            <!-- User bubble -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="bg-blue-600 text-white text-sm px-3 py-2 rounded-2xl rounded-tr-sm max-w-[80%]">
                {{ msg.content }}
              </div>
            </div>

            <!-- AI bubble -->
            <div v-else>
              <div class="bg-gray-100 text-gray-800 text-sm px-3 py-2 rounded-2xl rounded-tl-sm max-w-[90%] leading-relaxed">
                {{ msg.content }}
              </div>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="chatLoading" class="flex gap-1 items-center pl-1">
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
          </div>
        </div>

        <!-- Input -->
        <div class="flex gap-2 pt-3 border-t border-gray-100 flex-shrink-0 mt-3">
          <input
            v-model="chatInput"
            class="input-field flex-1 text-sm"
            placeholder="Задайте вопрос..."
            :disabled="chatLoading"
            @keydown.enter.prevent="sendMessage"
          />
          <button
            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all text-sm font-medium"
            :disabled="chatLoading || !chatInput.trim()"
            @click="sendMessage"
          >→</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiClient } from '@/services/api'

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
}

const route = useRoute()
const router = useRouter()
const lessonId = route.params.id as string
const assignmentId = route.params.assignmentId as string

const loading = ref(true)
const report = ref('')
const topic = ref('')

const chatOpen = ref(false)
const messages = ref<ChatMsg[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const messagesEl = ref<HTMLElement | null>(null)

// Convert markdown-like sections from AI report to HTML
const reportHtml = computed(() => {
  if (!report.value) return ''
  return report.value
    .replace(/^## (.+)$/gm, '<h3 class="report-heading">$1</h3>')
    .replace(/^\*\*(.+?)\*\* — (.+)$/gm, '<p class="report-term"><strong>$1</strong> — $2</p>')
    .replace(/^\*\*(.+?)\*\*$/gm, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]*?<\/li>)(\n(?!<li>))/g, '<ul>$1</ul>$2')
    .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul class="report-list">${match}</ul>`)
    .replace(/\n{2,}/g, '</p><p class="report-para">')
    .replace(/^(?!<[hup])(.+)$/gm, '<p class="report-para">$1</p>')
    .replace(/<p class="report-para"><\/p>/g, '')
})

function openChat() {
  chatOpen.value = true
}

function finish() {
  router.push(`/lessons/${lessonId}`)
}

function closeChat() {
  chatOpen.value = false
}

async function sendMessage() {
  const text = chatInput.value.trim()
  if (!text || chatLoading.value) return

  messages.value.push({ role: 'user', content: text })
  chatInput.value = ''
  chatLoading.value = true
  await scrollToBottom()

  try {
    const res = await apiClient.post(`/assignments/${assignmentId}/chat`, {
      message: text,
      history: messages.value.slice(0, -1),
    })
    messages.value.push({ role: 'assistant', content: res.data.reply })
  } catch {
    messages.value.push({ role: 'assistant', content: 'Произошла ошибка. Попробуйте ещё раз.' })
  } finally {
    chatLoading.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

onMounted(async () => {
  try {
    const res = await apiClient.get(`/assignments/${assignmentId}`)
    const data = res.data
    const qd = data.questions_data
    report.value = qd?.reference || ''
    topic.value = qd?.topic || ''
  } catch {
    report.value = ''
  } finally {
    loading.value = false
  }
})

</script>

<style scoped>
:deep(.report-heading) {
  font-size: 1rem;
  font-weight: 700;
  color: #1e40af;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #dbeafe;
}
:deep(.report-list) {
  list-style: disc;
  padding-left: 1.25rem;
  margin: 0.5rem 0;
  space-y: 0.25rem;
}
:deep(.report-list li) {
  margin-bottom: 0.25rem;
}
:deep(.report-term) {
  margin: 0.25rem 0;
}
:deep(.report-para) {
  margin: 0.4rem 0;
}
</style>
