import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())
const mockPut = vi.hoisted(() => vi.fn())

vi.mock('./config', () => ({
  apiClient: {
    get: mockGet,
    put: mockPut,
  }
}))

import { clusterApi } from './cluster'

describe('clusterApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getClusters calls GET /clusters', async () => {
    mockGet.mockResolvedValue({ data: { clusters: [], total: 0 } })
    const result = await clusterApi.getClusters()
    expect(mockGet).toHaveBeenCalledWith('/clusters')
    expect(result).toEqual({ clusters: [], total: 0 })
  })

  it('getClusters with data', async () => {
    const mockClusters = {
      clusters: [
        {
          cluster_name: 'condor-1',
          cluster_type: 'condor',
          tags: ['t1', 't2'],
          alias: '生产',
          description: '测试',
          enabled: true,
          extra: {},
          missing_fields: ['es_url', 'es_password'],
        },
      ],
      total: 1,
    }
    mockGet.mockResolvedValue({ data: mockClusters })
    const result = await clusterApi.getClusters()
    expect(result.total).toBe(1)
    expect(result.clusters[0]?.cluster_name).toBe('condor-1')
    expect(result.clusters[0]?.tags).toEqual(['t1', 't2'])
    expect(result.clusters[0]?.missing_fields).toEqual(['es_url', 'es_password'])
  })

  it('getCluster calls GET /clusters/:name', async () => {
    const mockCluster = {
      cluster_name: 'condor-1',
      cluster_type: 'condor',
      tags: ['t1'],
      alias: '',
      description: '',
      enabled: true,
      extra: {},
    }
    mockGet.mockResolvedValue({ data: mockCluster })
    const result = await clusterApi.getCluster('condor-1')
    expect(mockGet).toHaveBeenCalledWith('/clusters/condor-1')
    expect(result.cluster_name).toBe('condor-1')
  })

  it('getCluster URL-encodes cluster name with special characters', async () => {
    mockGet.mockResolvedValue({ data: { cluster_name: 'test/name', cluster_type: 'condor', tags: [] } })
    await clusterApi.getCluster('test/name')
    expect(mockGet).toHaveBeenCalledWith('/clusters/test%2Fname')
  })

  it('updateClusterConfig calls PUT /clusters/:name/config', async () => {
    mockPut.mockResolvedValue({ data: { message: 'ok', cluster_name: 'condor-1' } })
    const updateData = { alias: '新别名', enabled: false }
    const result = await clusterApi.updateClusterConfig('condor-1', updateData)
    expect(mockPut).toHaveBeenCalledWith('/clusters/condor-1/config', updateData)
    expect(result.message).toBe('ok')
  })

  it('updateClusterConfig with all fields', async () => {
    mockPut.mockResolvedValue({ data: { message: 'ok', cluster_name: 'condor-1' } })
    const updateData = {
      alias: '新别名',
      description: '新描述',
      enabled: false,
      extra: { key: 'value' },
    }
    await clusterApi.updateClusterConfig('condor-1', updateData)
    expect(mockPut).toHaveBeenCalledWith('/clusters/condor-1/config', updateData)
  })

  it('getClustersScheme calls GET /clusters/scheme', async () => {
    mockGet.mockResolvedValue({ data: { clusters: [], total: 0 } })
    const result = await clusterApi.getClustersScheme()
    expect(mockGet).toHaveBeenCalledWith('/clusters/scheme')
    expect(result).toEqual({ clusters: [], total: 0 })
  })

  it('getClustersScheme with data', async () => {
    const mockSchemes = {
      clusters: [
        {
          cluster_name: 'condor-1',
          cluster_type: 'condor',
          tags: ['t1'],
          alias: '生产',
          enabled: true,
          extra: {},
        },
      ],
      total: 1,
    }
    mockGet.mockResolvedValue({ data: mockSchemes })
    const result = await clusterApi.getClustersScheme()
    expect(result.clusters[0]?.cluster_name).toBe('condor-1')
    // scheme 不应有 description
    expect(result.clusters[0]).not.toHaveProperty('description')
  })
})
