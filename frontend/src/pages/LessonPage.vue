<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="lesson">
      <!-- Back -->
      <router-link
        to="/dashboard"
        class="inline-flex items-center text-sm text-gray-500 hover:text-blue-600 transition-colors mb-4"
      >
        {{ t('lesson.backToLessons') }}
      </router-link>

      <!-- Header -->
      <div class="flex justify-between items-start mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">{{ lesson.title }}</h1>
          <p v-if="lesson.cluster_data" class="text-gray-500 mt-1">
            {{ lesson.cluster_data.main_topic }}
          </p>
        </div>
        <div class="flex items-center gap-3 shrink-0 ml-4">
          <span class="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
            {{ lesson.language.toUpperCase() }}
          </span>
          <router-link
            to="/dashboard"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors"
          >
            <svg class="w-4 h-4" viewBox="0 0 16 16" fill="none">
              <path d="M3 8l3.5 3.5L13 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ t('lesson.finishLesson') }}
          </router-link>
        </div>
      </div>

      <!-- Two-column layout -->
      <div class="flex gap-6 items-start">

        <!-- Left: tabs + content -->
        <div class="flex-1 min-w-0">

          <!-- Tab navigation -->
          <div class="border-b border-gray-200 mb-6">
            <nav class="flex">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                class="flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors whitespace-nowrap"
                :class="!isAnalyzed
                  ? 'border-transparent text-gray-300 cursor-not-allowed'
                  : activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                :disabled="!isAnalyzed"
                @click="switchTab(tab.key)"
              >
                {{ tab.icon }} {{ tab.label }}
              </button>
            </nav>
          </div>

          <!-- Not analyzed warning -->
          <div v-if="!isAnalyzed" class="card py-12 flex flex-col items-center text-center gap-5">
            <div class="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center">
              <svg class="w-7 h-7 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800 text-lg mb-2">{{ t('lesson.notAnalyzedError.title') }}</h3>
              <p class="text-sm text-gray-500 max-w-sm mx-auto leading-relaxed">{{ t('lesson.notAnalyzedError.description') }}</p>
            </div>
            <router-link
              to="/lessons/create"
              class="px-5 py-2.5 border border-gray-300 text-gray-700 text-sm font-semibold rounded-xl hover:bg-gray-50 transition-colors"
            >
              {{ t('lesson.notAnalyzedError.createNew') }}
            </router-link>
          </div>

          <template v-else>

          <!-- Tab: Материалы -->
          <div v-if="activeTab === 'materials'">

            <!-- Карточка анализа -->
            <div v-if="lesson.cluster_data" class="card mb-4">
              <h2 class="font-semibold text-gray-700 mb-4">{{ t('lesson.analysis.title') }}</h2>
              <div class="grid grid-cols-2 gap-6">
                <div>
                  <p class="text-xs text-gray-400 mb-2">{{ t('lesson.analysis.subtopics') }}</p>
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="sub in lesson.cluster_data.subtopics"
                      :key="sub"
                      class="text-xs bg-purple-100 text-purple-700 px-2.5 py-0.5 rounded-full"
                    >{{ sub }}</span>
                  </div>
                </div>
                <div>
                  <p class="text-xs text-gray-400 mb-2">{{ t('lesson.analysis.concepts') }}</p>
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="k in lesson.cluster_data.key_concepts"
                      :key="k"
                      class="text-xs bg-green-100 text-green-700 px-2.5 py-0.5 rounded-full"
                    >{{ k }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="card mb-4 text-center py-12">
              <p class="text-gray-400 text-sm">{{ t('lesson.noAnalysis') }}</p>
            </div>

            <!-- Per-source summary cards -->
            <template
              v-for="src in (lesson.sources_metadata ?? []).filter(s => !s.fetch_error)"
              :key="src.name"
            >
              <div class="card mb-4">
                <div
                  class="flex items-center gap-2 pb-3 border-b border-gray-100 cursor-pointer select-none"
                  :class="collapsedSources.has(src.name) ? '' : 'mb-4'"
                  @click="toggleCollapse(src.name)"
                >
                  <span class="text-lg shrink-0">{{ sourceIcon(src) }}</span>
                  <span
                    class="font-semibold text-gray-800 truncate text-sm flex-1"
                    :title="src.name"
                  >{{ sourceDisplayName(src) }}</span>
                  <svg
                    class="w-4 h-4 text-gray-400 shrink-0 transition-transform duration-200"
                    :class="collapsedSources.has(src.name) ? '-rotate-90' : ''"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </div>

                <template v-if="!collapsedSources.has(src.name)">
                <!-- Video source: no summary available -->
                <div v-if="isVideoUrl(src.name)" class="flex flex-col items-center gap-2 py-6 text-amber-500">
                  <span class="text-2xl">🎬</span>
                  <p class="text-sm font-medium">Видео-источник</p>
                  <p class="text-xs text-gray-400">Конспект для видео не поддерживается</p>
                </div>

                <template v-else-if="sourceSummaries[src.name]">
                  <template v-for="(block, i) in parseRetellingBlocks(sourceSummaries[src.name])" :key="i">
                    <h3
                      v-if="block.type === 'heading'"
                      class="font-semibold text-gray-800 text-sm uppercase tracking-wide mt-5 mb-2"
                      :class="{ 'mt-0': i === 0 }"
                    >{{ block.content }}</h3>
                    <ul v-else-if="block.type === 'list'" class="space-y-1.5 mb-3">
                      <li
                        v-for="(item, j) in block.items"
                        :key="j"
                        class="flex items-start gap-2 text-sm text-gray-700 leading-relaxed"
                      >
                        <span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0"></span>
                        <span v-html="formatInline(item)"></span>
                      </li>
                    </ul>
                    <p
                      v-else
                      class="text-sm text-gray-700 leading-relaxed mb-2"
                      v-html="formatInline(block.content)"
                    ></p>
                  </template>
                </template>

                <div v-else class="flex flex-col items-center gap-2 py-8 text-gray-400">
                  <template v-if="loadingSourceSummaries[src.name]">
                    <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    <p class="text-sm">{{ t('lesson.summary.generating') }}</p>
                  </template>
                  <template v-else>
                    <p class="text-sm italic mb-3">{{ t('lesson.summary.noReport') }}</p>
                    <button
                      class="px-4 py-1.5 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
                      @click.stop="generateOneSummary(src.name)"
                    >
                      Сгенерировать конспект
                    </button>
                  </template>
                </div>
                </template>
              </div>
            </template>

          </div>

          <!-- Tab: Задание (battle, analysis, cards) -->
          <div v-else-if="activeTab === 'assignment'" class="card">
            <h2 class="font-semibold text-gray-800 mb-4 text-lg">{{ t('lesson.createAssignment') }}</h2>
            <div class="grid grid-cols-3 gap-3 mb-6">
              <button
                v-for="atype in assignmentTypeOptions"
                :key="atype.value"
                class="border-2 rounded-xl p-4 text-center transition-all hover:border-blue-400 hover:bg-blue-50"
                :class="selectedType === atype.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'"
                @click="selectedType = atype.value"
              >
                <span class="text-3xl">{{ atype.icon }}</span>
                <p class="text-sm font-medium mt-2">{{ atype.label }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ atype.desc }}</p>
              </button>
            </div>

            <!-- Cards form -->
            <div v-if="selectedType === 'cards'" class="flex gap-4 items-end">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.cards.countLabel') }}</label>
                <input v-model.number="questionCount" type="number" min="3" max="30" class="input-field w-24" />
              </div>
              <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
                {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
              </button>
            </div>

            <!-- Analysis form -->
            <div v-else-if="selectedType === 'analysis'">
              <div v-if="allTopicsUsed && !extraTopics.length" class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4 text-center">
                <p class="text-sm text-amber-800 font-medium mb-3">{{ t('lesson.analysisMode.allUsed') }}</p>
                <button
                  class="px-5 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 text-sm font-medium transition-colors disabled:opacity-60"
                  :disabled="loadingExtraTopics"
                  @click="loadExtraTopics"
                >
                  <span v-if="loadingExtraTopics" class="inline-flex items-center gap-2">
                    <span class="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full inline-block"></span>
                    {{ t('lesson.analysisMode.generating') }}
                  </span>
                  <span v-else>{{ t('lesson.analysisMode.getNew') }}</span>
                </button>
              </div>
              <div class="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
                <p class="text-sm font-medium text-gray-600 mb-3">
                  {{ extraTopics.length ? t('lesson.analysisMode.newTopics') : t('lesson.analysisMode.selectTopic') }}
                </p>
                <div v-if="availableAnalysisTopics.length" class="space-y-2">
                  <button
                    v-for="(sub, i) in availableAnalysisTopics"
                    :key="sub"
                    type="button"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 text-left transition-all"
                    :class="!extraTopics.length && usedAnalysisTopics.has(sub)
                      ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
                      : selectedAnalysisTopic === sub
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
                    :disabled="!extraTopics.length && usedAnalysisTopics.has(sub)"
                    @click="(!extraTopics.length && usedAnalysisTopics.has(sub)) || (selectedAnalysisTopic = sub)"
                  >
                    <span
                      class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors"
                      :class="!extraTopics.length && usedAnalysisTopics.has(sub)
                        ? 'bg-gray-200 text-gray-400'
                        : selectedAnalysisTopic === sub ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'"
                    >{{ i + 1 }}</span>
                    <span class="text-sm" :class="!extraTopics.length && usedAnalysisTopics.has(sub) ? 'text-gray-400 line-through' : 'text-gray-800'">{{ sub }}</span>
                    <span v-if="!extraTopics.length && usedAnalysisTopics.has(sub)" class="ml-auto text-xs text-gray-400">{{ t('lesson.analysisMode.used') }}</span>
                    <span v-else-if="selectedAnalysisTopic === sub" class="ml-auto text-blue-500 text-base">✓</span>
                  </button>
                </div>
                <p v-else class="text-sm text-gray-400">{{ t('lesson.analysisMode.noTopics') }}</p>
              </div>
              <button
                class="btn-primary px-8 py-2"
                :disabled="creating || !selectedAnalysisTopic"
                @click="handleCreateAssignment"
              >
                {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
              </button>
            </div>

            <!-- Battle form -->
            <div v-else-if="selectedType === 'battle'" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('lesson.battle.timerLabel') }}</label>
                <div class="flex gap-2 flex-wrap">
                  <button
                    v-for="opt in battleTimerOptions"
                    :key="opt.value"
                    type="button"
                    class="px-5 py-2 rounded-lg border-2 text-sm font-medium transition-all"
                    :class="battleTimer === opt.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-blue-300 text-gray-700'"
                    @click="battleTimer = opt.value"
                  >{{ opt.label }}</button>
                </div>
              </div>
              <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
                {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
              </button>
            </div>

            <div v-if="createError" class="mt-4 bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ createError }}</div>
          </div>

          <!-- Tab: Тест -->
          <div v-else-if="activeTab === 'test'" class="card">
            <h2 class="font-semibold text-gray-800 mb-4 text-lg">{{ t('lesson.createAssignment') }}</h2>
            <div class="space-y-5">
              <div class="flex gap-4 items-end flex-wrap">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.test.questionCount') }}</label>
                  <input v-model.number="questionCount" type="number" min="3" max="20" class="input-field w-24" />
                </div>
                <div v-if="testMode === 'group'">
                  <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.test.timer') }}</label>
                  <select v-model.number="timerSeconds" class="input-field w-28">
                    <option :value="30">{{ t('lesson.test.t30') }}</option>
                    <option :value="60">{{ t('lesson.test.t60') }}</option>
                    <option :value="90">{{ t('lesson.test.t90') }}</option>
                    <option :value="120">{{ t('lesson.test.t120') }}</option>
                    <option :value="0">{{ t('lesson.test.noTimer') }}</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">{{ t('lesson.test.mode') }}</label>
                <div class="grid grid-cols-2 gap-3 max-w-md">
                  <button
                    type="button"
                    class="border-2 rounded-xl p-4 text-left transition-all"
                    :class="testMode === 'group' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
                    @click="testMode = 'group'"
                  >
                    <span class="text-2xl">🖥️</span>
                    <p class="font-medium text-sm mt-2 text-gray-900">{{ t('lesson.test.screen') }}</p>
                    <p class="text-xs text-gray-400 mt-0.5">{{ t('lesson.test.screenDesc') }}</p>
                  </button>
                  <button
                    type="button"
                    class="border-2 rounded-xl p-4 text-left transition-all"
                    :class="testMode === 'individual' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'"
                    @click="testMode = 'individual'"
                  >
                    <span class="text-2xl">📱</span>
                    <p class="font-medium text-sm mt-2 text-gray-900">{{ t('lesson.test.phone') }}</p>
                    <p class="text-xs text-gray-400 mt-0.5">{{ t('lesson.test.phoneDesc') }}</p>
                  </button>
                </div>
              </div>
              <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
                {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
              </button>
            </div>
            <div v-if="createError" class="mt-4 bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ createError }}</div>
          </div>

          <!-- Tab: Спросить у ИИ -->
          <div v-else-if="activeTab === 'chat'" class="card">
            <h2 class="font-semibold text-gray-800 mb-4 text-lg">{{ t('lesson.createAssignment') }}</h2>
            <div class="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
              <p class="text-sm font-medium text-gray-600 mb-3">{{ t('lesson.retelling.topics') }}</p>
              <ul v-if="lesson?.cluster_data?.subtopics?.length" class="space-y-2">
                <li
                  v-for="(sub, i) in lesson.cluster_data.subtopics"
                  :key="i"
                  class="flex items-center gap-2 text-sm text-gray-700"
                >
                  <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs flex items-center justify-center font-medium flex-shrink-0">{{ i + 1 }}</span>
                  {{ sub }}
                </li>
              </ul>
              <p v-else class="text-sm text-gray-400">{{ t('lesson.retelling.noTopics') }}</p>
            </div>
            <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
              {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
            </button>
            <div v-if="createError" class="mt-4 bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ createError }}</div>
          </div>

          </template>

        </div>

        <!-- Right sidebar (always visible) -->
        <aside class="w-72 shrink-0 sticky top-24">
          <div class="card">
            <h2 class="font-semibold text-gray-800 mb-3">{{ t('lesson.sidebar.title') }}</h2>
            <div class="relative mb-3">
              <svg
                class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M21 21l-4.35-4.35M17 11A6 6 0 111 11a6 6 0 0116 0z"/>
              </svg>
              <input
                v-model="sidebarSearch"
                type="text"
                :placeholder="t('lesson.sidebar.search')"
                class="input-field pl-9 text-sm"
              />
            </div>
            <p
              v-if="activeTab !== 'materials' && filteredSources.some(s => !s.fetch_error && !isVideoUrl(s.name)) && selectedSources.size === 0"
              class="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-2"
            >
              Отметьте материалы для генерации
            </p>
            <div class="space-y-0.5 max-h-[480px] overflow-y-auto">
              <label
                v-for="src in filteredSources"
                :key="src.name"
                class="flex items-center gap-3 px-2 py-2 rounded-lg transition-colors select-none"
                :class="src.fetch_error || isVideoUrl(src.name)
                  ? 'opacity-60 cursor-not-allowed'
                  : activeTab !== 'materials'
                    ? 'hover:bg-gray-50 cursor-pointer ' + (selectedSources.has(src.name) ? '' : 'opacity-50')
                    : ''"
              >
                <span class="text-base shrink-0" :class="src.fetch_error ? 'grayscale' : ''">{{ sourceIcon(src) }}</span>
                <span
                  class="flex-1 truncate text-sm shrink min-w-0"
                  :class="src.fetch_error ? 'text-red-500 line-through' : 'text-gray-700'"
                  :title="src.name"
                >{{ src.name }}</span>
                <template v-if="src.fetch_error">
                  <span class="text-xs bg-red-50 text-red-500 px-2 py-0.5 rounded-full font-medium shrink-0 whitespace-nowrap">Ошибка</span>
                </template>
                <template v-else-if="isVideoUrl(src.name)">
                  <span class="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium shrink-0 whitespace-nowrap">Не поддерживается</span>
                </template>
                <template v-else-if="sourceLangs[src.name]">
                  <span
                    v-if="sourceLangs[src.name].supported"
                    class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium shrink-0"
                  >{{ sourceLangs[src.name].lang.toUpperCase() }}</span>
                  <span
                    v-else
                    class="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium shrink-0"
                  >⚠️</span>
                </template>
                <input
                  v-if="activeTab !== 'materials' && !isVideoUrl(src.name)"
                  type="checkbox"
                  :checked="selectedSources.has(src.name)"
                  :disabled="src.fetch_error || togglingSource.has(src.name)"
                  class="w-4 h-4 rounded accent-blue-500 shrink-0"
                  :class="togglingSource.has(src.name) ? 'opacity-50 cursor-wait' : 'cursor-pointer'"
                  @change="toggleSource(src.name)"
                />
              </label>
              <p v-if="!filteredSources.length" class="text-sm text-gray-400 text-center py-6">
                {{ t('lesson.sidebar.noMaterials') }}
              </p>
            </div>
          </div>
        </aside>

      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useLessonStore } from '@/stores/lesson'
import { apiClient } from '@/services/api'
import { translateApiError } from '@/i18n'
import type { Lesson, SourceMeta } from '@/types'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const lessonStore = useLessonStore()

const loading = ref(true)
const lesson = ref<Lesson | null>(null)
const sourceSummaries = ref<Record<string, string>>({})
const loadingSourceSummaries = ref<Record<string, boolean>>({})
const selectedSources = ref<Set<string>>(new Set())
const sourceLangs = ref<Record<string, { lang: string; supported: boolean }>>({})
const reanalyzing = ref(false)
const reanalyzeError = ref('')
const togglingSource = ref<Set<string>>(new Set())
const collapsedSources = ref<Set<string>>(new Set())
function toggleCollapse(name: string) {
  const next = new Set(collapsedSources.value)
  if (next.has(name)) next.delete(name)
  else next.add(name)
  collapsedSources.value = next
}

const isAnalyzed = computed(() => !!lesson.value?.cluster_data)

async function reanalyze() {
  if (!lesson.value) return
  reanalyzing.value = true
  reanalyzeError.value = ''
  try {
    const res = await apiClient.post<typeof lesson.value>(`/lessons/${lesson.value.id}/analyze`)
    lesson.value = res.data
  } catch (e: any) {
    reanalyzeError.value = translateApiError(e.response?.data?.detail, t('lesson.notAnalyzedError.retryError'))
  } finally {
    reanalyzing.value = false
  }
}

async function detectSourceLangs() {
  const sources = lesson.value?.sources_metadata ?? []
  const lessonLang = lesson.value?.language ?? ''
  const supported = ['ru', 'en', 'uz']
  for (const src of sources) {
    if (src.content) {
      try {
        const res = await apiClient.post('/lessons/detect-language', { text: src.content.slice(0, 3000) })
        sourceLangs.value[src.name] = { lang: res.data.language, supported: res.data.supported }
      } catch {}
    } else if (lessonLang) {
      sourceLangs.value[src.name] = { lang: lessonLang, supported: supported.includes(lessonLang) }
    }
  }
}

type TabKey = 'materials' | 'assignment' | 'test' | 'chat'
const activeTab = ref<TabKey>('materials')
const sidebarSearch = ref('')

const selectedType = ref('')
const questionCount = ref(10)
const timerSeconds = ref(60)
const testMode = ref<'group' | 'individual'>('group')
const selectedAnalysisTopic = ref('')
const usedAnalysisTopics = ref<Set<string>>(new Set())
const extraTopics = ref<string[]>([])
const loadingExtraTopics = ref(false)
const battleTimer = ref(300)
const creating = ref(false)
const createError = ref('')

const tabs = computed(() => [
  { key: 'materials' as TabKey, icon: '📋', label: t('lesson.tabs.materials') },
  { key: 'assignment' as TabKey, icon: '📝', label: t('lesson.tabs.assignment') },
  { key: 'test'       as TabKey, icon: '🎯', label: t('lesson.tabs.test') },
  { key: 'chat'       as TabKey, icon: '💬', label: t('lesson.tabs.chat') },
])

const assignmentTypeOptions = computed(() => [
  { value: 'battle',   icon: '⚔️', label: t('lesson.types.battle.label'),   desc: t('lesson.types.battle.desc') },
  { value: 'analysis', icon: '🔍', label: t('lesson.types.analysis.label'), desc: t('lesson.types.analysis.desc') },
  { value: 'cards',    icon: '🎴', label: t('lesson.types.cards.label'),    desc: t('lesson.types.cards.desc') },
])

const battleTimerOptions = computed(() => [
  { value: 180, label: t('lesson.battle.m3') },
  { value: 300, label: t('lesson.battle.m5') },
  { value: 420, label: t('lesson.battle.m7') },
  { value: 600, label: t('lesson.battle.m10') },
])

const availableAnalysisTopics = computed<string[]>(() => {
  if (extraTopics.value.length) return extraTopics.value
  return lesson.value?.cluster_data?.subtopics ?? []
})

const allTopicsUsed = computed(() => {
  const topics = lesson.value?.cluster_data?.subtopics ?? []
  return topics.length > 0 && topics.every(s => usedAnalysisTopics.value.has(s))
})

type RetellingBlock =
  | { type: 'heading'; content: string }
  | { type: 'paragraph'; content: string }
  | { type: 'list'; content: ''; items: string[] }

function parseRetellingBlocks(text: string): RetellingBlock[] {
  if (!text) return []
  const lines = text.split('\n')
  const result: RetellingBlock[] = []
  let currentList: string[] | null = null

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      if (currentList) { result.push({ type: 'list', content: '', items: currentList }); currentList = null }
      continue
    }
    if (trimmed.startsWith('## ')) {
      if (currentList) { result.push({ type: 'list', content: '', items: currentList }); currentList = null }
      result.push({ type: 'heading', content: trimmed.slice(3) })
    } else if (trimmed.startsWith('- ')) {
      if (!currentList) currentList = []
      currentList.push(trimmed.slice(2))
    } else {
      if (currentList) { result.push({ type: 'list', content: '', items: currentList }); currentList = null }
      result.push({ type: 'paragraph', content: trimmed })
    }
  }
  if (currentList) result.push({ type: 'list', content: '', items: currentList })
  return result
}

