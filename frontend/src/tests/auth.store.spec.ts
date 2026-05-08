import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/services/api'

vi.mock('@/services/api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

const mockPost = vi.mocked(apiClient.post)

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with null token when localStorage is empty', () => {
    const auth = useAuthStore()
    expect(auth.token).toBeNull()
    expect(auth.user).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('initializes from localStorage when token exists', () => {
    localStorage.setItem('access_token', 'fake-token')
    localStorage.setItem('user', JSON.stringify({ id: 'u1', email: 'a@b.com', username: 'Alice' }))
    setActivePinia(createPinia())
    const auth = useAuthStore()
    expect(auth.token).toBe('fake-token')
    expect(auth.user?.email).toBe('a@b.com')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('login sets token and user, saves to localStorage', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        access_token: 'jwt-token-123',
        user: { id: 'u1', email: 'teacher@test.com', username: 'Teacher' },
      },
    })

    const auth = useAuthStore()
    await auth.login('teacher@test.com', 'secret')

    expect(auth.token).toBe('jwt-token-123')
    expect(auth.user?.email).toBe('teacher@test.com')
    expect(auth.isAuthenticated).toBe(true)
    expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'jwt-token-123')
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'user',
      JSON.stringify({ id: 'u1', email: 'teacher@test.com', username: 'Teacher' })
    )
  })

  it('register sets token and user', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        access_token: 'new-jwt',
        user: { id: 'u2', email: 'new@test.com', username: 'New User' },
      },
    })

    const auth = useAuthStore()
    await auth.register('new@test.com', 'New User', 'password123')

    expect(auth.token).toBe('new-jwt')
    expect(auth.user?.username).toBe('New User')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('logout clears token, user, and localStorage', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'jwt', user: { id: 'u1', email: 'a@b.com', username: 'A' } },
    })

    const auth = useAuthStore()
    await auth.login('a@b.com', 'pw')
    expect(auth.isAuthenticated).toBe(true)

    auth.logout()

    expect(auth.token).toBeNull()
    expect(auth.user).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('user')
  })

  it('login throws error on API failure', async () => {
    mockPost.mockRejectedValueOnce({ response: { data: { detail: 'Invalid credentials' } } })

    const auth = useAuthStore()
    await expect(auth.login('bad@test.com', 'wrong')).rejects.toBeDefined()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('isAuthenticated is false without token', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('isAuthenticated is true with token', async () => {
    mockPost.mockResolvedValueOnce({
      data: { access_token: 'tok', user: { id: 'u1', email: 'e@t.com', username: 'U' } },
    })
    const auth = useAuthStore()
    await auth.login('e@t.com', 'p')
    expect(auth.isAuthenticated).toBe(true)
  })
})
