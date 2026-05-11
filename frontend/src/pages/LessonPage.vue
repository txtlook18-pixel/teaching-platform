<template>
  <AppLayout>
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="lesson">
      <div class="mb-8">
        <div class="flex justify-between items-start">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">{{ lesson.title }}</h1>
            <p v-if="lesson.cluster_data" class="text-gray-500 mt-1">
              {{ lesson.cluster_data.main_topic }}
            </p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
              {{ lesson.language.toUpperCase() }}
            </span>
            <router-link
              to="/dashboard"
              class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors"
            >
              {{ t('lesson.finishLesson') }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- Cluster info -->
      <div v-if="lesson.cluster_data" class="card mb-8">
        <h2 class="font-semibold text-gray-700 mb-3">{{ t('lesson.analysis.title') }}</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p class="text-xs text-gray-400">{{ t('lesson.analysis.subtopics') }}</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="sub in lesson.cluster_data.subtopics"
                :key="sub"
                class="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded"
              >{{ sub }}</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400">{{ t('lesson.analysis.concepts') }}</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="k in lesson.cluster_data.key_concepts"
                :key="k"
                class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
              >{{ k }}</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400">{{ t('lesson.analysis.difficulty') }}</p>
            <p class="font-medium capitalize mt-1">{{ lesson.cluster_data.difficulty_estimate }}</p>
          </div>
          <router-link :to="`/lessons/${lesson.id}/questions`" class="block hover:opacity-70 transition-opacity cursor-pointer">
            <p class="text-xs text-gray-400">{{ t('lesson.analysis.suggestedCount') }}</p>
            <p class="font-medium mt-1 text-blue-600">{{ lesson.cluster_data.suggested_question_count }}</p>
          </router-link>
        </div>
      </div>

      <!-- Create assignment -->
      <div class="card">
        <h2 class="font-semibold text-gray-800 mb-4 text-lg">{{ t('lesson.createAssignment') }}</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <button
            v-for="atype in assignmentTypes"
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

        <!-- Q&A mode -->
        <div v-if="selectedType === 'retelling'" class="mt-6">
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
        </div>

        <!-- Test mode -->
        <div v-else-if="selectedType === 'test'" class="mt-6 space-y-5">
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

        <!-- Cards mode -->
        <div v-else-if="selectedType === 'cards'" class="mt-6 flex gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.cards.countLabel') }}</label>
            <input v-model.number="questionCount" type="number" min="3" max="30" class="input-field w-24" />
          </div>
          <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
            {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
          </button>
        </div>

        <!-- Analysis mode -->
        <div v-else-if="selectedType === 'analysis'" class="mt-6">
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
                    : selectedAnalysisTopic === sub
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-600'"
                >{{ i + 1 }}</span>
                <span class="text-sm" :class="!extraTopics.length && usedAnalysisTopics.has(sub) ? 'text-gray-400 line-through' : 'text-gray-800'">{{ sub }}</span>
                <span v-if="!extraTopics.length && usedAnalysisTopics.has(sub)" class="ml-auto text-xs text-gray-400">
                  {{ t('lesson.analysisMode.used') }}
                </span>
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

        <!-- Battle mode -->
        <div v-else-if="selectedType === 'battle'" class="mt-6 space-y-4">
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

        <!-- Standard mode -->
        <div v-else-if="selectedType" class="mt-6 flex gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.test.questionCount') }}</label>
            <input v-model.number="questionCount" type="number" min="3" max="20" class="input-field w-24" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('lesson.test.timer') }}</label>
            <select v-model.number="timerSeconds" class="input-field w-28">
              <option :value="30">{{ t('lesson.test.t30') }}</option>
              <option :value="60">{{ t('lesson.test.t60') }}</option>
              <option :value="90">{{ t('lesson.test.t90') }}</option>
              <option :value="120">{{ t('lesson.test.t120') }}</option>
              <option :value="0">{{ t('lesson.test.noTimer') }}</option>
            </select>
          </div>
          <button class="btn-primary px-8 py-2" :disabled="creating" @click="handleCreateAssignment">
            {{ creating ? t('lesson.creating') : t('lesson.createAndLaunch') }}
          </button>
        </div>

        <div v-if="createError" class="mt-4 bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ createError }}</div>
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
import type { Lesson } from '@/types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const lessonStore = useLessonStore()

const loading = ref(true)
const lesson = ref<Lesson | null>(null)
const selectedType = ref('')
const questionCount = ref(10)
const timerSeconds = ref(60)
const testMode = ref<'group' | 'individual'>('group')
const selectedAnalysisTopic = ref('')
const usedAnalysisTopics = ref<Set<string>>(new Set())
const extraTopics = ref<string[]>([])
const loadingExtraTopics = ref(false)

const availableAnalysisTopics = computed<string[]>(() => {
  if (extraTopics.value.length) return extraTopics.value
  return lesson.value?.cluster_data?.subtopics ?? []
})

const allTopicsUsed = computed(() => {
  const topics = lesson.value?.cluster_data?.subtopics ?? []
  return topics.length > 0 && topics.every(t => usedAnalysisTopics.value.has(t))
})

const battleTimer = ref(300)
const battleTimerOptions = computed(() => [
  { value: 180, label: t('lesson.battle.m3') },
  { value: 300, label: t('lesson.battle.m5') },
  { value: 420, label: t('lesson.battle.m7') },
  { value: 600, label: t('lesson.battle.m10') },
])

const creating = ref(false)
const createError = ref('')

const assignmentTypes = computed(() => [
  { value: 'test', icon: '🧪', label: t('lesson.types.test.label'), desc: t('lesson.types.test.desc') },
  { value: 'battle', icon: '⚔️', label: t('lesson.types.battle.label'), desc: t('lesson.types.battle.desc') },
  { value: 'analysis', icon: '🔍', label: t('lesson.types.analysis.label'), desc: t('lesson.types.analysis.desc') },
  { value: 'cards', icon: '🎴', label: t('lesson.types.cards.label'), desc: t('lesson.types.cards.desc') },
  { value: 'retelling', icon: '💬', label: t('lesson.types.retelling.label'), desc: t('lesson.types.retelling.desc') },
])

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
  } finally {
    loading.value = false
  }
})

async function handleCreateAssignment() {
  if (!selectedType.value || !lesson.value) return
  creating.value = true
  createError.value = ''
  try {
    const isRetelling = selectedType.value === 'retelling'
    const isCards = selectedType.value === 'cards'
    const isTest = selectedType.value === 'test'
    const isAnalysis = selectedType.value === 'analysis'
    const isBattle = selectedType.value === 'battle'
    const res = await apiClient.post(`/assignments/lessons/${lesson.value.id}/assignments`, {
      assignment_type: selectedType.value,
      question_count: isRetelling ? 1 : isAnalysis ? 1 : isBattle ? 1 : questionCount.value,
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
