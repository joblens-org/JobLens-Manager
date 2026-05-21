import { apiClient } from './config'

// export interface CollectorPerf {
//   name: string
//   type: string
//   metrics_collected: number
//   avg_collection_time: number
//   errors: number
//   last_error?: string
// }

export interface CollectorPerf {
  name: string
  // type: string
  call_cnt: number
  err_cnt: number
  max_us: number
  mean_us: number
  min_us: number
  variance: number
}

// export interface WriterPerf {
//   name: string
//   metrics_written: number
//   avg_write_time: number
//   buffer_size: number
//   errors: number
// }

export interface WriterPerf {
  name: string
  call_cnt: number
  err_cnt: number
  max_us: number
  mean_us: number
  min_us: number
  variance: number
}

export interface WriterInfo {
  name: string
  type: string
  config: Record<string, unknown>
  status: string
  metrics_written: number
}

export interface ServiceMetrics {
  service_id: string
  service_name: string
  collectors: CollectorPerf[]
  writers: WriterPerf[]
}

export interface PrometheusMetrics {
  content: string
}

export interface RegistryMetrics {
  registry_health: {
    status: string
    version: string
    uptime?: string
  }
  registry_stats: {
    total_services: number
    healthy_services: number
    unhealthy_services: number
    active_services: number
  }
}

export const metricsApi = {
  async getCollectorPerformance(serviceId: string): Promise<CollectorPerf[]> {
    const response = await apiClient.get(`/metrics/services/${serviceId}/collectors`)
    return response.data
  },

  async getWriterPerformance(serviceId: string): Promise<WriterPerf[]> {
    const response = await apiClient.get(`/metrics/services/${serviceId}/writers`)
    return response.data
  },

  async getWriterInfo(serviceId: string, writerName: string): Promise<WriterInfo> {
    const response = await apiClient.get(`/metrics/services/${serviceId}/writers/${writerName}`)
    return response.data
  },

  async getAllMetrics(serviceId: string): Promise<ServiceMetrics> {
    const response = await apiClient.get(`/metrics/services/${serviceId}/all`)
    return response.data
  },

  async getPrometheusMetrics(serviceId: string): Promise<string> {
    const response = await apiClient.get(`/metrics/services/${serviceId}/prometheus`)
    return response.data.content
  },

  async getRegistryMetrics(): Promise<RegistryMetrics> {
    const response = await apiClient.get('/metrics/registry')
    return response.data
  },
}
