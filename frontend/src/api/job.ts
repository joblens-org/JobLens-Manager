import { apiClient } from './config'

export interface JobInfo {
  JobID: string
  jobtype: string
  subtype: string
  JobPIDs: number[]
  CollectorNames: string[]
}

export interface JobListResponse {
  service_id: string
  service_name: string
  jobs: JobInfo[]
}

export interface JobCount {
  job_count: number
  total: number
  active: number
  completed: number
  failed: number
}

export interface JobCreateRequest {
  service_id: string
  job_type: 'job.condor' | 'job.common'
  job_id: number
  job_pids: number[]
  lens: string[]
  slot?: string
}

export const jobApi = {
  async getAllJobs(): Promise<JobListResponse[]> {
    const response = await apiClient.get('/jobs')
    return response.data
  },

  async getJobsByServiceIds(serviceIds: string[]): Promise<JobListResponse[]> {
    const params: Record<string, string> = {}
    if (serviceIds && serviceIds.length > 0) {
      params.service_ids = serviceIds.join(',')
    }
    const response = await apiClient.get('/jobs', { params })
    return response.data
  },

  async getJob(jobId: string, serviceId: string): Promise<JobInfo> {
    const response = await apiClient.get(`/jobs/${jobId}`, {
      params: { service_id: serviceId },
    })
    return response.data
  },

  async createJob(request: JobCreateRequest): Promise<JobInfo> {
    const response = await apiClient.post('/jobs', request)
    return response.data
  },

  async deleteJob(jobId: string, serviceId: string, jobType: string): Promise<void> {
    await apiClient.delete(`/jobs/${jobId}`, {
      params: {
        service_id: serviceId,
        job_type: jobType,
      },
    })
  },

  async getJobCount(serviceId: string): Promise<JobCount> {
    const response = await apiClient.get(`/jobs/${serviceId}/count`)
    return response.data
  },
}
