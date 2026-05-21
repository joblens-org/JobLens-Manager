import { apiClient } from './config'

export interface RuleInfo {
  rule_id: string
  role_id: string
  name: string
  lua_content: string
  created_at: string
  updated_at: string
  version: number
  metadata?: Record<string, unknown>
}

export interface RoleInfo {
  role_id: string
  name: string
  description?: string
  parent_role_id?: string
  rule_ids: string[]
  created_at: string
  updated_at: string
  service_count: number
  default: boolean
  metadata?: Record<string, unknown>
}

export interface RoleWithRules extends RoleInfo {
  rules: RuleInfo[]
}

export interface RuleListResponse {
  rules: RuleInfo[]
  total: number
}

export interface RoleCreate {
  name: string
  description?: string
  parent_role_id?: string
  rule_ids?: string[]
  metadata?: Record<string, unknown>
}

export interface RoleUpdate {
  description?: string
  default?: boolean
  metadata?: Record<string, unknown>
}

export interface RuleCreate {
  name: string
  lua_content: string
}

export interface RuleUpdate {
  name?: string
  lua_content?: string
}

export interface RoleListResponse {
  roles: RoleInfo[]
  total: number
}

export interface RoleRulesResponse {
  role: RoleWithRules
  effective_rules: RuleInfo[]
}

export const rolesApi = {
  // 获取所有角色列表
  async getRoles(): Promise<RoleListResponse> {
    const response = await apiClient.get('/roles')
    return response.data
  },

  // 创建新角色
  async createRole(roleData: RoleCreate): Promise<RoleInfo> {
    const response = await apiClient.post('/roles', roleData)
    return response.data
  },

  // 获取角色详情
  async getRole(roleId: string): Promise<RoleInfo> {
    const response = await apiClient.get(`/roles/${roleId}`)
    return response.data
  },

  // 更新角色信息
  async updateRole(roleId: string, updateData: RoleUpdate): Promise<RoleInfo> {
    const response = await apiClient.put(`/roles/${roleId}`, updateData)
    return response.data
  },

  // 删除角色
  async deleteRole(roleId: string): Promise<void> {
    await apiClient.delete(`/roles/${roleId}`)
  },



  // 获取角色规则（包括继承的规则）
  async getRoleRules(roleId: string): Promise<RuleListResponse> {
    const response = await apiClient.get(`/roles/${roleId}/rules`)
    return response.data
  },

  // 获取角色生效的规则（去重后）
  async getRoleEffectiveRules(roleId: string): Promise<RuleListResponse> {
    const response = await apiClient.get(`/roles/${roleId}/rules/effective`)
    return response.data
  },

  // 获取默认角色
  async getDefaultRole(): Promise<RoleInfo> {
    const response = await apiClient.get('/roles/default')
    return response.data
  },
}