function formatInline(text: string): string {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

function sourcesWord(count: number): string {
  if (locale.value === 'uz') return 'manba'
  if (locale.value === 'en') return count === 1 ? 'source' : 'sources'
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return 'источник'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'источника'
  return 'источников'
}

function formatDate(dt: string): string {
  return new Date(dt).toLocaleDateString(locale.value || 'ru', { day: 'numeric', month: 'long', year: 'numeric' })
}

async function generateOneSummary(srcName: string) {
  if (!lesson.value) return
  loadingSourceSummaries.value[srcName] = true
  try {
    const res = await apiClient.post(`/lessons/${lesson.value.id}/generate-summary`, {
      source_names: [srcName],
    })
    sourceSummaries.value[srcName] = res.data.summary
  } catch (e: any) {
    if (e.response?.data?.detail === 'error.video_no_summary') {
      sourceSummaries.value[srcName] = '📹 Конспект для видео-источников недоступен — текстовое содержимое отсутствует.'
    }
    // other errors: leave unset so the "Сгенерировать конспект" button stays visible
  } finally {
    loadingSourceSummaries.value[srcName] = false
  }
}

async function generateSourceSummaries() {
  if (!lesson.value) return
  const sources = (lesson.value.sources_metadata ?? []).filter(s => !s.fetch_error && !isVideoUrl(s.name))
  await Promise.all(sources.map(src => generateOneSummary(src.name)))
}

const filteredSources = computed<SourceMeta[]>(() => {
  const sources = lesson.value?.sources_metadata ?? []
  if (!sidebarSearch.value.trim()) return sources
  const q = sidebarSearch.value.toLowerCase()
  return sources.filter(s => s.name.toLowerCase().includes(q))
})

async function loadSourceStates() {
  if (!lesson.value) return
  try {
    const res = await apiClient.get<{ name: string; enabled: boolean }[]>(
      `/lessons/${lesson.value.id}/sources`
    )
    const next = new Set<string>()
    for (const s of res.data) {
      if (s.enabled) next.add(s.name)
    }
    selectedSources.value = next
  } catch {
    selectedSources.value = new Set()
  }
}

async function toggleSource(name: string) {
  if (togglingSource.value.has(name)) return
  // optimistic update
  const next = new Set(selectedSources.value)
  if (next.has(name)) next.delete(name)
  else next.add(name)
  selectedSources.value = next

  const toggling = new Set(togglingSource.value)
  toggling.add(name)
  togglingSource.value = toggling
  try {
    await apiClient.patch(`/lessons/${lesson.value!.id}/sources/toggle`, { source_name: name })
  } catch {
    // rollback
    const rollback = new Set(selectedSources.value)
    if (rollback.has(name)) rollback.delete(name)
    else rollback.add(name)
    selectedSources.value = rollback
  } finally {
    const done = new Set(togglingSource.value)
    done.delete(name)
    togglingSource.value = done
  }
}

function sourceDisplayName(src: SourceMeta): string {
  if (src.type === 'url') {
    try { return new URL(src.name).hostname } catch { return src.name }
  }
  return src.name
}

const VIDEO_HOSTS = /youtube\.com|youtu\.be|vimeo\.com|rutube\.ru|tiktok\.com|twitch\.tv/i
function isVideoUrl(name: string): boolean {
  return VIDEO_HOSTS.test(name)
}

function sourceIcon(src: SourceMeta): string {
  if (src.type === 'url' && isVideoUrl(src.name)) return '🎬'
  if (src.type === 'url')  return '🔗'
  if (src.type === 'text') return '📝'
  const ext = src.name.split('.').pop()?.toLowerCase()
  const map: Record<string, string> = {
    pdf: '📕', docx: '📘', doc: '📘', md: '📋', txt: '📄',
    pptx: '📊', ppt: '📊', xlsx: '📗', xls: '📗',
  }
  return map[ext ?? ''] ?? '📄'
}

function switchTab(tab: TabKey) {
  activeTab.value = tab
  createError.value = ''
  if (tab === 'test') {
    selectedType.value = 'test'
  } else if (tab === 'chat') {
    selectedType.value = 'retelling'
  } else {
    selectedType.value = ''
  }
}

watch(selectedType, async (type) => {
  selectedAnalysisTopic.value = ''
  extraTopics.value = []
  if (type === 'analysis' && lesson.value) {
    try {
      const res = await apiClient.get(`/assignments/lessons/${lesson.value.id}/assignments`)
      const used = new Set<string>()
      for (const a of res.data) {
        if (a.assignment_type === 'analysis') {
          const topic = a.questions_data?.topic || a.settings_data?.topic
          if (topic) used.add(topic)
        }
      }
      usedAnalysisTopics.value = used
    } catch {
      usedAnalysisTopics.value = new Set()
    }
  }
})

onMounted(async () => {
  try {
    lesson.value = await lessonStore.fetchLesson(route.params.id as string)
    await loadSourceStates()
  } finally {
    loading.value = false
  }
  detectSourceLangs()
  const validSources = (lesson.value?.sources_metadata ?? []).filter(s => !s.fetch_error)
  if (validSources.length) {
    collapsedSources.value = new Set(validSources.map(s => s.name))
    generateSourceSummaries()
  }
})

async function loadExtraTopics() {
  if (!lesson.value) return
  loadingExtraTopics.value = true
  selectedAnalysisTopic.value = ''
  try {
    const allUsed = [...usedAnalysisTopics.value]
    const res = await apiClient.post(`/lessons/${lesson.value.id}/topics/more`, {
      exclude: allUsed,
      count: 5,
    })
    extraTopics.value = res.data.topics
  } catch {
    extraTopics.value = []
  } finally {
    loadingExtraTopics.value = false
  }
}

async function handleCreateAssignment() {
  if (!selectedType.value || !lesson.value) return
  const hasSourceList = (lesson.value.sources_metadata ?? []).some(s => !s.fetch_error && !isVideoUrl(s.name))
  if (hasSourceList && selectedSources.value.size === 0) {
    createError.value = 'Выберите хотя бы один материал для генерации задания'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const isRetelling = selectedType.value === 'retelling'
    const isCards    = selectedType.value === 'cards'
    const isTest     = selectedType.value === 'test'
    const isAnalysis = selectedType.value === 'analysis'
    const isBattle   = selectedType.value === 'battle'
    const res = await apiClient.post(`/assignments/lessons/${lesson.value.id}/assignments`, {
      assignment_type: selectedType.value,
      question_count: isRetelling || isAnalysis || isBattle ? 1 : questionCount.value,
      timer_seconds: isBattle
        ? battleTimer.value
        : (isRetelling || isCards || isAnalysis || (isTest && testMode.value === 'individual')) ? 0 : timerSeconds.value,
      settings_data: isTest
        ? { mode: testMode.value }
        : isAnalysis
          ? { topic: selectedAnalysisTopic.value }
          : undefined,
    })
    const assignmentId = res.data.id
    await apiClient.post(`/assignments/${assignmentId}/generate`)

    // Reset source selections so next visit starts with all unchecked
    try { await apiClient.delete(`/lessons/${lesson.value.id}/sources`) } catch {}
    selectedSources.value = new Set()

    if (isRetelling) {
      router.push(`/lessons/${lesson.value.id}/retelling/${assignmentId}`)
    } else if (isCards) {
      router.push(`/lessons/${lesson.value.id}/cards-group/${assignmentId}`)
    } else if (isTest && testMode.value === 'group') {
      router.push(`/lessons/${lesson.value.id}/screen-test/${assignmentId}`)
    } else if (isAnalysis) {
      router.push(`/lessons/${lesson.value.id}/analysis-group/${assignmentId}`)
    } else if (isBattle) {
      router.push(`/lessons/${lesson.value.id}/battle-screen/${assignmentId}`)
    } else {
      await apiClient.post(`/assignments/${assignmentId}/activate`)
      router.push(`/lessons/${lesson.value.id}/assignment/${assignmentId}`)
    }
  } catch (e: any) {
    createError.value = translateApiError(e.response?.data?.detail, t('lesson.defaultError'))
  } finally {
    creating.value = false
  }
}
</script>
