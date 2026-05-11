import { defineStore } from 'pinia'
import { computed } from 'vue'
import { i18n, setLocale, getCurrentLocale, SUPPORTED_LOCALES } from '@/i18n'
import type { Locale } from '@/i18n'

export const useLocaleStore = defineStore('locale', () => {
  const locale = computed(() => getCurrentLocale())

  function change(newLocale: Locale) {
    setLocale(newLocale)
  }

  const localeOptions = SUPPORTED_LOCALES.map((code) => ({
    code,
    label: i18n.global.t(`lang.${code}`),
  }))

  return { locale, change, localeOptions, SUPPORTED_LOCALES }
})
