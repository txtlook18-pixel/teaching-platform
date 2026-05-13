<template>
  <AppLayout>
    <div class="max-w-3xl mx-auto">
      <div class="mb-8">
        <router-link to="/dashboard" class="text-blue-600 hover:underline text-sm">
          {{ t('createLesson.back') }}
        </router-link>
        <h1 class="text-3xl font-bold mt-2">{{ t('createLesson.title') }}</h1>
        <p class="text-gray-500 mt-1">{{ t('createLesson.subtitle') }}</p>
      </div>

      <div class="card">
        <form @submit.prevent="handleCreate" class="space-y-6">

          <!-- Title -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ t('createLesson.titleLabel') }}
            </label>
            <input
              v-model="form.title"
              type="text"
              class="input-field"
              :placeholder="t('createLesson.titlePlaceholder')"
              required
            />
          </div>

          <!-- Sources section -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              {{ t('createLesson.sourcesLabel') }}
            </label>

            <!-- Added sources list -->
            <div v-if="sources.length" class="space-y-2 mb-4">
              <div
                v-for="(src, i) in sources"
                :key="src.id"
                class="border rounded-xl bg-white overflow-hidden transition-all"
                :class="[
                  sortDragOver === i && sortDragIndex !== i ? 'border-blue-400 shadow-sm' : 'border-gray-200',
                  sortDragIndex === i ? 'opacity-40' : '',
                ]"
                @dragover.prevent="sortDragOver = i"
                @dragleave="sortDragOver = null"
                @drop.prevent="onSortDrop(i)"
              >
                <!-- File row -->
                <div v-if="src.type === 'file'" class="flex items-center gap-3 px-4 py-3">
                  <span draggable="true" class="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing select-none shrink-0" @dragstart="onSortStart(i)" @dragend="onSortEnd">⠿</span>
                  <span class="text-lg shrink-0">{{ fileIcon(src.file.name) }}</span>
                  <span class="flex-1 truncate text-sm font-medium text-gray-700">{{ src.file.name }}</span>
                  <span class="text-xs text-gray-400 shrink-0">{{ formatSize(src.file.size) }}</span>
                  <span v-if="src.file.size > MAX_FILE_BYTES" class="text-xs text-red-500 shrink-0">{{ t('createLesson.oversize') }}</span>
                  <template v-if="'detectedLang' in src && src.detectedLang">
                    <span v-if="src.langSupported" class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium shrink-0">{{ src.detectedLang.toUpperCase() }}</span>
                    <span v-else class="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium shrink-0">⚠️ {{ t('createLesson.langUnsupported') }}</span>
                  </template>
                  <button type="button" class="ml-1 text-gray-300 hover:text-red-500 transition-colors text-lg leading-none shrink-0" @click="removeSource(i)">×</button>
                </div>

                <!-- URL row -->
                <div v-else-if="src.type === 'url'" class="flex items-center gap-3 px-4 py-3">
                  <span draggable="true" class="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing select-none shrink-0" @dragstart="onSortStart(i)" @dragend="onSortEnd">⠿</span>
                  <span class="shrink-0">🔗</span>
                  <template v-if="src.editing">
                    <input v-model="src.url" type="url" class="flex-1 text-sm border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400" @keydown.enter.prevent="src.editing = false" />
                    <button type="button" class="text-xs text-blue-600 font-semibold shrink-0 hover:text-blue-700" @click="src.editing = false">{{ t('createLesson.saveBtn') }}</button>
                  </template>
                  <template v-else>
                    <span
                      class="flex-1 truncate text-sm"
                      :class="isValidUrl(src.url) ? 'text-blue-600' : 'text-red-500 line-through'"
                    >{{ src.url }}</span>
                    <span v-if="!isValidUrl(src.url)" class="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full shrink-0 font-medium bg-red-50 text-red-500">Ошибка</span>
                    <span v-else class="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full shrink-0 font-medium" :class="urlTypeBadgeClass(src.url)">{{ urlTypeIcon(src.url) }} {{ t(`createLesson.urlType.${urlTypeKey(src.url)}`) }}</span>
                    <button type="button" class="text-gray-400 hover:text-gray-600 transition-colors shrink-0 text-base" @click="src.editing = true">✏️</button>
                  </template>
                  <button type="button" class="ml-1 text-gray-300 hover:text-red-500 transition-colors text-lg leading-none shrink-0" @click="removeSource(i)">×</button>
                </div>

                <!-- Text note row -->
                <div v-else class="px-4 py-3">
                  <div class="flex items-center gap-2 mb-2">
                    <span draggable="true" class="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing select-none shrink-0" @dragstart="onSortStart(i)" @dragend="onSortEnd">⠿</span>
                    <span class="shrink-0">📝</span>
                    <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">{{ t('createLesson.textNote') }} {{ textNoteIndex(i) }}</span>
                    <template v-if="'detectedLang' in src && src.detectedLang">
                      <span v-if="src.langSupported" class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">{{ src.detectedLang.toUpperCase() }}</span>
                      <span v-else class="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium">⚠️ {{ t('createLesson.langUnsupported') }}</span>
                    </template>
                    <div class="ml-auto flex items-center gap-2">
                      <button type="button" class="text-xs font-semibold transition-colors shrink-0" :class="src.editing ? 'text-blue-600 hover:text-blue-700' : 'text-gray-400 hover:text-gray-600'" @click="src.editing = !src.editing">{{ src.editing ? t('createLesson.saveBtn') : '✏️' }}</button>
                      <button type="button" class="text-gray-300 hover:text-red-500 transition-colors text-lg leading-none" @click="removeSource(i)">×</button>
                    </div>
                  </div>
                  <textarea v-if="src.editing" v-model="src.content" class="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-y" rows="5"></textarea>
                  <p v-else class="text-sm text-gray-700 line-clamp-3 whitespace-pre-line leading-relaxed">{{ src.content }}</p>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div
              v-else
              class="border-2 border-dashed border-gray-200 rounded-xl py-10 text-center text-gray-400 mb-4"
            >
              <div class="text-4xl mb-2">📚</div>
              <p class="text-sm">{{ t('createLesson.sourcesEmpty') }}</p>
            </div>

            <!-- Add source panel -->
            <div class="border border-gray-200 rounded-xl overflow-hidden">
              <div class="flex border-b border-gray-200 bg-gray-50">
                <button
                  v-for="tab in addTabs"
                  :key="tab.type"
                  type="button"
                  class="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-sm font-medium transition-colors"
                  :class="activeTab === tab.type
                    ? 'bg-white text-blue-600 border-b-2 border-blue-500'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'"
                  @click="switchTab(tab.type)"
                >
                  <span>{{ tab.icon }}</span>
                  {{ tab.label }}
                </button>
              </div>

              <!-- File tab -->
              <div v-if="activeTab === 'file'" class="p-4">
                <div
                  class="border-2 border-dashed rounded-xl py-8 text-center transition-colors cursor-pointer"
                  :class="isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-300 hover:bg-gray-50'"
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
                  <div class="text-3xl mb-2">📂</div>
                  <p class="text-gray-600 text-sm font-medium">{{ t('createLesson.dropzoneText') }}</p>
                  <p class="text-gray-400 text-xs mt-1">{{ t('createLesson.dropzoneHint') }}</p>
                </div>
              </div>

              <!-- URL tab -->
              <div v-else-if="activeTab === 'url'" class="p-4">
                <div class="flex gap-2">
                  <input
                    v-model="addInput"
                    type="url"
                    class="input-field flex-1"
                    placeholder="https://..."
                    @keydown.enter.prevent="addUrlSource"
                  />
                  <button
                    type="button"
                    class="btn-primary px-5 shrink-0"
                    :disabled="!addInput.trim()"
                    @click="addUrlSource"
                  >{{ t('createLesson.addBtn') }}</button>
                </div>
              </div>

              <!-- Text tab -->
              <div v-else class="p-4">
                <textarea
                  v-model="addInput"
                  class="input-field w-full mb-3"
                  rows="7"
                  :placeholder="t('createLesson.textPlaceholder')"
                ></textarea>
                <div class="flex justify-end">
                  <button
                    type="button"
                    class="btn-primary px-6"
                    :disabled="!addInput.trim()"
                    @click="addTextSource"
                  >{{ t('createLesson.addBtn') }}</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Error -->
          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ error }}</div>

          <!-- Actions row: language selector + submit + cancel -->
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2 mr-auto">
              <span class="text-sm text-gray-500 shrink-0">{{ t('createLesson.languageLabel') }}:</span>
              <span
                :class="`fi fi-${localeFlagCodes[form.language]}`"
                style="border-radius:2px;width:1.25em;height:0.95em;display:inline-block;background-size:cover;flex-shrink:0"
              ></span>
              <select
                v-model="form.language"
                class="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer"
              >
                <option value="ru">Русский</option>
                <option value="en">English</option>
                <option value="uz">O'zbek</option>
              </select>
            </div>
            <router-link to="/dashboard" class="btn-secondary py-3 px-6 shrink-0">
              {{ t('createLesson.cancel') }}
            </router-link>
            <button
              type="submit"
              class="btn-primary py-3 px-8 shrink-0"
              :disabled="loading || !canSubmit"
            >
              {{ submitLabel }}
            </button>
          </div>

        </form>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'
