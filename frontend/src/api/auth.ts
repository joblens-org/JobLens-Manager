import axios from 'axios'

const runtimeConfig = (typeof window !== 'undefined' && (window as any).__RUNTIME_CONFIG__)
  ? (window as any).__RUNTIME_CONFIG__
  : { API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api' }

const authClient = axios.create({
  baseURL: runtimeConfig.API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
})

export async function loginApi(password: string): Promise<string> {
  const response = await authClient.post('/auth/login', { password })
  return response.data.token
}
