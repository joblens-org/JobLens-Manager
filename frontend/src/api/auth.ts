import axios from 'axios'

interface RuntimeConfig {
  API_BASE_URL: string
}

function getRuntimeConfig(): RuntimeConfig {
  const w = typeof window !== 'undefined' ? window as unknown as Record<string, unknown> : null
  const runtimeConfig = w?.__RUNTIME_CONFIG__ as RuntimeConfig | undefined
  if (runtimeConfig) return runtimeConfig
  return { API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api' }
}

const runtimeConfig = getRuntimeConfig()

const authClient = axios.create({
  baseURL: runtimeConfig.API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
})

export async function loginApi(password: string): Promise<string> {
  const response = await authClient.post('/auth/login', { password })
  return response.data.token
}
