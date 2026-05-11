<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <div class="text-center mb-8">
        <span class="text-5xl">🔑</span>
        <h1 class="text-2xl font-bold mt-3 text-gray-900">{{ t('forgotPassword.title') }}</h1>
        <p class="text-gray-500 mt-1">{{ t('forgotPassword.subtitle') }}</p>
      </div>

      <template v-if="!sent">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('forgotPassword.emailLabel') }}</label>
            <input
              v-model="email"
              type="email"
              class="input-field"
              placeholder="teacher@school.com"
              required
            />
          </div>

          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full py-3 text-base" :disabled="loading">
            {{ loading ? t('forgotPassword.submitting') : t('forgotPassword.submit') }}
          </button>
        </form>
      </template>

      <template v-else>
        <div class="bg-green-50 text-green-700 text-sm p-4 rounded-lg text-center">
          {{ t('forgotPassword.sentMessage') }}
        </div>
      </template>

      <p class="text-center text-sm text-gray-500 mt-6">
        <router-link to="/login" class="text-blue-600 hover:underline">
          {{ t('forgotPassword.backToLogin') }}
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()

const email = ref('')
const loading = ref(false)
const error = ref('')
const sent = ref(false)

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    await authStore.forgotPassword(email.value)
    sent.value = true
  } catch {
    error.value = t('forgotPassword.error')
  } finally {
    loading.value = false
  }
}
</script>