import { translateApiError } from '@/i18n'

const { t } = useI18n()
const router = useRouter()
const lessonStore = useLessonStore()

const MAX_FILE_BYTES = 20 * 1024 * 1024

const localeFlagCodes: Record<string, string> = { ru: 'ru', en: 'us', uz: 'uz' }

// ── Source types ──────────────────────────────────────────────────────────────
type LangInfo = { detectedLang?: string; langSupported?: boolean }
type FileSource = { id: string; type: 'file'; file: File } & LangInfo
type UrlSource  = { id: string; type: 'url';  url: string; editing: boolean }
type TextSource = { id: string; type: 'text'; content: string; editing: boolean } & LangInfo
type SourceItem = FileSource | UrlSource | TextSource

let _nextId = 1
const sources    = ref<SourceItem[]>([])
const activeTab  = ref<'file' | 'url' | 'text'>('file')
const addInput   = ref('')
const isDragging = ref(false)
const fileInput  = ref<HTMLInputElement | null>(null)

const loading      = ref(false)
const loadingStage = ref<'extract' | 'fetch' | 'create' | 'analyze' | ''>('')
const error        = ref('')

const sortDragIndex = ref<number | null>(null)
const sortDragOver  = ref<number | null>(null)
function onSortStart(i: number) { sortDragIndex.value = i }
function onSortEnd()            { sortDragIndex.value = null; sortDragOver.value = null }
function onSortDrop(i: number) {
  if (sortDragIndex.value !== null && sortDragIndex.value !== i) {
    const items = [...sources.value]
    const [moved] = items.splice(sortDragIndex.value, 1)
    items.splice(i, 0, moved)
    sources.value = items
  }
  sortDragIndex.value = null
  sortDragOver.value  = null
}

