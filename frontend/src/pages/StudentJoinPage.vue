<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-sm">
      <div class="text-center mb-6">
        <span class="text-5xl">📱</span>
        <h1 class="text-xl font-bold mt-3">Присоединиться к заданию</h1>
      </div>

      <form @submit.prevent="handleJoin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Ваше имя</label>
          <input
            v-model="studentName"
            type="text"
            class="input-field"
            placeholder="Иван Иванов"
            required
          />
        </div>

        <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ error }}</div>

        <button type="submit" class="btn-primary w-full py-3" :disabled="loading || !token">
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>

      <p v-if="!token" class="text-center text-sm text-red-500 mt-4">
        Неверная ссылка. Попросите учителя поделиться QR-кодом.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/services/api'

const route = useRoute()
const router = useRouter()

const token = ref<string | null>(null)
const studentName = ref('')
const loading = ref(false)
const error = ref('')

onMounted(() => {
  token.value = route.query.token as string || null
})

async function handleJoin() {
  if (!token.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await apiClient.post('/assignments/join', {
      student_name: studentName.value,
      session_token: token.value,
    })
    localStorage.setItem('student_session', JSON.stringify(res.data))
    router.push(`/play/${res.data.session_id}`)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка подключения'
  } finally {
    loading.value = false
  }
}
</script>
