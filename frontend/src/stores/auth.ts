import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { loginApi } from '@/api/auth'

const TOKEN_KEY = 'joblens_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function setToken(value: string | null) {
    token.value = value
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function login(password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const t = await loginApi(password)
      setToken(t)
      return true
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || '登录失败'
      error.value = msg
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    setToken(null)
    error.value = null
  }

  function clearError() {
    error.value = null
  }

  return { token, loading, error, isAuthenticated, login, logout, clearError }
})
