<template>
  <div class="job-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ $t('job.title') }}</span>
          <el-button
            type="primary"
            @click="showCreateDialog = true"
            :size="isMobile ? 'small' : 'default'"
          >
            <el-icon><Plus /></el-icon>
            <span v-if="!isMobile">{{ $t('job.addJob') }}</span>
          </el-button>
        </div>
      </template>

      <div class="table-container" ref="tableContainerRef">
        <!-- 节点选择区域 -->
        <div class="service-selector">
          <div class="selector-header">
            <span class="selector-title">{{ $t('job.selectNodes') }}</span>
          </div>
          <div class="selector-controls">
            <el-input
              v-model="serviceSearchKeyword"
              :placeholder="$t('job.searchNodePlaceholder')"
              clearable
              :size="isMobile ? 'small' : 'default'"
              style="flex-basis: 200px"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="selectAllServices" :size="isMobile ? 'small' : 'default'">
              {{ $t('job.selectAll') }}
            </el-button>
            <el-button @click="clearSelectedServices" :size="isMobile ? 'small' : 'default'">
              {{ $t('job.clearSelection') }}
            </el-button>
            <el-button
              type="primary"
              @click="loadJobsForSelectedServices"
              :loading="loading"
              :size="isMobile ? 'small' : 'default'"
            >
              {{ $t('job.loadJobs') }}
            </el-button>
          </div>
          <div class="selected-services">
            <el-tag
              v-for="service in selectedServices"
              :key="service.id"
              closable
              @close="removeService(service.id)"
              :size="isMobile ? 'small' : 'default'"
            >
              {{ service.name }}
            </el-tag>
            <span v-if="selectedServices.length === 0" class="no-selection">
              {{ $t('job.noNodeSelected') }}
            </span>
          </div>
          <div class="service-list">
            <el-checkbox-group v-model="selectedServiceIds" class="service-checkbox-group">
              <el-checkbox
                v-for="service in filteredServices"
                :key="service.id"
                :label="service.id"
                class="service-checkbox"
              >
                {{ service.name }}
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>

        <!-- 筛选区域 -->
        <div class="filter-bar">
          <el-input
            v-model="filters.keyword"
            :placeholder="$t('job.searchPlaceholderDetail')"
            clearable
            :size="isMobile ? 'small' : 'default'"
            style="flex-basis: 240px"
          >
            <template #append>
              <el-button @click="onSearch" :size="isMobile ? 'small' : 'default'">{{ $t('common.search') }}</el-button>
            </template>
          </el-input>
          <el-select
            v-model="filters.subtype"
            :placeholder="$t('job.filterByType')"
            clearable
            :size="isMobile ? 'small' : 'default'"
            style="flex-basis: 160px"
          >
            <el-option v-for="type in subtypes" :key="type" :label="type" :value="type" />
          </el-select>
          <el-select
            v-model="filters.lenses"
            multiple
            :placeholder="$t('job.filterByLens')"
            clearable
            :size="isMobile ? 'small' : 'default'"
            style="flex-basis: 160px"
          >
            <el-option v-for="lens in allLenses" :key="lens" :label="lens" :value="lens" />
          </el-select>
          <el-button @click="clearFilters" :size="isMobile ? 'small' : 'default'">{{ $t('common.reset') }}</el-button>
          <div class="result-count">{{ $t('job.totalRecords', { count: filteredJobs.length }) }}</div>
        </div>

        <el-table
          v-loading="loading"
          :data="pageJobs"
          style="width: 100%"
          :size="isMobile ? 'small' : 'default'"
        >
          <el-table-column
            prop="service_name"
            :label="$t('job.belongService')"
            min-width="150"
            :show-overflow-tooltip="true"
          />
          <el-table-column prop="JobID" :label="$t('job.jobId')" width="100" />
          <el-table-column prop="subtype" :label="$t('job.jobType')" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.subtype }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('job.processId')" min-width="150">
            <template #default="{ row }">
              <div class="tag-list">
                <el-tag
                  v-for="pid in row.JobPIDs.slice(0, 2)"
                  :key="pid"
                  size="small"
                  class="tag-item"
                >
                  {{ pid }}
                </el-tag>
                <el-tag v-if="row.JobPIDs.length > 2" size="small" type="info">
                  +{{ row.JobPIDs.length - 2 }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('job.lens')" min-width="150">
            <template #default="{ row }">
              <div class="tag-list">
                <el-tag
                  v-for="lens in row.CollectorNames.slice(0, 2)"
                  :key="lens"
                  size="small"
                  class="tag-item"
                >
                  {{ lens }}
                </el-tag>
                <el-tag v-if="row.CollectorNames.length > 2" size="small" type="info">
                  +{{ row.CollectorNames.length - 2 }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <!-- <el-table-column prop="status" label="状态" width="80" fixed="right">
            <template #default="{ row }">
              <el-tag 
                :type="row.status === 'running' ? 'success' : 'info'" 
                size="small"
              >
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column> -->
          <el-table-column :label="$t('common.operation')" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                type="danger"
                :size="isMobile ? 'small' : 'default'"
                @click="deleteJob(row)"
              >
                {{ $t('common.delete') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-row justify="center" style="margin-top: 4px">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredJobs.length"
            background
            @current-change="handlePageChange"
          />
        </el-row>
      </div>
    </el-card>

    <el-dialog
      v-model="showCreateDialog"
      :title="$t('job.addJob')"
      :width="isMobile ? '90%' : '600px'"
      @close="resetForm"
      class="create-dialog"
    >
      <el-form
        ref="formRef"
        :model="createForm"
        :rules="rules"
        :label-width="isMobile ? '100px' : '120px'"
        :label-position="isMobile ? 'top' : 'right'"
      >
        <el-form-item :label="$t('job.targetService')" prop="service_id">
          <el-select v-model="createForm.service_id" :placeholder="$t('job.selectServicePlaceholder')" style="width: 100%">
            <el-option
              v-for="service in services"
              :key="service.id"
              :label="service.name"
              :value="service.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('job.jobType')" prop="job_type">
          <el-radio-group v-model="createForm.job_type" class="radio-group">
            <el-radio label="job.condor">{{ $t('job.condorJob') }}</el-radio>
            <el-radio label="job.common">{{ $t('job.commonJob') }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item :label="$t('job.jobId')" prop="job_id">
          <el-input-number v-model="createForm.job_id" :min="1" style="width: 100%" />
        </el-form-item>

        <el-form-item :label="$t('job.processId')" prop="job_pids">
          <el-select
            v-model="createForm.job_pids"
            multiple
            filterable
            allow-create
            :placeholder="$t('job.enterPidPlaceholder')"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item :label="$t('job.lens')" prop="lens">
          <el-select
            v-model="createForm.lens"
            multiple
            filterable
            allow-create
            :placeholder="$t('job.enterLensPlaceholder')"
            style="width: 100%"
          >
            <el-option label="proc_collector" value="proc_collector" />
            <el-option label="system_collector" value="system_collector" />
            <el-option label="network_collector" value="network_collector" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="createForm.job_type === 'job.condor'" :label="$t('job.slot')" prop="slot">
          <el-input v-model="createForm.slot" :placeholder="$t('job.slotPlaceholder')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createJob" :loading="creating">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { jobApi, serviceApi } from '@/api'
import type { JobListResponse, JobCreateRequest, ServiceInfo } from '@/api'

const { t } = useI18n()

const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const jobResponses = ref<JobListResponse[]>([])
const services = ref<ServiceInfo[]>([])
const isMobile = ref(window.innerWidth <= 768)

// 节点选择相关
const serviceSearchKeyword = ref('')
const selectedServiceIds = ref<string[]>([])

const currentPage = ref(1)
const pageSize = ref(10)

const formRef = ref()
const createForm = ref<JobCreateRequest>({
  service_id: '',
  job_type: 'job.common',
  job_id: 1,
  job_pids: [],
  lens: ['proc_collector'],
  slot: 'slot1',
})

const rules = computed(() => ({
  service_id: [{ required: true, message: t('job.selectServiceRequired'), trigger: 'change' }],
  job_type: [{ required: true, message: t('job.selectTypeRequired'), trigger: 'change' }],
  job_id: [{ required: true, message: t('job.enterJobIdRequired'), trigger: 'blur' }],
  job_pids: [{ required: true, message: t('job.pidRequired'), trigger: 'change' }],
  lens: [{ required: true, message: t('job.lensRequired'), trigger: 'change' }],
  slot: [{ required: true, message: t('job.enterSlotRequired'), trigger: 'blur' }],
}))

const allJobs = computed(() => {
  const jobs: any[] = []
  jobResponses.value.forEach((response) => {
    response.jobs.forEach((job) => {
      jobs.push({
        ...job,
        service_name: response.service_name,
        service_id: response.service_id,
      })
    })
  })
  return jobs
})

// 节点选择相关计算属性
const selectedServices = computed(() => {
  return services.value.filter(s => selectedServiceIds.value.includes(s.id))
})

const filteredServices = computed(() => {
  if (!serviceSearchKeyword.value) {
    return services.value
  }
  const keyword = serviceSearchKeyword.value.toLowerCase()
  return services.value.filter(s => 
    s.name.toLowerCase().includes(keyword) || 
    s.id.toLowerCase().includes(keyword)
  )
})

const filters = ref({
  keyword: '',
  service_id: '',
  subtype: '',
  lenses: [] as string[],
})

watch(
  filters,
  () => {
    currentPage.value = 1
  },
  { deep: true },
)

const pageJobs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredJobs.value.slice(start, end)
})

const subtypes = computed(() => {
  const set = new Set<string>()
  allJobs.value.forEach((j) => {
    if (j.subtype) set.add(j.subtype)
  })
  return Array.from(set)
})

const allLenses = computed(() => {
  const set = new Set<string>()
  allJobs.value.forEach((j) => {
    ;(j.CollectorNames || []).forEach((l: string) => set.add(l))
  })
  return Array.from(set)
})

const filteredJobs = computed(() => {
  const kw = (filters.value.keyword || '').toString().trim().toLowerCase()
  return allJobs.value.filter((job: any) => {
    if (filters.value.service_id && String(job.service_id) !== String(filters.value.service_id)) {
      return false
    }
    if (filters.value.subtype && job.subtype !== filters.value.subtype) {
      return false
    }
    if (filters.value.lenses && filters.value.lenses.length > 0) {
      const hasLens = (job.CollectorNames || []).some((l: string) =>
        filters.value.lenses.includes(l),
      )
      if (!hasLens) return false
    }
    if (kw) {
      const found =
        (job.service_name || '').toString().toLowerCase().includes(kw) ||
        String(job.JobID || job.job_id || '')
          .toLowerCase()
          .includes(kw) ||
        (job.subtype || '').toString().toLowerCase().includes(kw) ||
        String(job.service_id || '')
          .toLowerCase()
          .includes(kw) ||
        (job.JobPIDs || []).some((p: any) => String(p).toLowerCase().includes(kw)) ||
        (job.CollectorNames || []).some((l: any) => String(l).toLowerCase().includes(kw))
      if (!found) return false
    }
    return true
  })
})

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

const handlePageChange = () => {
  nextTick(() => {
    document.querySelector('.table-container')?.scrollIntoView({ behavior: 'smooth' })
  })
}

const onSearch = () => {
  currentPage.value = 1
}

const clearFilters = () => {
  filters.value = { keyword: '', service_id: '', subtype: '', lenses: [] }
}

const loadJobsForSelectedServices = async () => {
  if (selectedServiceIds.value.length === 0) {
    ElMessage.warning(t('job.selectNodesFirst'))
    return
  }
  
  loading.value = true
  try {
    jobResponses.value = await jobApi.getJobsByServiceIds(selectedServiceIds.value)
  } catch (error) {
    console.error('加载作业列表失败:', error)
    ElMessage.error(t('job.loadJobsFailed'))
  } finally {
    loading.value = false
  }
}

const selectAllServices = () => {
  selectedServiceIds.value = services.value.map(s => s.id)
}

const clearSelectedServices = () => {
  selectedServiceIds.value = []
  jobResponses.value = []
}

const removeService = (serviceId: string) => {
  selectedServiceIds.value = selectedServiceIds.value.filter(id => id !== serviceId)
  // 如果移除后没有选中节点，清空作业数据
  if (selectedServiceIds.value.length === 0) {
    jobResponses.value = []
  }
}

const loadServices = async () => {
  try {
    const svcResult = await serviceApi.getServices()
    services.value = Array.isArray(svcResult) ? svcResult : svcResult.services
  } catch (error) {
    console.error('加载服务列表失败:', error)
  }
}

    const createJob = async () => {
  try {
    await formRef.value.validate()
    creating.value = true

    await jobApi.createJob(createForm.value)
    ElMessage.success(t('job.createSuccess'))
    showCreateDialog.value = false
    loadJobsForSelectedServices()
  } catch (error) {
    if (error !== false) {
      console.error('创建作业失败:', error)
      ElMessage.error(t('job.createFailed'))
    }
  } finally {
    creating.value = false
  }
}

const deleteJob = async (job: any) => {
  try {
    await ElMessageBox.confirm(t('job.confirmDelete', { jobId: job.job_id }), t('common.warning'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })

    await jobApi.deleteJob(job.job_id, job.service_id, job.job_type)
    ElMessage.success(t('job.deleteSuccess'))
    loadJobsForSelectedServices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除作业失败:', error)
      ElMessage.error(t('job.deleteFailed'))
    }
  }
}

const resetForm = () => {
  createForm.value = {
    service_id: '',
    job_type: 'job.common',
    job_id: 1,
    job_pids: [],
    lens: ['proc_collector'],
    slot: 'slot1',
  }
}

onMounted(() => {
  loadServices()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.job-manager {
  padding: 4px;
  height: calc(100vh - 100px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

:deep(.el-card) {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
  min-height: 0;
}

:deep(.el-card__body) {
  padding: 4px;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

@media (max-width: 768px) {
  .job-manager {
    padding: 2px;
    height: calc(100vh - 50px);
  }

  :deep(.el-card__body) {
    padding: 2px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  height: 30px;
  line-height: 30px;
}

.card-title {
  font-size: 15px;
  font-weight: 500;
}

.table-container {
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: overlay;
}

:deep(.filter-bar) {
  margin-bottom: 4px !important;
  gap: 4px;
  flex-wrap: wrap;
  padding: 0 4px;
  display: flex;
  align-items: center;
  min-height: 32px;
}

.result-count {
  margin-left: auto;
  color: var(--el-text-color-primary);
  font-size: 13px;
  white-space: nowrap;
  line-height: 32px;
}

:deep(.el-table) {
  min-width: 700px;
  font-size: 13px;
}

:deep(.el-table .el-table__row) {
  height: 35px;
}

:deep(.el-table .el-table__header-wrapper) {
  margin-bottom: 0;
}

:deep(.el-table .cell) {
  padding: 2px 4px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-item {
  margin-right: 0 !important;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

:deep(.el-pagination) {
  margin-top: 4px;
  padding: 4px;
  justify-content: center;
  height: 32px;
  line-height: 32px;
}

@media (max-width: 768px) {
  .card-title {
    font-size: 13px;
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table .cell) {
    padding: 2px 2px;
  }

  :deep(.el-table .el-table__row) {
    height: 32px;
  }

  .tag-list {
    gap: 2px;
  }

  :deep(.el-tag) {
    margin: 0;
  }

  .filter-bar {
    gap: 2px;
  }

  :deep(.el-pagination) {
    font-size: 12px;
  }
}

:deep(.create-dialog) {
  max-width: 95vw;
}

:deep(.create-dialog .el-dialog__body) {
  padding: 20px 10px;
}
</style>
