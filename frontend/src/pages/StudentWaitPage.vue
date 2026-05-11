<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm text-center">
      <div class="text-6xl mb-6">📱</div>
      <h1 class="text-2xl font-bold text-gray-800">{{ t('student.wait.title') }}</h1>
      <p class="text-gray-500 mt-2">
        {{ t('student.wait.hello') }}
        <span class="font-semibold text-gray-700">{{ studentName }}</span>!
      </p>
      <p class="text-gray-400 mt-1 text-sm">{{ t('student.wait.subtitle') }}</p>

      <div class="mt-8 flex justify-center gap-2">
        <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
        <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
        <div class="w-2.5 h-2.5 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
      </div>

      <p class="text-xs text-gray-300 mt-10">{{ t('student.wait.doNotClose') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStudentWS } from '@/services/websocket'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const sessionId = route.params.sessionId as string
const studentName = ref('')

const { connect: wsConnect } = useStudentWS(sessionId, {
  onTestStarted() {
    router.push(`/play/${sessionId}`)
  },
  onFinished() {
    router.push(`/play/${sessionId}`)
  },
})

onMounted(() => {
  const saved = localStorage.getItem('student_session')
  if (saved) {
    studentName.value = JSON.parse(saved).student_name ?? ''
  }
  wsConnect()
})
</script>
