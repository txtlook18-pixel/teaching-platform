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
                  @change="onSourceTypeChange"
                />
                <div class="text-center">
                  <span class="text-2xl">{{ opt.icon }}</span>
                  <p class="text-sm font-medium mt-1">{{ opt.label }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Text / URL -->
          <div v-if="form.source_type !== 'file'">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ form.source_type === 'text' ? 'Текст материала' : 'URL ссылка' }}
            </label>
            <textarea
              v-if="form.source_type === 'text'"
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

          <!-- File upload zone -->
          <div v-else>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Файлы <span class="text-gray-400 font-normal">(TXT, MD, PDF, DOCX · до 20 МБ каждый)</span>
            </label>

            <div
              class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
              :class="isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'"
              @dragenter.prevent="isDragging = true"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="onDrop"
              @click="fileInput?.click()"
            >
              <input
                ref="fileInput"
                type="file"
                multiple
                accept=".txt,.md,.pdf,.docx"
                class="sr-only"
                @change="onFileChange"
              />
              <div class="text-4xl mb-2">📂</div>
              <p class="text-gray-600 font-medium">Нажмите или перетащите файлы сюда</p>
              <p class="text-gray-400 text-sm mt-1">TXT, MD, PDF, DOCX · до 20 МБ каждый</p>
            </div>

            <!-- File list -->
            <ul v-if="selectedFiles.length" class="mt-3 space-y-2">
              <li
                v-for="(f, i) in selectedFiles"
                :key="i"
                class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-sm"
              >
                <div class="flex items-center gap-2 min-w-0">
                  <span>{{ fileIcon(f.name) }}</span>
                  <span class="truncate text-gray-700 font-medium">{{ f.name }}</span>
                  <span class="text-gray-400 shrink-0">{{ formatSize(f.size) }}</span>
                  <span v-if="f.size > MAX_FILE_BYTES" class="text-red-500 text-xs shrink-0">превышает 20 МБ</span>
                </div>
                <button
                  type="button"
                  class="ml-2 text-gray-400 hover:text-red-500 transition-colors shrink-0"
                  @click.stop="removeFile(i)"
                >✕</button>
              </li>
            </ul>

            <p v-if="!selectedFiles.length" class="text-sm text-gray-400 mt-2">
              Файлы не выбраны
            </p>
          </div>

          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ error }}</div>

          <div class="flex gap-3">
            <button
              type="submit"
              class="btn-primary flex-1 py-3"
              :disabled="loading || !canSubmit"
            >
              {{ submitLabel }}
            </button>
            <router-link to="/dashboard" class="btn-secondary py-3 px-6">Отмена</router-link>
          </div>
        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'

const router = useRouter()
const lessonStore = useLessonStore()

const MAX_FILE_BYTES = 20 * 1024 * 1024

const loading = ref(false)
const loadingStage = ref<'extract' | 'fetch' | 'create' | 'analyze' | ''>('')
const error = ref('')
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<File[]>([])

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

const hasOversizedFile = computed(() => selectedFiles.value.some((f) => f.size > MAX_FILE_BYTES))

const canSubmit = computed(() => {
  if (form.value.source_type === 'file') return selectedFiles.value.length > 0 && !hasOversizedFile.value
  return true
})

const submitLabel = computed(() => {
  if (!loading.value) return 'Создать урок'
  if (loadingStage.value === 'extract') return 'Извлекаем текст...'
  if (loadingStage.value === 'fetch') return 'Загружаем страницу...'
  if (loadingStage.value === 'create') return 'Создаём урок...'
  if (loadingStage.value === 'analyze') return 'Анализируем...'
  return 'Загружаем...'
})

function onSourceTypeChange() {
  form.value.source_content = ''
  selectedFiles.value = []
  error.value = ''
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  addFiles(Array.from(input.files ?? []))
  input.value = ''
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  addFiles(Array.from(e.dataTransfer?.files ?? []))
}

function addFiles(incoming: File[]) {
  const existing = new Set(selectedFiles.value.map((f) => f.name + f.size))
  for (const f of incoming) {
    if (!existing.has(f.name + f.size)) selectedFiles.value.push(f)
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`
}

function fileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase()
  return { pdf: '📕', docx: '📘', doc: '📘', md: '📋', txt: '📄' }[ext ?? ''] ?? '📄'
}

async function handleCreate() {
  loading.value = true
  error.value = ''
  try {
    if (form.value.source_type === 'file') {
      loadingStage.value = 'extract'
      const fd = new FormData()
      for (const f of selectedFiles.value) fd.append('files', f)
      const res = await apiClient.post<{ text: string; file_count: number }>('/lessons/extract-text', fd)
      form.value.source_content = res.data.text
    }

    loadingStage.value = 'create'
    const lesson = await lessonStore.createLesson(form.value)

    if (form.value.source_type === 'url') {
      loadingStage.value = 'fetch'
      await apiClient.post(`/lessons/${lesson.id}/fetch-url`)
    }

    loadingStage.value = 'analyze'
    await lessonStore.analyzeLesson(lesson.id)

    router.push(`/lessons/${lesson.id}`)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка создания урока'
  } finally {
    loading.value = false
    loadingStage.value = ''
  }
}
</script>
