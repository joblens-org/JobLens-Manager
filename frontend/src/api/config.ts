import axios from 'axios'

// 从运行时配置读取环境变量，如果没有则使用默认值
interface RuntimeConfig {
  API_BASE_URL: string
  REFRESH_INTERVAL: string
  API_TIMEOUT: string
  SERVICE_DETAIL_REFRESH_INTERVAL: string
}

const getRuntimeConfig = (): RuntimeConfig => {
  // 尝试从 window.__RUNTIME_CONFIG__ 读取
  const w = typeof window !== 'undefined' ? window as unknown as Record<string, unknown> : null
  const c = w?.__RUNTIME_CONFIG__ as RuntimeConfig | undefined
  if (c) return c
  // 否则使用 Vite 环境变量（开发环境）
  return {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    REFRESH_INTERVAL: import.meta.env.VITE_REFRESH_INTERVAL || '30000',
    API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT || '30000',
    SERVICE_DETAIL_REFRESH_INTERVAL: import.meta.env.VITE_SERVICE_DETAIL_REFRESH_INTERVAL || '5000'
  }
}

const runtimeConfig = getRuntimeConfig()

// 创建 API 客户端
const apiClient = axios.create({
  baseURL: runtimeConfig.API_BASE_URL || 'http://localhost:8000/api',
  timeout: parseInt(runtimeConfig.API_TIMEOUT || '30000'),
})

// 请求拦截器：自动附加认证 token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('joblens_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 未认证
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem('joblens_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// 配置响应接口
export interface ConfigResponse {
  mode: string
  config: string
  metadata?: {
    version: number
    revision: number
    created_revision: number
    mod_revision: number
    lease_id: number
    key: string | null
  }
}

// 版本信息接口
export interface VersionInfo {
  version: number
  revision: number
  timestamp: string
  is_current: boolean
  description?: string
}

// 版本历史响应
export interface VersionHistoryResponse {
  mode: string
  total_versions: number
  current_version: number
  versions: VersionInfo[]
}

// 配置更新请求
export interface ConfigUpdateRequest {
  config: string
  description?: string
}

// 配置更新响应
export interface ConfigUpdateResponse {
  mode: string
  message: string
  new_version: number
  revision: number
  description?: string
  timestamp: string
}

// 特定版本配置响应
export interface VersionConfigResponse {
  mode: string
  version: string
  config: string
  metadata: {
    revision: number
    mod_revision: number
    created_revision: number
    lease_id: number
  }
}

// 回滚响应
export interface RollbackResponse {
  mode: string
  message: string
  from_version: number | null
  to_version: string
  description: string
  timestamp: string
}

// 模式状态响应
export interface ModeStatus {
  mode: string
  exists: boolean
  version: number | null
  has_config: boolean
  info?: Record<string, unknown>
}

// 模式列表响应
export interface ModeListResponse {
  modes: ModeStatus[]
  timestamp: string
}

export const configApi = {
  // 获取当前配置
  async getConfig(mode: string, includeMetadata = false): Promise<ConfigResponse> {
    const response = await apiClient.get(`/configs/${mode}`, {
      params: { include_metadata: includeMetadata },
    })
    return response.data
  },

  // 更新配置
  async updateConfig(
    mode: string,
    config: string,
    description?: string,
  ): Promise<ConfigUpdateResponse> {
    const response = await apiClient.put(`/configs/${mode}`, {
      raw_config: config,
      description: description,
    })
    return response.data
  },

  // 获取版本历史
  async getVersionHistory(mode: string, limit = 10): Promise<VersionHistoryResponse> {
    const response = await apiClient.get(`/configs/${mode}/versions`, {
      params: { limit },
    })
    return response.data
  },

  // 获取特定版本配置
  async getSpecificVersion(mode: string, version: string): Promise<VersionConfigResponse> {
    const response = await apiClient.get(`/configs/${mode}/version/${version}`)
    return response.data
  },

  // 回滚到指定版本
  async rollbackToVersion(
    mode: string,
    version: string,
    description = 'rollback',
  ): Promise<RollbackResponse> {
    const response = await apiClient.post(`/configs/${mode}/rollback/${version}`, null, {
      params: { description },
    })
    return response.data
  },

  // 获取所有模式状态
  async getAllModes(): Promise<ModeListResponse> {
    const response = await apiClient.get('/configs/modes')
    return response.data
  },

  // 健康检查
  async healthCheck(): Promise<Record<string, unknown>> {
    const response = await apiClient.get('/configs/health')
    return response.data
  },
}

export { apiClient }
