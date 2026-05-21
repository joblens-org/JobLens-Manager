import { apiClient } from './config'

export interface ModeInfo {
  name: string
  description?: string
  created_at: string
  updated_at: string
  default: boolean
  config_count: number
}

export interface ModeCreate {
  name: string
  description?: string
  default?: boolean
}

export interface ModeUpdate {
  description?: string
  default?: boolean
}

export interface ModeConfigUpdate {
  raw_config: string
  description?: string
}

export interface ModeConfigResponse {
  mode: string
  config: string
  metadata?: {
    version?: number
    create_revision?: number
    mod_revision?: number
    lease_id?: number
    key?: string
  }
}

export interface ModeVersionInfo {
  version: string
  timestamp: string
  is_current?: boolean
  description?: string
  config_preview?: string
}

export interface ModeVersionsResponse {
  mode: string
  versions: ModeVersionInfo[]
  total: number
  current_version: string
}

export interface ModeRollbackResponse {
  message: string
  mode: string
  from_version?: string
  to_version: string
  timestamp: string
}

export interface ModeListResponse {
  modes: ModeInfo[]
  total: number
}

export const modesApi = {
  // 获取所有模式列表
  async getModes(): Promise<ModeListResponse> {
    const response = await apiClient.get('/modes')
    return response.data
  },

  // 创建新模式
  async createMode(modeData: ModeCreate): Promise<ModeInfo> {
    const response = await apiClient.post('/modes', modeData)
    return response.data
  },

  // 获取模式详情
  async getMode(modeName: string): Promise<ModeInfo> {
    const response = await apiClient.get(`/modes/${modeName}`)
    return response.data
  },

  // 更新模式信息
  async updateMode(modeName: string, updateData: ModeUpdate): Promise<ModeInfo> {
    const response = await apiClient.put(`/modes/${modeName}`, updateData)
    return response.data
  },

  // 删除模式
  async deleteMode(modeName: string): Promise<void> {
    await apiClient.delete(`/modes/${modeName}`)
  },

  // 获取模式配置
  async getModeConfig(modeName: string): Promise<ModeConfigResponse> {
    const response = await apiClient.get(`/modes/${modeName}/config`)
    return response.data
  },

  // 更新模式配置
  async updateModeConfig(modeName: string, configData: ModeConfigUpdate): Promise<{ message: string }> {
    const response = await apiClient.put(`/modes/${modeName}/config`, configData)
    return response.data
  },

  // 获取配置版本历史
  async getModeConfigVersions(modeName: string): Promise<ModeVersionsResponse> {
    const response = await apiClient.get(`/modes/${modeName}/versions`)
    return response.data
  },

  // 回滚到指定版本
  async rollbackModeConfig(modeName: string, version: string): Promise<ModeRollbackResponse> {
    const response = await apiClient.post(`/modes/${modeName}/rollback/${version}`)
    return response.data
  },

  // 获取特定版本配置
  async getSpecificVersion(modeName: string, version: string): Promise<ModeConfigResponse> {
    const response = await apiClient.get(`/modes/${modeName}/version/${version}`)
    return response.data
  },

  // 获取默认模式
  async getDefaultMode(): Promise<ModeInfo> {
    const response = await apiClient.get('/modes/default')
    return response.data
  },
}
