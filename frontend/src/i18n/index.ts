import { createI18n } from 'vue-i18n'
import ru from '@/locales/ru'
import en from '@/locales/en'
import uz from '@/locales/uz'

export type Locale = 'ru' | 'en' | 'uz'
export const SUPPORTED_LOCALES: Locale[] = ['ru', 'en', 'uz']
export const DEFAULT_LOCALE: Locale = 'ru'

function getStoredLocale(): Locale {
  const stored = localStorage.getItem('app_locale') as Locale | null
  return stored && SUPPORTED_LOCALES.includes(stored) ? stored : DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: getStoredLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: { ru, en, uz },
})

export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('app_locale', locale)
  document.documentElement.lang = locale
}

export function getCurrentLocale(): Locale {
  return i18n.global.locale.value as Locale
}

/** Translate a backend error code (e.g. "error.invalid_credentials") to UI string.
 *  Supports optional colon-separated context: "error.file_too_large:filename.pdf" */
export function translateApiError(detail: string | undefined, fallback: string): string {
  if (!detail) return fallback
  if (detail.startsWith('error.')) {
    // Strip any trailing context (e.g. filename after first colon past "error.")
    const withoutPrefix = detail.slice(6) // removes "error."
    const codeOnly = withoutPrefix.split(':')[0]
    const context = withoutPrefix.includes(':') ? withoutPrefix.slice(codeOnly.length + 1) : ''
    const key = `errors.${codeOnly}`
    const translated = i18n.global.t(key)
    const message = translated !== key ? translated : fallback
    return context ? `${message}: ${context}` : message
  }
  return detail
}
