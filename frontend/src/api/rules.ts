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

export interface RuleCreate {
  role_id: string
  name: string
  lua_content: string
  metadata?: Record<string, unknown>
}

export interface RuleUpdate {
  name?: string
  lua_content?: string
  metadata?: Record<string, unknown>
}

export interface RuleListResponse {
  rules: RuleInfo[]
  total: number
}

export const rulesApi = {
  // 获取所有规则列表
  async getRules(page: number = 1, pageSize: number = 20): Promise<RuleListResponse> {
    const response = await apiClient.get('/rules', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  // 创建新规则
  async createRule(ruleData: RuleCreate): Promise<RuleInfo> {
    const response = await apiClient.post('/rules', ruleData)
    return response.data
  },

  // 获取规则详情
  async getRule(ruleId: string): Promise<RuleInfo> {
    const response = await apiClient.get(`/rules/${ruleId}`)
    return response.data
  },

  // 更新规则
  async updateRule(ruleId: string, updateData: RuleUpdate): Promise<RuleInfo> {
    const response = await apiClient.put(`/rules/${ruleId}`, updateData)
    return response.data
  },

  // 删除规则
  async deleteRule(ruleId: string): Promise<void> {
    await apiClient.delete(`/rules/${ruleId}`)
  },
}
