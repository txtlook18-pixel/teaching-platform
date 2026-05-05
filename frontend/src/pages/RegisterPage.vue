<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <div class="text-center mb-8">
        <span class="text-5xl">🎓</span>
        <h1 class="text-2xl font-bold mt-3">Создать аккаунт</h1>
        <p class="text-gray-500 mt-1">Регистрация учителя</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Имя</label>
          <input v-model="form.username" type="text" class="input-field" placeholder="Иван Иванов" required />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="form.email" type="email" class="input-field" placeholder="teacher@school.com" required />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
          <input v-model="form.password" type="password" class="input-field" placeholder="Минимум 6 символов" required minlength="6" />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Telegram (необязательно)</label>
          <input v-model="form.telegram_username" type="text" class="input-field" placeholder="@username" />
        </div>

        <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ error }}</div>

        <button type="submit" class="btn-primary w-full py-3 text-base" :disabled="loading">
          {{ loading ? 'Регистрируем...' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-6">
        Уже есть аккаунт?
        <router-link to="/login" class="text-blue-600 hover:underline">Войти</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const form = ref({ username: '', email: '', password: '', telegram_username: '' })

async function handleRegister() {
  loading.value = true
  error.value = ''
  try {
    await authStore.register(form.value.email, form.value.username, form.value.password, form.value.telegram_username || undefined)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
