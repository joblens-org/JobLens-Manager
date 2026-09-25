import { describe, expect, it, vi } from 'vitest'

vi.mock('./router', () => ({
  default: {
    install() {},
  },
}))

vi.mock('./App.vue', async () => {
  const { h } = await import('vue')
  const { ElPagination } = await import('element-plus')

  return {
    default: {
      setup() {
        return () =>
          h(ElPagination, {
            layout: 'total, jumper',
            total: 20,
          })
      },
    },
  }
})

async function bootstrap(lang: 'zh-CN' | 'en') {
  localStorage.setItem('lang', lang)
  document.body.innerHTML = '<div id="app"></div>'
  vi.resetModules()
  await import('./main')

  return {
    jumperValue:
      document.querySelector<HTMLInputElement>('.el-pagination__jump .el-input__inner')?.value ?? '',
    text: document.body.textContent?.replace(/\s+/g, ' ').trim() ?? '',
  }
}

describe('Element Plus locale', () => {
  it('renders Chinese pagination copy instead of raw locale keys', async () => {
    const { jumperValue, text } = await bootstrap('zh-CN')

    expect(text).toContain('共 20 条')
    expect(text).toContain('前往页')
    expect(jumperValue).toBe('1')
    expect(text).not.toContain('el.pagination.')
  })

  it('renders English pagination copy instead of raw locale keys', async () => {
    const { jumperValue, text } = await bootstrap('en')

    expect(text).toContain('Total 20')
    expect(text).toContain('Go to')
    expect(jumperValue).toBe('1')
    expect(text).not.toContain('el.pagination.')
  })
})
