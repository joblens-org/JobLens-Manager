import { createI18n } from 'vue-i18n'
import elZhCn from 'element-plus/es/locale/lang/zh-cn'
import elEn from 'element-plus/es/locale/lang/en'
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
  messages: {
    // legacy:false 下 EP 组件文案委托给 vue-i18n，必须注入 el.* 键，否则页面直接显示 el.table.emptyText 等原始 key
    'zh-CN': { ...zhCN, el: elZhCn.el },
    en: { ...en, el: elEn.el },
  },
})

export function switchLang(lang: 'zh-CN' | 'en') {
  i18n.global.locale.value = lang
  localStorage.setItem('lang', lang)
}
