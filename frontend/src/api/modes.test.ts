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

import { modesApi } from './modes'

describe('modesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getModes calls GET /modes', async () => {
    mockGet.mockResolvedValue({ data: { modes: [], total: 0 } })
    const result = await modesApi.getModes()
    expect(mockGet).toHaveBeenCalledWith('/modes')
    expect(result.total).toBe(0)
  })

  it('createMode calls POST /modes', async () => {
    mockPost.mockResolvedValue({ data: { name: 'new-mode', default: false } })
    const result = await modesApi.createMode({ name: 'new-mode', description: 'desc' })
    expect(mockPost).toHaveBeenCalledWith('/modes', { name: 'new-mode', description: 'desc' })
    expect(result.name).toBe('new-mode')
  })

  it('getMode calls GET /modes/{name}', async () => {
    mockGet.mockResolvedValue({ data: { name: 'prod', description: '生产', default: true, config_count: 1 } })
    const result = await modesApi.getMode('prod')
    expect(mockGet).toHaveBeenCalledWith('/modes/prod')
    expect(result.name).toBe('prod')
  })

  it('updateMode calls PUT /modes/{name}', async () => {
    mockPut.mockResolvedValue({ data: { name: 'prod', description: '新描述', default: true, config_count: 1 } })
    await modesApi.updateMode('prod', { description: '新描述' })
    expect(mockPut).toHaveBeenCalledWith('/modes/prod', { description: '新描述' })
  })

  it('deleteMode calls DELETE /modes/{name}', async () => {
    mockDelete.mockResolvedValue({})
    await modesApi.deleteMode('prod')
    expect(mockDelete).toHaveBeenCalledWith('/modes/prod')
  })

  it('getModeConfig calls GET /modes/{name}/config', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'prod', config: 'yaml' } })
    const result = await modesApi.getModeConfig('prod')
    expect(mockGet).toHaveBeenCalledWith('/modes/prod/config')
    expect(result.config).toBe('yaml')
  })

  it('updateModeConfig calls PUT /modes/{name}/config', async () => {
    mockPut.mockResolvedValue({ data: { message: '已更新' } })
    const result = await modesApi.updateModeConfig('prod', { raw_config: 'new' })
    expect(mockPut).toHaveBeenCalledWith('/modes/prod/config', { raw_config: 'new' })
    expect(result.message).toBe('已更新')
  })

  it('getModeConfigVersions calls GET /modes/{name}/versions', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'prod', versions: [], total: 0, current_version: 'v1' } })
    const result = await modesApi.getModeConfigVersions('prod')
    expect(mockGet).toHaveBeenCalledWith('/modes/prod/versions')
    expect(result.current_version).toBe('v1')
  })

  it('rollbackModeConfig calls POST /modes/{name}/rollback/{v}', async () => {
    mockPost.mockResolvedValue({ data: { message: '已回滚', mode: 'prod', to_version: 'v1', timestamp: '' } })
    const result = await modesApi.rollbackModeConfig('prod', 'v1')
    expect(mockPost).toHaveBeenCalledWith('/modes/prod/rollback/v1')
    expect(result.message).toBe('已回滚')
  })

  it('getSpecificVersion calls GET /modes/{name}/version/{v}', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'prod', version: 'v1', config: 'yaml' } })
    const result = await modesApi.getSpecificVersion('prod', 'v1')
    expect(mockGet).toHaveBeenCalledWith('/modes/prod/version/v1')
  })

  it('getDefaultMode calls GET /modes/default', async () => {
    mockGet.mockResolvedValue({ data: { name: 'default', default: true, config_count: 1 } })
    const result = await modesApi.getDefaultMode()
    expect(mockGet).toHaveBeenCalledWith('/modes/default')
    expect(result.default).toBe(true)
  })
})
