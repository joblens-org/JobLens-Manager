import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.hoisted(() => vi.fn())
const mockPost = vi.hoisted(() => vi.fn())
const mockDelete = vi.hoisted(() => vi.fn())

vi.mock('./config', () => ({
  apiClient: {
    get: mockGet,
    post: mockPost,
    put: vi.fn(),
    delete: mockDelete,
  }
}))

import { jobApi } from './job'

describe('jobApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getAllJobs calls GET /jobs', async () => {
    mockGet.mockResolvedValue({ data: [{ service_id: 's1', jobs: [] }] })
    const result = await jobApi.getAllJobs()
    expect(mockGet).toHaveBeenCalledWith('/jobs')
    expect(result[0]?.service_id).toBe('s1')
  })

  it('getJobsByServiceIds calls GET /jobs with service_ids', async () => {
    mockGet.mockResolvedValue({ data: [] })
    await jobApi.getJobsByServiceIds(['s1', 's2'])
    expect(mockGet).toHaveBeenCalledWith('/jobs', { params: { service_ids: 's1,s2' } })
  })

  it('getJobsByServiceIds with empty array sends no param', async () => {
    mockGet.mockResolvedValue({ data: [] })
    await jobApi.getJobsByServiceIds([])
    expect(mockGet).toHaveBeenCalledWith('/jobs', { params: {} })
  })

  it('getJob calls GET /jobs/{id} with service_id param', async () => {
    mockGet.mockResolvedValue({ data: { JobID: '1', jobtype: 'job', subtype: 'common' } })
    const result = await jobApi.getJob('1', 's1')
    expect(mockGet).toHaveBeenCalledWith('/jobs/1', { params: { service_id: 's1' } })
    expect(result.JobID).toBe('1')
  })

  it('createJob calls POST /jobs with body', async () => {
    mockPost.mockResolvedValue({ data: { JobID: '1' } })
    const req = { service_id: 's1', job_type: 'job.common' as const, job_id: 1, job_pids: [100], lens: ['l1'] }
    const result = await jobApi.createJob(req)
    expect(mockPost).toHaveBeenCalledWith('/jobs', req)
    expect(result.JobID).toBe('1')
  })

  it('deleteJob calls DELETE /jobs/{id} with params', async () => {
    mockDelete.mockResolvedValue({})
    await jobApi.deleteJob('1', 's1', 'job.common')
    expect(mockDelete).toHaveBeenCalledWith('/jobs/1', { params: { service_id: 's1', job_type: 'job.common' } })
  })

  it('getJobCount calls GET /jobs/{id}/count', async () => {
    mockGet.mockResolvedValue({ data: { job_count: 5, total: 10 } })
    const result = await jobApi.getJobCount('s1')
    expect(mockGet).toHaveBeenCalledWith('/jobs/s1/count')
    expect(result.job_count).toBe(5)
  })
})
