<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <div class="text-center mb-8">
        <span class="text-5xl">🎓</span>
        <h1 class="text-2xl font-bold mt-3 text-gray-900">{{ t('login.title') }}</h1>
        <p class="text-gray-500 mt-1">{{ t('login.subtitle') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('login.emailLabel') }}</label>
          <input
            v-model="form.email"
            type="email"
            class="input-field"
            placeholder="teacher@school.com"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('login.passwordLabel') }}</label>
          <input
            v-model="form.password"
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
          {{ loading ? t('login.submitting') : t('login.submit') }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-4">
        <router-link to="/forgot-password" class="text-blue-600 hover:underline">
          {{ t('login.forgotPassword') }}
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { translateApiError } from '@/i18n'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const form = ref({ email: '', password: '' })

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.value.email, form.value.password)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = translateApiError(e.response?.data?.detail, t('login.defaultError'))
  } finally {
    loading.value = false
  }
}
</script>
