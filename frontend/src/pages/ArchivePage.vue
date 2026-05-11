<template>
  <AppLayout>
    <div>
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">{{ t('archive.title') }}</h1>
          <p class="text-gray-500 mt-1">{{ t('archive.subtitle') }}</p>
        </div>

        <!-- Filter -->
        <div class="flex gap-2">
          <button
            v-for="f in filters"
            :key="f.value"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
            :class="activeFilter === f.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
            @click="activeFilter = f.value"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="filtered.length === 0" class="text-center py-20">
        <span class="text-6xl">📭</span>
        <h2 class="text-xl font-semibold text-gray-700 mt-4">{{ t('archive.empty.title') }}</h2>
        <p class="text-gray-500 mt-2">
          {{ activeFilter === 'all' ? t('archive.empty.all') : t('archive.empty.filtered') }}
        </p>
      </div>

      <!-- Table -->
      <div v-else class="card overflow-hidden p-0">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-200">
              <tr>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.type') }}</th>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.lesson') }}</th>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.status') }}</th>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.students') }}</th>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.answers') }}</th>
                <th class="text-left px-4 py-3 text-gray-500 font-medium">{{ t('archive.table.date') }}</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="item in filtered"
                :key="item.id"
                class="hover:bg-gray-50 transition-colors"
              >
                <td class="px-4 py-3">
                  <span class="text-xl" :title="typeLabel(item.assignment_type)">
                    {{ typeIcon(item.assignment_type) }}
                  </span>
                  <span class="ml-2 text-gray-700 font-medium">{{ typeLabel(item.assignment_type) }}</span>
                </td>
                <td class="px-4 py-3 text-gray-700 max-w-xs truncate">{{ item.lesson_title }}</td>
                <td class="px-4 py-3">
                  <span
                    class="px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="statusClass(item.status)"
                  >
                    {{ statusLabel(item.status) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-gray-600">{{ item.student_count }}</td>
                <td class="px-4 py-3 text-gray-600">{{ item.response_count }}</td>
                <td class="px-4 py-3 text-gray-400 whitespace-nowrap">
                  {{ new Date(item.created_at).toLocaleDateString(locale) }}
                </td>
                <td class="px-4 py-3">
                  <router-link
                    v-if="item.status === 'active'"
                    :to="`/lessons/${item.lesson_id}/assignment/${item.id}`"
                    class="text-blue-600 hover:text-blue-800 text-xs font-medium"
                  >
                    {{ t('archive.openLink') }}
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLayout from '@/components/layout/AppLayout.vue'
import { apiClient } from '@/services/api'
import type { AssignmentHistoryItem, AssignmentType, AssignmentStatus } from '@/types'

const { t, locale } = useI18n()

const loading = ref(true)
const items = ref<AssignmentHistoryItem[]>([])
const activeFilter = ref<'all' | AssignmentStatus>('all')

const filters = computed(() => [
  { label: t('archive.filters.all'), value: 'all' },
  { label: t('archive.filters.active'), value: 'active' },
  { label: t('archive.filters.finished'), value: 'finished' },
  { label: t('archive.filters.draft'), value: 'draft' },
] as const)

const filtered = computed(() =>
  activeFilter.value === 'all'
    ? items.value
    : items.value.filter((i) => i.status === activeFilter.value),
)

const typeIcon = (type: AssignmentType) =>
  ({ test: '🧪', battle: '⚔️', analysis: '🔍', cards: '🎴', retelling: '📝' }[type] ?? '📋')

const typeLabel = (type: AssignmentType) => {
  const map: Record<string, string> = {
    test: t('archive.types.test'),
    battle: t('archive.types.battle'),
    analysis: t('archive.types.analysis'),
    cards: t('archive.types.cards'),
    retelling: t('archive.types.retelling'),
  }
  return map[type] ?? type
}

const statusLabel = (s: AssignmentStatus) => {
  const map: Record<string, string> = {
    draft: t('archive.statuses.draft'),
    active: t('archive.statuses.active'),
    finished: t('archive.statuses.finished'),
    archived: t('archive.statuses.archived'),
  }
  return map[s] ?? s
}

const statusClass = (s: AssignmentStatus) => ({
  draft:    'bg-gray-100 text-gray-600',
  active:   'bg-green-100 text-green-700',
  finished: 'bg-blue-100 text-blue-700',
  archived: 'bg-amber-100 text-amber-700',
}[s] ?? 'bg-gray-100 text-gray-600')

onMounted(async () => {
  try {
    const res = await apiClient.get<AssignmentHistoryItem[]>('/assignments/history')
    items.value = res.data
  } finally {
    loading.value = false
  }
})
</script>
