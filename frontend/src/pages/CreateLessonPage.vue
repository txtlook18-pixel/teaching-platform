<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto">
      <div class="mb-8">
        <router-link to="/dashboard" class="text-blue-600 hover:underline text-sm">← Назад</router-link>
        <h1 class="text-3xl font-bold mt-2">Создать урок</h1>
        <p class="text-gray-500 mt-1">Добавьте материал — ИИ создаст задания автоматически</p>
      </div>

      <div class="card">
        <form @submit.prevent="handleCreate" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Название урока</label>
            <input
              v-model="form.title"
              type="text"
              class="input-field"
              placeholder="Например: Фотосинтез у растений"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Язык</label>
            <select v-model="form.language" class="input-field">
              <option value="ru">Русский</option>
              <option value="en">English</option>
              <option value="uz">O'zbek</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Тип материала</label>
            <div class="flex gap-3">
              <label
                v-for="opt in sourceOptions"
                :key="opt.value"
                class="flex-1 border-2 rounded-lg p-3 cursor-pointer transition-colors"
                :class="form.source_type === opt.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <input
                  v-model="form.source_type"
                  type="radio"
                  :value="opt.value"
                  class="sr-only"
                />
                <div class="text-center">
                  <span class="text-2xl">{{ opt.icon }}</span>
                  <p class="text-sm font-medium mt-1">{{ opt.label }}</p>
                </div>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ form.source_type === 'text' ? 'Текст материала' : form.source_type === 'url' ? 'URL ссылка' : 'Вставьте текст из файла' }}
            </label>
            <textarea
              v-if="form.source_type === 'text' || form.source_type === 'file'"
              v-model="form.source_content"
              class="input-field"
              rows="10"
              placeholder="Вставьте или напишите учебный материал здесь..."
              required
            ></textarea>
            <input
              v-else
              v-model="form.source_content"
              type="url"
              class="input-field"
              placeholder="https://..."
              required
            />
          </div>

          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ error }}</div>

          <div class="flex gap-3">
            <button type="submit" class="btn-primary flex-1 py-3" :disabled="loading">
              {{ loading ? (analyzing ? 'Анализируем...' : 'Создаём...') : 'Создать урок' }}
            </button>
            <router-link to="/dashboard" class="btn-secondary py-3 px-6">Отмена</router-link>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'

const router = useRouter()
const lessonStore = useLessonStore()

const loading = ref(false)
const analyzing = ref(false)
const error = ref('')

const sourceOptions = [
  { value: 'text', label: 'Текст', icon: '📝' },
  { value: 'url', label: 'Ссылка', icon: '🔗' },
  { value: 'file', label: 'Файл', icon: '📄' },
]

const form = ref({
  title: '',
  language: 'ru',
  source_type: 'text',
  source_content: '',
})

async function handleCreate() {
  loading.value = true
  error.value = ''
  try {
    const lesson = await lessonStore.createLesson(form.value)
    analyzing.value = true
    await lessonStore.analyzeLesson(lesson.id)
    router.push(`/lessons/${lesson.id}`)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка создания урока'
  } finally {
    loading.value = false
    analyzing.value = false
  }
}
</script>
