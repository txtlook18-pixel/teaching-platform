<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <div class="text-center mb-8">
        <span class="text-5xl">🔐</span>
        <h1 class="text-2xl font-bold mt-3 text-gray-900">Новый пароль</h1>
        <p class="text-gray-500 mt-1">Введите новый пароль для вашей учётной записи</p>
      </div>

      <template v-if="!tokenPresent">
        <div class="bg-red-50 text-red-600 text-sm p-4 rounded-lg text-center">
          Недействительная ссылка. Запросите сброс пароля заново.
        </div>
      </template>

      <template v-else-if="!done">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Новый пароль</label>
            <input
              v-model="password"
              type="password"
              class="input-field"
              placeholder="Минимум 6 символов"
              minlength="6"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Повторите пароль</label>
            <input
              v-model="passwordConfirm"
              type="password"
              class="input-field"
              placeholder="••••••••"
              required
            />
          </div>

          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full py-3 text-base" :disabled="loading">
            {{ loading ? 'Сохраняем...' : 'Сохранить пароль' }}
          </button>
        </form>
      </template>

      <template v-else>
        <div class="bg-green-50 text-green-700 text-sm p-4 rounded-lg text-center">
          Пароль успешно изменён. Теперь вы можете войти.
        </div>
        <p class="text-center text-sm text-gray-500 mt-6">
          <router-link to="/login" class="text-blue-600 hover:underline">Войти в аккаунт</router-link>
        </p>
      </template>

      <template v-if="!done && tokenPresent">
        <p class="text-center text-sm text-gray-500 mt-6">
          <router-link to="/login" class="text-blue-600 hover:underline">← Вернуться ко входу</router-link>
        </p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const token = computed(() => route.query.token as string | undefined)
const tokenPresent = computed(() => !!token.value)

const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')
const done = ref(false)

async function handleSubmit() {
  if (password.value !== passwordConfirm.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authStore.resetPassword(token.value!, password.value)
    done.value = true
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ссылка недействительна или истёк срок действия'
  } finally {
    loading.value = false
  }
}
</script>