const form = ref({ title: '', language: 'ru' })

const addTabs = computed(() => [
  { type: 'file' as const, icon: '📄', label: t('createLesson.source.file') },
  { type: 'url'  as const, icon: '🔗', label: t('createLesson.source.url')  },
  { type: 'text' as const, icon: '📝', label: t('createLesson.source.text') },
])

const hasOversizedFile = computed(() =>
  sources.value.some((s) => s.type === 'file' && (s as FileSource).file.size > MAX_FILE_BYTES),
)
const canSubmit = computed(() => sources.value.length > 0 && !hasOversizedFile.value)

const submitLabel = computed(() => {
  if (!loading.value) return t('createLesson.submit')
  const map: Record<string, string> = {
    extract: t('createLesson.submitting.extract'),
    fetch:   t('createLesson.submitting.fetch'),
    create:  t('createLesson.submitting.create'),
    analyze: t('createLesson.submitting.analyze'),
  }
  return map[loadingStage.value] ?? t('createLesson.submitting.default')
})

// ── Source management ─────────────────────────────────────────────────────────
function switchTab(tab: 'file' | 'url' | 'text') {
  activeTab.value = tab
  addInput.value  = ''
}

function textNoteIndex(sourceIndex: number): number {
  return sources.value.slice(0, sourceIndex + 1).filter((s) => s.type === 'text').length
}

async function detectLang(index: number) {
  const src = sources.value[index]
  let text = ''
  if (src.type === 'text') {
    text = (src as TextSource).content
  } else if (src.type === 'file') {
    const ext = (src as FileSource).file.name.split('.').pop()?.toLowerCase()
    if (ext === 'txt' || ext === 'md') {
      text = await new Promise<string>(resolve => {
        const reader = new FileReader()
        reader.onload = e => resolve((e.target?.result as string) || '')
        reader.onerror = () => resolve('')
        reader.readAsText((src as FileSource).file)
      })
    }
  }
  if (!text.trim()) return
  try {
    const res = await apiClient.post('/lessons/detect-language', { text: text.slice(0, 3000) })
    sources.value[index] = { ...sources.value[index], detectedLang: res.data.language, langSupported: res.data.supported }
  } catch {}
}

function addUrlSource() {
  const url = addInput.value.trim()
  if (!url) return
  sources.value.push({ id: String(_nextId++), type: 'url', url, editing: false })
  addInput.value = ''
}

function addTextSource() {
  const content = addInput.value.trim()
  if (!content) return
  sources.value.push({ id: String(_nextId++), type: 'text', content, editing: false })
  addInput.value = ''
  detectLang(sources.value.length - 1)
}

function removeSource(index: number) {
  sources.value.splice(index, 1)
}

