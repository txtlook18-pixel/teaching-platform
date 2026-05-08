import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

const mockGet = vi.mocked(apiClient.get)
const mockPost = vi.mocked(apiClient.post)
const mockDelete = vi.mocked(apiClient.delete)

const FAKE_LESSON = {
  id: 'lesson-1',
  title: 'Photosynthesis',
  language: 'en',
  source_type: 'text',
  source_content: 'Plants convert sunlight...',
  teacher_id: 'user-1',
  cluster_data: null,
  created_at: '2026-05-08T10:00:00Z',
}

describe('Lesson Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty lessons list', () => {
    const store = useLessonStore()
    expect(store.lessons).toEqual([])
    expect(store.currentLesson).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('fetchLessons populates lessons array', async () => {
    mockGet.mockResolvedValueOnce({ data: [FAKE_LESSON] })

    const store = useLessonStore()
    await store.fetchLessons()

    expect(store.lessons).toHaveLength(1)
    expect(store.lessons[0].title).toBe('Photosynthesis')
    expect(store.loading).toBe(false)
  })

  it('fetchLessons sets loading to false even on error', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'))

    const store = useLessonStore()
    await expect(store.fetchLessons()).rejects.toThrow()
    expect(store.loading).toBe(false)
  })

  it('fetchLesson sets currentLesson', async () => {
    mockGet.mockResolvedValueOnce({ data: FAKE_LESSON })

    const store = useLessonStore()
    const lesson = await store.fetchLesson('lesson-1')

    expect(store.currentLesson?.id).toBe('lesson-1')
    expect(lesson.title).toBe('Photosynthesis')
  })

  it('createLesson adds to front of list', async () => {
    const existingLesson = { ...FAKE_LESSON, id: 'old', title: 'Old Lesson' }
    const newLesson = { ...FAKE_LESSON, id: 'new', title: 'New Lesson' }

    const store = useLessonStore()
    store.lessons = [existingLesson as any]
    mockPost.mockResolvedValueOnce({ data: newLesson })

    await store.createLesson({ title: 'New Lesson', language: 'en', source_type: 'text', source_content: 'Content' })

    expect(store.lessons[0].title).toBe('New Lesson')
    expect(store.lessons[1].title).toBe('Old Lesson')
  })

  it('analyzeLesson updates currentLesson and list item', async () => {
    const analyzed = { ...FAKE_LESSON, cluster_data: { main_topic: 'Photosynthesis' } }

    const store = useLessonStore()
    store.lessons = [FAKE_LESSON as any]
    mockPost.mockResolvedValueOnce({ data: analyzed })

    await store.analyzeLesson('lesson-1')

    expect(store.currentLesson?.cluster_data).toEqual({ main_topic: 'Photosynthesis' })
    expect((store.lessons[0] as any).cluster_data).toEqual({ main_topic: 'Photosynthesis' })
  })

  it('deleteLesson removes from list', async () => {
    mockDelete.mockResolvedValueOnce({ data: {} })

    const store = useLessonStore()
    store.lessons = [FAKE_LESSON as any, { ...FAKE_LESSON, id: 'lesson-2', title: 'Other' } as any]

    await store.deleteLesson('lesson-1')

    expect(store.lessons).toHaveLength(1)
    expect(store.lessons[0].id).toBe('lesson-2')
  })

  it('fetchLessons returns empty array when API returns empty', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })

    const store = useLessonStore()
    await store.fetchLessons()
    expect(store.lessons).toEqual([])
  })
})
