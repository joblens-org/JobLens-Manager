import { apiClient } from './config'

export interface ServiceInfo {
  id: string
  host: string
  port: number
  name: string
  version: string
  base_url: string
  healthy?: boolean
  last_heartbeat?: string
  metadata?: Record<string, unknown>
  status: string
  // 新增字段
  mode?: string
  role_id?: string
}

export interface FilterOptions {
  modes: string[]
  roles: Array<{
    id: string
    name: string
  }>
}

export interface ServiceAttributesUpdate {
  mode?: string
  role_id?: string
}

export interface PaginatedServices {
  services: ServiceInfo[]
  total: number
}

export interface ServiceHealth {
  service_id: string
  name: string
  host: string
  port: number
  registry_healthy: boolean
  collector_healthy: boolean
  last_heartbeat?: string
  version?: string
}

export interface RegistryStats {
  total_services: number
  healthy_services: number
  unhealthy_services: number
  active_services: number
}

export interface RegistryHealth {
  status: string
  version: string
  uptime?: string
}

export const serviceApi = {
  async getServices(
    healthyOnly = false,
    unhealthyOnly = false,
    mode?: string,
    roleId?: string,
    search?: string,
    page = 1,
    pageSize = 20,
    sortBy?: string,
    sortOrder?: string,
  ): Promise<PaginatedServices | ServiceInfo[]> {
    const response = await apiClient.get('/services', {
      params: {
        healthy_only: healthyOnly,
        unhealthy_only: unhealthyOnly,
        mode: mode,
        role_id: roleId,
        search: search || undefined,
        page: page,
        page_size: pageSize,
        sort_by: sortBy || undefined,
        sort_order: sortOrder || undefined,
      },
    })
    return response.data
  },

  async getServicesCount(
    healthyOnly = false,
    unhealthyOnly = false,
    mode?: string,
    roleId?: string,
    search?: string,
  ): Promise<number> {
    const response = await apiClient.get('/services/count', {
      params: {
        healthy_only: healthyOnly,
        unhealthy_only: unhealthyOnly,
        mode: mode,
        role_id: roleId,
        search: search || undefined,
      },
    })
    return response.data
  },

  async getService(serviceId: string): Promise<ServiceInfo> {
    const response = await apiClient.get(`/services/${serviceId}`)
    return response.data
  },

  async getServiceHealth(serviceId: string): Promise<ServiceHealth> {
    const response = await apiClient.get(`/services/${serviceId}/health`)
    return response.data
  },

  async deleteService(serviceId: string): Promise<void> {
    await apiClient.delete(`/services/${serviceId}`)
  },

  async getRegistryHealth(): Promise<RegistryHealth> {
    const response = await apiClient.get('/services/registry/health')
    return response.data
  },

  async getRegistryStats(): Promise<RegistryStats> {
    const response = await apiClient.get('/services/registry/stats')
    return response.data
  },

  async getFilterOptions(): Promise<FilterOptions> {
    const response = await apiClient.get('/services/filter-options')
    return response.data
  },

  async getClusterTags(): Promise<string[]> {
    const response = await apiClient.get('/services/cluster/tags')
    return response.data
  },

  async updateServiceAttributes(
    serviceId: string,
    attributes: ServiceAttributesUpdate,
  ): Promise<void> {
    await apiClient.put(`/services/${serviceId}/attributes`, attributes)
  },
}
