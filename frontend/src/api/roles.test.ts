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

import { rolesApi } from './roles'

describe('rolesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getRoles calls GET /roles', async () => {
    mockGet.mockResolvedValue({ data: { roles: [], total: 0 } })
    const result = await rolesApi.getRoles()
    expect(mockGet).toHaveBeenCalledWith('/roles')
    expect(result.total).toBe(0)
  })

  it('createRole calls POST /roles', async () => {
    mockPost.mockResolvedValue({ data: { role_id: 'r1', name: 'admin' } })
    const result = await rolesApi.createRole({ name: 'admin' })
    expect(mockPost).toHaveBeenCalledWith('/roles', { name: 'admin' })
    expect(result.role_id).toBe('r1')
  })

  it('getRole calls GET /roles/{id}', async () => {
    mockGet.mockResolvedValue({ data: { role_id: 'r1', name: 'admin' } })
    const result = await rolesApi.getRole('r1')
    expect(mockGet).toHaveBeenCalledWith('/roles/r1')
    expect(result.name).toBe('admin')
  })

  it('updateRole calls PUT /roles/{id}', async () => {
    mockPut.mockResolvedValue({ data: { role_id: 'r1', name: 'admin', description: 'new' } })
    await rolesApi.updateRole('r1', { description: 'new' })
    expect(mockPut).toHaveBeenCalledWith('/roles/r1', { description: 'new' })
  })

  it('deleteRole calls DELETE /roles/{id}', async () => {
    mockDelete.mockResolvedValue({})
    await rolesApi.deleteRole('r1')
    expect(mockDelete).toHaveBeenCalledWith('/roles/r1')
  })

  it('getRoleRules calls GET /roles/{id}/rules', async () => {
    mockGet.mockResolvedValue({ data: { rules: [], total: 0 } })
    const result = await rolesApi.getRoleRules('r1')
    expect(mockGet).toHaveBeenCalledWith('/roles/r1/rules')
    expect(result.total).toBe(0)
  })

  it('getRoleEffectiveRules calls GET /roles/{id}/rules/effective', async () => {
    mockGet.mockResolvedValue({ data: { rules: [], total: 0 } })
    await rolesApi.getRoleEffectiveRules('r1')
    expect(mockGet).toHaveBeenCalledWith('/roles/r1/rules/effective')
  })

  it('getDefaultRole calls GET /roles/default', async () => {
    mockGet.mockResolvedValue({ data: { role_id: 'default-id', name: 'default-role' } })
    const result = await rolesApi.getDefaultRole()
    expect(mockGet).toHaveBeenCalledWith('/roles/default')
    expect(result.name).toBe('default-role')
  })
})
