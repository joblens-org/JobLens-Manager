import { apiClient } from './config'

export interface ClusterConfig {
  alias: string
  description: string
  enabled: boolean
  extra: Record<string, unknown>
  updated_at?: string
}

export interface ClusterDetail {
  cluster_name: string
  cluster_type: string
  tags: string[]
  alias: string
  description: string
  enabled: boolean
  extra: Record<string, unknown>
  missing_fields: string[]
  updated_at?: string
}

export interface ClusterConfigUpdate {
  alias?: string
  description?: string
  enabled?: boolean
  extra?: Record<string, unknown>
}

export interface ClusterListResponse {
  clusters: ClusterDetail[]
  total: number
}

export interface ClusterScheme {
  cluster_name: string
  cluster_type: string
  tags: string[]
  alias: string
  enabled: boolean
  extra: Record<string, unknown>
  missing_fields: string[]
}

export interface ClusterSchemeResponse {
  clusters: ClusterScheme[]
  total: number
}

export const clusterApi = {
  async getClusters(): Promise<ClusterListResponse> {
    const response = await apiClient.get('/clusters')
    return response.data
  },

  async getCluster(clusterName: string): Promise<ClusterDetail> {
    const response = await apiClient.get(`/clusters/${encodeURIComponent(clusterName)}`)
    return response.data
  },

  async updateClusterConfig(
    clusterName: string,
    config: ClusterConfigUpdate,
  ): Promise<{ message: string; cluster_name: string }> {
    const response = await apiClient.put(
      `/clusters/${encodeURIComponent(clusterName)}/config`,
      config,
    )
    return response.data
  },

  async getClustersScheme(): Promise<ClusterSchemeResponse> {
    const response = await apiClient.get('/clusters/scheme')
    return response.data
  },
}
