import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())
const mockPut = vi.hoisted(() => vi.fn())
const mockDelete = vi.hoisted(() => vi.fn())

vi.mock('./config', () => ({
  apiClient: {
    get: mockGet,
    post: vi.fn(),
    put: mockPut,
    delete: mockDelete,
  }
}))

import { serviceApi } from './service'

describe('serviceApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getServices calls /services with params', async () => {
    mockGet.mockResolvedValue({ data: { services: [], total: 0 } })
    const result = await serviceApi.getServices(true, false, 'prod', 'role-1', 'search-kw', 2, 10)
    expect(mockGet).toHaveBeenCalledWith('/services', {
      params: { healthy_only: true, unhealthy_only: false, mode: 'prod', role_id: 'role-1', search: 'search-kw', page: 2, page_size: 10 }
    })
    expect(result).toEqual({ services: [], total: 0 })
  })

  it('getServices uses defaults', async () => {
    mockGet.mockResolvedValue({ data: [] })
    await serviceApi.getServices()
    expect(mockGet).toHaveBeenCalledWith('/services', {
      params: { healthy_only: false, unhealthy_only: false, mode: undefined, role_id: undefined, search: undefined, page: 1, page_size: 20 }
    })
  })

  it('getServices passes search param', async () => {
    mockGet.mockResolvedValue({ data: { services: [], total: 0 } })
    await serviceApi.getServices(false, false, undefined, undefined, 'nginx')
    expect(mockGet).toHaveBeenCalledWith('/services', {
      params: { healthy_only: false, unhealthy_only: false, mode: undefined, role_id: undefined, search: 'nginx', page: 1, page_size: 20 }
    })
  })

  it('getServicesCount calls /services/count', async () => {
    mockGet.mockResolvedValue({ data: 5 })
    const result = await serviceApi.getServicesCount(false, false, 'prod', undefined, 'test-kw')
    expect(mockGet).toHaveBeenCalledWith('/services/count', {
      params: { healthy_only: false, unhealthy_only: false, mode: 'prod', role_id: undefined, search: 'test-kw' }
    })
    expect(result).toBe(5)
  })

  it('getService calls /services/{id}', async () => {
    mockGet.mockResolvedValue({ data: { id: 'svc-1', name: 'test' } })
    const result = await serviceApi.getService('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/services/svc-1')
    expect(result.name).toBe('test')
  })

  it('getServiceHealth calls /services/{id}/health', async () => {
    mockGet.mockResolvedValue({ data: { service_id: 'svc-1', registry_healthy: true } })
    const result = await serviceApi.getServiceHealth('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/services/svc-1/health')
    expect(result.registry_healthy).toBe(true)
  })

  it('deleteService calls DELETE /services/{id}', async () => {
    mockDelete.mockResolvedValue({})
    await serviceApi.deleteService('svc-1')
    expect(mockDelete).toHaveBeenCalledWith('/services/svc-1')
  })

  it('getRegistryHealth calls /services/registry/health', async () => {
    mockGet.mockResolvedValue({ data: { status: 'healthy', version: '1.0' } })
    const result = await serviceApi.getRegistryHealth()
    expect(mockGet).toHaveBeenCalledWith('/services/registry/health')
    expect(result.status).toBe('healthy')
  })

  it('getRegistryStats calls /services/registry/stats', async () => {
    mockGet.mockResolvedValue({ data: { total_services: 10 } })
    const result = await serviceApi.getRegistryStats()
    expect(result.total_services).toBe(10)
  })

  it('getFilterOptions calls /services/filter-options', async () => {
    mockGet.mockResolvedValue({ data: { modes: [], roles: [] } })
    const result = await serviceApi.getFilterOptions()
    expect(mockGet).toHaveBeenCalledWith('/services/filter-options')
    expect(result.modes).toEqual([])
  })

  it('getClusterTags calls /services/cluster/tags', async () => {
    mockGet.mockResolvedValue({ data: ['tag1', 'tag2'] })
    const result = await serviceApi.getClusterTags()
    expect(mockGet).toHaveBeenCalledWith('/services/cluster/tags')
    expect(result).toEqual(['tag1', 'tag2'])
  })

  it('updateServiceAttributes calls PUT /services/{id}/attributes', async () => {
    mockPut.mockResolvedValue({})
    await serviceApi.updateServiceAttributes('svc-1', { mode: 'prod', role_id: 'r1' })
    expect(mockPut).toHaveBeenCalledWith('/services/svc-1/attributes', { mode: 'prod', role_id: 'r1' })
  })
})
