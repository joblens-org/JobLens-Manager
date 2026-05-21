import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import en from './en'

function getDefaultLocale(): string {
  const stored = localStorage.getItem('lang')
  if (stored === 'zh-CN' || stored === 'en') return stored
  const browser = navigator.language
  if (browser.startsWith('zh')) return 'zh-CN'
  return import.meta.env.VITE_DEFAULT_LANG || 'zh-CN'
}

export const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN',
  messages: { 'zh-CN': zhCN, en },
})

export function switchLang(lang: 'zh-CN' | 'en') {
  i18n.global.locale.value = lang
  localStorage.setItem('lang', lang)
}