function addFiles(incoming: File[]) {
  const existing = new Set(
    sources.value
      .filter((s): s is FileSource => s.type === 'file')
      .map((s) => s.file.name + s.file.size),
  )
  for (const f of incoming) {
    if (!existing.has(f.name + f.size)) {
      sources.value.push({ id: String(_nextId++), type: 'file', file: f })
      detectLang(sources.value.length - 1)
    }
  }
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

// ── Formatting / helpers ──────────────────────────────────────────────────────
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function fileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase()
  return ({ pdf: '📕', docx: '📘', doc: '📘', md: '📋', txt: '📄' } as Record<string, string>)[ext ?? ''] ?? '📄'
}

function isValidUrl(url: string): boolean {
  try {
    const u = new URL(url)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

function urlTypeKey(url: string): 'video' | 'file' | 'page' {
  const u = url.toLowerCase()
  if (/youtube\.com|youtu\.be|vimeo\.com|rutube\.ru|tiktok\.com|twitch\.tv|reddit\.com/.test(u)) return 'video'
  if (/\.(pdf|docx?|xlsx?|pptx?|txt|md|csv|zip|rar)(\?.*)?$/.test(u)) return 'file'
  return 'page'
}
function urlTypeIcon(url: string): string {
  return { video: '🎬', file: '📄', page: '🌐' }[urlTypeKey(url)]
}
function urlTypeBadgeClass(url: string): string {
  return { video: 'bg-purple-50 text-purple-600', file: 'bg-orange-50 text-orange-600', page: 'bg-gray-100 text-gray-500' }[urlTypeKey(url)]
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function handleCreate() {
  loading.value = true
  error.value   = ''
  try {
    const fileSources = sources.value.filter((s): s is FileSource => s.type === 'file')
    const urlSources  = sources.value.filter((s): s is UrlSource  => s.type === 'url')
    const textSources = sources.value.filter((s): s is TextSource => s.type === 'text')

    // Extract files per-file to preserve individual content
    let fileTexts: string[] = []
    if (fileSources.length) {
      loadingStage.value = 'extract'
      const fd = new FormData()
      for (const s of fileSources) fd.append('files', s.file)
      const res = await apiClient.post<{ files: { filename: string; text: string }[] }>('/lessons/extract-text-per-file', fd)
      fileTexts = res.data.files.map((f) => f.text)
    }

    // Fetch URL content for multi-source lessons
    let urlTexts: (string | null)[] = urlSources.map(() => null)
    const isMultiSource = fileSources.length + textSources.length + urlSources.length > 1 || urlSources.length > 1
    if (urlSources.length > 0 && isMultiSource) {
      loadingStage.value = 'fetch'
      urlTexts = await Promise.all(
        urlSources.map(async (s) => {
          try {
            const res = await apiClient.post<{ text: string }>('/lessons/fetch-url-text', { url: s.url })
            return res.data.text || null
          } catch {
            return null
          }
        })
      )
    }

    // Assemble source_content: files first, then texts, then URLs
    const parts: string[] = []
    for (const t of fileTexts) if (t) parts.push(t)
    for (const s of textSources) parts.push(s.content)

    let sourceType: string
    let sourceContent: string

    if (urlSources.length === 1 && fileSources.length === 0 && textSources.length === 0) {
      sourceType    = 'url'
      sourceContent = urlSources[0].url
    } else {
      for (const t of urlTexts) if (t) parts.push(t)
      sourceType    = 'text'
      sourceContent = parts.join('\n\n---\n\n')
    }

    loadingStage.value = 'create'
    let fileIdx = 0
    let urlIdx = 0
    const sourcesMetadata = sources.value.map((s) => {
      if (s.type === 'file') {
        const content = fileTexts[fileIdx++] ?? null
        return { name: (s as FileSource).file.name, type: 'file' as const, size: (s as FileSource).file.size, content }
      }
      if (s.type === 'url') {
        const content = urlTexts[urlIdx++] ?? null
        return { name: (s as UrlSource).url, type: 'url' as const, content }
      }
      const content = (s as TextSource).content
      return { name: `Текст ${textNoteIndex(sources.value.indexOf(s))}`, type: 'text' as const, content }
    })
    const lesson = await lessonStore.createLesson({
      title:            form.value.title,
      language:         form.value.language,
      source_type:      sourceType,
      source_content:   sourceContent,
      sources_metadata: sourcesMetadata,
    })

    if (sourceType === 'url') {
      loadingStage.value = 'fetch'
      await apiClient.post(`/lessons/${lesson.id}/fetch-url`)
    }

    loadingStage.value = 'analyze'
    await lessonStore.analyzeLesson(lesson.id)

    router.push(`/lessons/${lesson.id}`)
  } catch (e: any) {
    error.value = translateApiError(e.response?.data?.detail, t('createLesson.defaultError'))
  } finally {
    loading.value      = false
    loadingStage.value = ''
  }
}
</script>
