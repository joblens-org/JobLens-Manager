import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())
const mockPut = vi.hoisted(() => vi.fn())
const mockPost = vi.hoisted(() => vi.fn())

const mockInterceptorRequestUse = vi.hoisted(() => vi.fn())
const mockInterceptorResponseUse = vi.hoisted(() => vi.fn())

const mockAxiosInstance = vi.hoisted(() => ({
  get: mockGet,
  put: mockPut,
  post: mockPost,
  delete: vi.fn(),
  interceptors: {
    request: { use: mockInterceptorRequestUse },
    response: { use: mockInterceptorResponseUse },
  },
}))

vi.mock('axios', () => {
  const mockAxios = vi.fn() as unknown as Record<string, unknown>
  mockAxios.create = vi.fn(() => mockAxiosInstance)
  mockAxios.isAxiosError = vi.fn(() => false)
  return { default: mockAxios as unknown as typeof import('axios').default }
})

import { configApi } from './config'

describe('configApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getConfig calls GET /configs/{mode} with params', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'test', config: 'yaml' } })
    const result = await configApi.getConfig('test', true)
    expect(mockGet).toHaveBeenCalledWith('/configs/test', { params: { include_metadata: true } })
    expect(result.mode).toBe('test')
  })

  it('getConfig defaults to no metadata', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'test', config: '' } })
    await configApi.getConfig('test')
    expect(mockGet).toHaveBeenCalledWith('/configs/test', { params: { include_metadata: false } })
  })

  it('updateConfig calls PUT /configs/{mode}', async () => {
    mockPut.mockResolvedValue({ data: { mode: 'test', message: 'ok', new_version: 2 } })
    const result = await configApi.updateConfig('test', 'new: yaml', 'update desc')
    expect(mockPut).toHaveBeenCalledWith('/configs/test', { raw_config: 'new: yaml', description: 'update desc' })
    expect(result.new_version).toBe(2)
  })

  it('updateConfig without description', async () => {
    mockPut.mockResolvedValue({ data: { mode: 'test', message: 'ok', new_version: 1 } })
    await configApi.updateConfig('test', 'yaml')
    expect(mockPut).toHaveBeenCalledWith('/configs/test', { raw_config: 'yaml', description: undefined })
  })

  it('getVersionHistory calls GET /configs/{mode}/versions', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'test', total_versions: 3, current_version: 3, versions: [] } })
    const result = await configApi.getVersionHistory('test', 5)
    expect(mockGet).toHaveBeenCalledWith('/configs/test/versions', { params: { limit: 5 } })
    expect(result.total_versions).toBe(3)
  })

  it('getSpecificVersion calls GET /configs/{mode}/version/{v}', async () => {
    mockGet.mockResolvedValue({ data: { mode: 'test', version: 'v1', config: 'yaml' } })
    const result = await configApi.getSpecificVersion('test', 'v1')
    expect(mockGet).toHaveBeenCalledWith('/configs/test/version/v1')
    expect(result.config).toBe('yaml')
  })

  it('rollbackToVersion calls POST /configs/{mode}/rollback/{v}', async () => {
    mockPost.mockResolvedValue({ data: { mode: 'test', message: 'ok', to_version: 'v1' } })
    const result = await configApi.rollbackToVersion('test', 'v1')
    expect(mockPost).toHaveBeenCalledWith('/configs/test/rollback/v1', null, { params: { description: 'rollback' } })
    expect(result.to_version).toBe('v1')
  })

  it('getAllModes calls GET /configs/modes', async () => {
    mockGet.mockResolvedValue({ data: { modes: [], timestamp: '' } })
    await configApi.getAllModes()
    expect(mockGet).toHaveBeenCalledWith('/configs/modes')
  })

  it('healthCheck calls GET /configs/health', async () => {
    mockGet.mockResolvedValue({ data: { status: 'healthy' } })
    const result = await configApi.healthCheck()
    expect(mockGet).toHaveBeenCalledWith('/configs/health')
    expect(result.status).toBe('healthy')
  })
})
