import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())

vi.mock('./config', () => ({
  apiClient: {
    get: mockGet,
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

import { metricsApi } from './metrics'

describe('metricsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getCollectorPerformance calls GET /metrics/services/{id}/collectors', async () => {
    mockGet.mockResolvedValue({ data: [{ name: 'col-1', call_cnt: 100 }] })
    const result = await metricsApi.getCollectorPerformance('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/metrics/services/svc-1/collectors')
    expect(result[0]?.name).toBe('col-1')
  })

  it('getWriterPerformance calls GET /metrics/services/{id}/writers', async () => {
    mockGet.mockResolvedValue({ data: [{ name: 'wrt-1', call_cnt: 50 }] })
    const result = await metricsApi.getWriterPerformance('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/metrics/services/svc-1/writers')
    expect(result[0]?.name).toBe('wrt-1')
  })

  it('getWriterInfo calls GET /metrics/services/{id}/writers/{name}', async () => {
    mockGet.mockResolvedValue({ data: { name: 'wrt-1', type: 'file', config: {}, status: 'running', metrics_written: 100 } })
    const result = await metricsApi.getWriterInfo('svc-1', 'wrt-1')
    expect(mockGet).toHaveBeenCalledWith('/metrics/services/svc-1/writers/wrt-1')
    expect(result.status).toBe('running')
  })

  it('getAllMetrics calls GET /metrics/services/{id}/all', async () => {
    mockGet.mockResolvedValue({ data: { service_id: 'svc-1', service_name: 'test', collectors: [], writers: [] } })
    const result = await metricsApi.getAllMetrics('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/metrics/services/svc-1/all')
    expect(result.service_id).toBe('svc-1')
  })

  it('getPrometheusMetrics calls GET /metrics/services/{id}/prometheus', async () => {
    mockGet.mockResolvedValue({ data: { content: '# HELP test\ntest 1' } })
    const result = await metricsApi.getPrometheusMetrics('svc-1')
    expect(mockGet).toHaveBeenCalledWith('/metrics/services/svc-1/prometheus')
    expect(result).toBe('# HELP test\ntest 1')
  })

  it('getRegistryMetrics calls GET /metrics/registry', async () => {
    mockGet.mockResolvedValue({ data: { registry_health: { status: 'healthy' }, registry_stats: { total_services: 5 } } })
    const result = await metricsApi.getRegistryMetrics()
    expect(mockGet).toHaveBeenCalledWith('/metrics/registry')
    expect(result.registry_health.status).toBe('healthy')
    expect(result.registry_stats.total_services).toBe(5)
  })
})
