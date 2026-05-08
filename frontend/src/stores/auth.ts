import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'
import type { User, TokenResponse } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res = await apiClient.post<TokenResponse>('/auth/login', { email, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  async function forgotPassword(email: string) {
    await apiClient.post('/auth/forgot-password', { email })
  }

  async function resetPassword(resetToken: string, newPassword: string) {
    await apiClient.post('/auth/reset-password', { token: resetToken, new_password: newPassword })
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, login, forgotPassword, resetPassword, logout }
})
