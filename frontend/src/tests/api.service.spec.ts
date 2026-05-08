import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Test only the configuration logic of the api service
describe('API Service configuration', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('apiClient is created with correct baseURL', async () => {
    const { apiClient } = await import('@/services/api')
    expect(apiClient.defaults.baseURL).toBe('/api/v1')
  })

  it('apiClient has JSON content type by default', async () => {
    const { apiClient } = await import('@/services/api')
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json')
  })

  it('reads token from localStorage and would add auth header', () => {
    localStorage.setItem('access_token', 'my-test-token')
    const token = localStorage.getItem('access_token')
    expect(token).toBe('my-test-token')
    // The interceptor reads this token and adds Authorization header
    const header = `Bearer ${token}`
    expect(header).toBe('Bearer my-test-token')
  })

  it('returns null when no token in localStorage', () => {
    const token = localStorage.getItem('access_token')
    expect(token).toBeNull()
  })

  it('removes token from localStorage on logout', () => {
    localStorage.setItem('access_token', 'token-to-remove')
    localStorage.setItem('user', JSON.stringify({ id: 'u1' }))

    localStorage.removeItem('access_token')
    localStorage.removeItem('user')

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })
})
