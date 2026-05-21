import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())
const mockPost = vi.hoisted(() => vi.fn())
const mockPut = vi.hoisted(() => vi.fn())
const mockDelete = vi.hoisted(() => vi.fn())

vi.mock('./config', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
    put: mockPut,
    delete: mockDelete,
  }
}))

import { rulesApi } from './rules'

describe('rulesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getRules calls GET /rules with pagination', async () => {
    mockGet.mockResolvedValue({ data: { rules: [], total: 0 } })
    const result = await rulesApi.getRules(1, 20)
    expect(mockGet).toHaveBeenCalledWith('/rules', { params: { page: 1, page_size: 20 } })
    expect(result.total).toBe(0)
  })

  it('getRules uses default pagination', async () => {
    mockGet.mockResolvedValue({ data: { rules: [], total: 0 } })
    await rulesApi.getRules()
    expect(mockGet).toHaveBeenCalledWith('/rules', { params: { page: 1, page_size: 20 } })
  })

  it('createRule calls POST /rules', async () => {
    mockPost.mockResolvedValue({ data: { rule_id: 'rule-1', role_id: 'r1', name: 'test' } })
    const result = await rulesApi.createRule({ role_id: 'r1', name: 'test', lua_content: 'function() end' })
    expect(mockPost).toHaveBeenCalledWith('/rules', { role_id: 'r1', name: 'test', lua_content: 'function() end' })
    expect(result.rule_id).toBe('rule-1')
  })

  it('getRule calls GET /rules/{id}', async () => {
    mockGet.mockResolvedValue({ data: { rule_id: 'rule-1', name: 'test' } })
    const result = await rulesApi.getRule('rule-1')
    expect(mockGet).toHaveBeenCalledWith('/rules/rule-1')
    expect(result.name).toBe('test')
  })

  it('updateRule calls PUT /rules/{id}', async () => {
    mockPut.mockResolvedValue({ data: { rule_id: 'rule-1', name: 'updated' } })
    await rulesApi.updateRule('rule-1', { name: 'updated' })
    expect(mockPut).toHaveBeenCalledWith('/rules/rule-1', { name: 'updated' })
  })

  it('deleteRule calls DELETE /rules/{id}', async () => {
    mockDelete.mockResolvedValue({})
    await rulesApi.deleteRule('rule-1')
    expect(mockDelete).toHaveBeenCalledWith('/rules/rule-1')
  })
})
