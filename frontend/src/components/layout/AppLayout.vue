<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <router-link to="/dashboard" class="flex items-center gap-2">
            <span class="text-2xl">🎓</span>
            <span class="text-xl font-bold text-blue-600">{{ t('app.logo') }}</span>
          </router-link>

          <nav class="flex items-center gap-4">
            <router-link
              to="/dashboard"
              class="text-gray-600 hover:text-blue-600 font-medium transition-colors"
              active-class="text-blue-600"
            >
              {{ t('nav.lessons') }}
            </router-link>
            <router-link
              to="/archive"
              class="text-gray-600 hover:text-blue-600 font-medium transition-colors"
              active-class="text-blue-600"
            >
              {{ t('nav.history') }}
            </router-link>

            <!-- Language switcher -->
            <div class="relative" ref="langMenuRef">
              <button
                class="flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
                @click="langMenuOpen = !langMenuOpen"
              >
                <span :class="`fi fi-${localeFlagCodes[currentLocale]}`" style="border-radius:2px"></span>
                <svg class="w-3 h-3 ml-0.5" viewBox="0 0 12 12" fill="currentColor">
                  <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>
                </svg>
              </button>
              <div
                v-if="langMenuOpen"
                class="absolute right-0 mt-1 w-36 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-20"
              >
                <button
                  v-for="loc in SUPPORTED_LOCALES"
                  :key="loc"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 transition-colors"
                  :class="loc === currentLocale ? 'text-blue-600 font-semibold' : 'text-gray-700'"
                  @click="selectLocale(loc)"
                >
                  <span :class="`fi fi-${localeFlagCodes[loc]}`" style="border-radius:2px"></span>
                  <span>{{ t(`lang.${loc}`) }}</span>
                  <span v-if="loc === currentLocale" class="ml-auto text-blue-500 text-xs">✓</span>
                </button>
              </div>
            </div>

            <router-link
              to="/profile"
              class="flex items-center gap-1.5 ml-2 text-sm text-gray-600 hover:text-blue-600 transition-colors"
              active-class="text-blue-600"
            >
              <span class="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-600">
                {{ initials }}
              </span>
              {{ authStore.user?.username }}
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { setLocale, SUPPORTED_LOCALES, getCurrentLocale } from '@/i18n'
import type { Locale } from '@/i18n'

const { t, locale } = useI18n()
const authStore = useAuthStore()

const langMenuOpen = ref(false)
const langMenuRef = ref<HTMLElement | null>(null)

const currentLocale = computed(() => locale.value as Locale)

const localeFlagCodes: Record<Locale, string> = { ru: 'ru', en: 'us', uz: 'uz' }

const initials = computed(() =>
  (authStore.user?.username ?? '').slice(0, 2).toUpperCase() || '?',
)

function selectLocale(loc: Locale) {
  setLocale(loc)
  langMenuOpen.value = false
}

function handleClickOutside(e: MouseEvent) {
  if (langMenuRef.value && !langMenuRef.value.contains(e.target as Node)) {
    langMenuOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>
