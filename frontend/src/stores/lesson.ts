import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '@/services/api'
import type { Lesson } from '@/types'

export const useLessonStore = defineStore('lesson', () => {
  const lessons = ref<Lesson[]>([])
  const currentLesson = ref<Lesson | null>(null)
  const loading = ref(false)

  async function fetchLessons() {
    loading.value = true
    try {
      const res = await apiClient.get<Lesson[]>('/lessons/')
      lessons.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchLesson(id: string) {
    loading.value = true
    try {
      const res = await apiClient.get<Lesson>(`/lessons/${id}`)
      currentLesson.value = res.data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function createLesson(data: {
    title: string
    language: string
    source_type: string
    source_content: string
  }) {
    const res = await apiClient.post<Lesson>('/lessons/', data)
    lessons.value.unshift(res.data)
    return res.data
  }

  async function fetchLessonUrl(id: string) {
    const res = await apiClient.post<Lesson>(`/lessons/${id}/fetch-url`)
    currentLesson.value = res.data
    return res.data
  }

  async function analyzeLesson(id: string) {
    const res = await apiClient.post<Lesson>(`/lessons/${id}/analyze`)
    currentLesson.value = res.data
    const idx = lessons.value.findIndex((l) => l.id === id)
    if (idx !== -1) lessons.value[idx] = res.data
    return res.data
  }

  async function deleteLesson(id: string) {
    await apiClient.delete(`/lessons/${id}`)
    lessons.value = lessons.value.filter((l) => l.id !== id)
  }

  return { lessons, currentLesson, loading, fetchLessons, fetchLesson, createLesson, fetchLessonUrl, analyzeLesson, deleteLesson }
})
