<template>
  <div class="service-detail">
    <el-page-header @back="goBack" :content="t('service.detailTitle')" />

    <el-row :gutter="isMobile ? 10 : 20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="16" :lg="16" :xl="16">
        <el-card>
          <template #header>
            <span class="card-title">{{ t('service.basicInfo') }}</span>
          </template>
          <el-descriptions :column="isMobile ? 1 : 2" border>
            <!-- 第 1 行 -->
            <el-descriptions-item :label="t('service.name')">{{ service.name }}</el-descriptions-item>
            <el-descriptions-item :label="t('service.host')">{{ service.host }}</el-descriptions-item>

            <!-- 第 2 行 -->
            <el-descriptions-item :label="t('service.port')">{{ service.port }}</el-descriptions-item>
            <el-descriptions-item :label="t('service.version')">{{
              parseBuild(service.version).ver
            }}</el-descriptions-item>

            <!-- 第 3 行 -->
            <el-descriptions-item :label="t('service.buildId')">{{
              parseBuild(service.version).bid
            }}</el-descriptions-item>
            <el-descriptions-item :label="t('service.buildTime')">{{
              parseBuild(service.version).btime
            }}</el-descriptions-item>

            <!-- 第 4 行 -->
            <el-descriptions-item :label="t('service.status')">
              <el-tag :type="service.status === 'healthy' ? 'success' : 'danger'" size="small">
                {{ service.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="t('common.lastHeartbeat')">{{
              formatDate(service.last_heartbeat)
            }}</el-descriptions-item>

            <!-- 第 5 行：模式和角色 -->
            <el-descriptions-item :label="t('service.mode')">
              <el-tag v-if="service.mode" type="info" size="small">{{ service.mode }}</el-tag>
              <span v-else class="empty-field">-</span>
              <el-button type="text" @click="editMode" style="margin-left: 8px">{{ t('service.editAttributes') }}</el-button>
            </el-descriptions-item>
            <el-descriptions-item :label="t('service.role')">
              <el-tag v-if="service.role_id" type="info" size="small">{{getRoleName(service.role_id)}}</el-tag>
              <span v-else class="empty-field">-</span>
              <el-button type="text" @click="editRole" style="margin-left: 8px">{{ t('service.editAttributes') }}</el-button>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span class="card-title">{{ t('service.healthStatus') }}</span>
          </template>
          <el-descriptions :column="isMobile ? 1 : 2" border v-if="health">
            <el-descriptions-item :label="t('service.registryStatus')">
              <el-tag :type="health.registry_healthy ? 'success' : 'danger'" size="small">
                {{ health.registry_healthy ? t('common.healthy') : t('common.unhealthy') }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="t('service.collectorStatus')">
              <el-tag :type="health.collector_healthy ? 'success' : 'danger'" size="small">
                {{ health.collector_healthy ? t('common.healthy') : t('common.unhealthy') }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8" :lg="8" :xl="8">
        <el-card>
          <template #header>
            <span class="card-title">{{ t('service.jobCount') }}</span>
          </template>
          <div v-if="jobCount">
            <div class="stat-item">
              <div class="stat-label">{{ t('service.totalJobs') }}</div>
              <div class="stat-value">{{ jobCount.job_count }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">{{ t('service.running') }}</div>
              <div class="stat-value running">{{ t('service.notAvailable') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">{{ t('service.completed') }}</div>
              <div class="stat-value completed">{{ t('service.notAvailable') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">{{ t('service.failed') }}</div>
              <div class="stat-value failed">{{ t('service.notAvailable') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="isMobile ? 10 : 20" style="margin-top: 20px">
      <!-- 左侧：采集器性能（不动） -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <span class="card-title">{{ t('service.collectorPerf') }}</span>
          </template>
          <div class="table-wrapper">
            <el-table
              :data="collectorPerfList"
              style="width: 100%"
              :size="isMobile ? 'small' : 'default'"
            >
              <el-table-column prop="name" :label="t('common.name')" min-width="120" show-overflow-tooltip />
              <el-table-column :label="t('service.callCnt')" width="90">
                <template #default="{ row }">
                  {{ row.call_cnt.toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.errCnt')" width="90">
                <template #default="{ row }">
                  {{ row.err_cnt.toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.avgLatency')" width="110">
                <template #default="{ row }">
                  {{ (row.mean_us / 1000).toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.maxLatency')" width="110">
                <template #default="{ row }">
                  {{ (row.max_us / 1000).toFixed(2) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：Writer 拆成两张表 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <span class="card-title">{{ t('service.writerPerf') }}</span>
          </template>
          <div class="table-wrapper">
            <el-table
              :data="writerPerfList"
              style="width: 100%"
              :size="isMobile ? 'small' : 'default'"
            >
              <el-table-column prop="name" :label="t('common.name')" min-width="120" show-overflow-tooltip />
              <el-table-column :label="t('service.callCnt')" width="90">
                <template #default="{ row }">
                  {{ row.call_cnt.toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.errCnt')" width="90">
                <template #default="{ row }">
                  {{ row.err_cnt.toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.avgLatency')" width="110">
                <template #default="{ row }">
                  {{ (row.mean_us / 1000).toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column :label="t('service.maxLatency')" width="110">
                <template #default="{ row }">
                  {{ (row.max_us / 1000).toFixed(2) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>

  <!-- 编辑服务属性对话框 -->
  <el-dialog
    v-model="showEditDialog"
    :title="editDialogTitle"
    :width="isMobile ? '90%' : '500px'"
  >
    <el-form :model="editForm" label-width="100px">
      <!-- 仅编辑模式时显示 -->
      <el-form-item v-if="editTarget === 'mode' || editTarget === 'both'" :label="t('service.mode')">
        <el-select
          v-model="editForm.mode"
          :placeholder="t('config.modePlaceholder')"
          clearable
          filterable
          style="width: 100%"
          :loading="loadingModes"
          :filter-method="filterModes"
        >
          <el-option
            v-for="mode in filteredModeOptions"
            :key="mode.name"
            :label="mode.name"
            :value="mode.name"
          >
            <span>{{ mode.name }}</span>
            <el-tag v-if="mode.default" type="warning" size="small" style="margin-left: 8px">{{ t('service.default') }}</el-tag>
          </el-option>
        </el-select>
      </el-form-item>
      
      <!-- 仅编辑角色时显示 -->
      <el-form-item v-if="editTarget === 'role' || editTarget === 'both'" :label="t('service.role')">
        <el-select
          v-model="editForm.role_id"
          :placeholder="t('service.selectRole')"
          clearable
          filterable
          style="width: 100%"
          :loading="loadingRoles"
          :filter-method="filterRoles"
        >
          <el-option
            v-for="role in filteredRoleOptions"
            :key="role.role_id"
            :label="role.name"
            :value="role.role_id"
          >
            <span>{{ role.name }}</span>
            <el-tag v-if="role.default" type="warning" size="small" style="margin-left: 8px">{{ t('service.default') }}</el-tag>
          </el-option>
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showEditDialog = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="saveServiceAttributes" :loading="saving">
        {{ t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { i18n } from '@/locales'
import { useRouter } from 'vue-router'
import { useIntervalFn } from '@vueuse/core'
import { dayjs, ElMessage } from 'element-plus'
import { serviceApi, jobApi, metricsApi, modesApi, rolesApi } from '@/api'
import type {
  ServiceInfo,
  ServiceHealth,
  ServiceMetrics,
  JobCount,
  WriterPerf,
  CollectorPerf,
  ModeInfo,
  RoleInfo,
} from '@/api'

const { t } = useI18n()
const router = useRouter()
const props = defineProps<{
  id: string
}>()

const service = ref<ServiceInfo>({} as ServiceInfo)
const health = ref<ServiceHealth>({} as ServiceHealth)
const metrics = ref<ServiceMetrics>({} as ServiceMetrics)
const jobCount = ref<JobCount>({} as JobCount)
const isMobile = ref(window.innerWidth <= 768)
const collectorPerfList = ref<CollectorPerf[]>([])
const writerPerfList = ref<WriterPerf[]>([])

// 筛选选项缓存（全局静态，避免重复拉取）
const filterOptionsCache = {
  data: {
    modes: [] as string[],
    roles: [] as Array<{ id: string; name: string }>,
  },
  loaded: false,
  loading: false,
}

// 筛选选项（用于获取角色名称）
const filterOptions = ref({
  modes: [] as string[],
  roles: [] as Array<{ id: string; name: string }>,
})
const loadingFilterOptions = ref(false)

// 编辑相关变量
const showEditDialog = ref(false)
const editDialogTitle = ref(t('service.editServiceAttr'))
const editTarget = ref<'mode' | 'role' | 'both'>('both')
const editForm = ref({
  mode: '',
  role_id: '',
})
const modeOptions = ref<ModeInfo[]>([])
const roleOptions = ref<RoleInfo[]>([])
const filteredModeOptions = ref<ModeInfo[]>([])
const filteredRoleOptions = ref<RoleInfo[]>([])
const modeSearchKeyword = ref('')
const roleSearchKeyword = ref('')
const loadingModes = ref(false)
const loadingRoles = ref(false)
const saving = ref(false)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

const loadData = async () => {
  try {
    const [serviceData, healthData, metricsData, jobCountData] = await Promise.all([
      serviceApi.getService(props.id),
      serviceApi.getServiceHealth(props.id),
      metricsApi.getAllMetrics(props.id),
      jobApi.getJobCount(props.id),
    ])

    service.value = serviceData
    health.value = healthData
    metrics.value = metricsData
    jobCount.value = jobCountData
    writerPerfList.value = await metricsApi.getWriterPerformance(props.id)
    collectorPerfList.value = await metricsApi.getCollectorPerformance(props.id)
  } catch (error) {
    console.error('加载服务详情失败:', error)
    ElMessage.error(t('common.loadFailed'))
  }
}

// 加载筛选选项（用于获取角色名称）- 使用缓存避免重复拉取
const loadFilterOptions = async () => {
  // 如果已经加载过，直接使用缓存
  if (filterOptionsCache.loaded) {
    filterOptions.value = { ...filterOptionsCache.data }
    return
  }
  
  // 如果正在加载中，等待完成
  if (filterOptionsCache.loading) {
    return
  }
  
  filterOptionsCache.loading = true
  loadingFilterOptions.value = true
  
  try {
    // 直接调用 modesApi 和 rolesApi 获取筛选选项
    const [modesResponse, rolesResponse] = await Promise.all([
      modesApi.getModes(), // 获取所有模式
      rolesApi.getRoles(), // 获取所有角色
    ])
    
    // 更新缓存
    filterOptionsCache.data = {
      modes: modesResponse.modes.map(mode => mode.name),
      roles: rolesResponse.roles.map(role => ({
        id: role.role_id,
        name: role.name,
      })),
    }
    filterOptionsCache.loaded = true
    
    // 更新响应式变量
    filterOptions.value = { ...filterOptionsCache.data }
  } catch (error) {
    console.error('加载筛选选项失败:', error)
    ElMessage.error(t('common.loadFailed'))
  } finally {
    filterOptionsCache.loading = false
    loadingFilterOptions.value = false
  }
}

// 根据角色ID获取角色名称
const getRoleName = (roleId: string): string => {
  if (!roleId) return '-'
  const role = filterOptions.value.roles.find((r) => r.id === roleId)
  if (role) return role.name
  // 如果选项还没加载完，显示简短提示
  if (!filterOptionsCache.loaded) return t('common.loading')
  // 加载完成后仍没找到，显示ID前8位
  return roleId.substring(0, 8)
}

const goBack = () => {
  router.back()
}

// 编辑模式
const editMode = async () => {
  // 重置搜索关键词
  modeSearchKeyword.value = ''
  
  // 加载模式选项
  await loadModeOptions()
  
  // 设置当前值
  editForm.value = {
    mode: service.value.mode || '',
    role_id: service.value.role_id || '',
  }
  
  // 设置对话框标题和编辑类型
  editDialogTitle.value = t('config.editMode')
  editTarget.value = 'mode'
  
  showEditDialog.value = true
}

// 编辑角色
const editRole = async () => {
  // 重置搜索关键词
  roleSearchKeyword.value = ''
  
  // 加载角色选项
  await loadRoleOptions()
  
  // 设置当前值
  editForm.value = {
    mode: service.value.mode || '',
    role_id: service.value.role_id || '',
  }
  
  // 设置对话框标题和编辑类型
  editDialogTitle.value = t('service.editRole')
  editTarget.value = 'role'
  
  showEditDialog.value = true
}

// 加载模式选项
const loadModeOptions = async () => {
  loadingModes.value = true
  try {
    const response = await modesApi.getModes()
    modeOptions.value = response.modes
    filteredModeOptions.value = response.modes
  } catch (error) {
    console.error('加载模式列表失败:', error)
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loadingModes.value = false
  }
}

// 加载角色选项
const loadRoleOptions = async () => {
  loadingRoles.value = true
  try {
    const response = await rolesApi.getRoles()
    roleOptions.value = response.roles
    filteredRoleOptions.value = response.roles
  } catch (error) {
    console.error('加载角色列表失败:', error)
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loadingRoles.value = false
  }
}

// 过滤模式选项
const filterModes = (keyword: string) => {
  modeSearchKeyword.value = keyword
  if (!keyword) {
    filteredModeOptions.value = modeOptions.value
  } else {
    const lowerKeyword = keyword.toLowerCase()
    filteredModeOptions.value = modeOptions.value.filter(mode =>
      mode.name.toLowerCase().includes(lowerKeyword)
    )
  }
}

// 过滤角色选项
const filterRoles = (keyword: string) => {
  roleSearchKeyword.value = keyword
  if (!keyword) {
    filteredRoleOptions.value = roleOptions.value
  } else {
    const lowerKeyword = keyword.toLowerCase()
    filteredRoleOptions.value = roleOptions.value.filter(role =>
      role.name.toLowerCase().includes(lowerKeyword)
    )
  }
}

// 保存服务属性
const saveServiceAttributes = async () => {
  saving.value = true
  try {
    // 根据编辑类型决定保存哪些字段
    const attributes: { mode?: string; role_id?: string } = {}
    
    if (editTarget.value === 'mode' || editTarget.value === 'both') {
      attributes.mode = editForm.value.mode || undefined
    }
    
    if (editTarget.value === 'role' || editTarget.value === 'both') {
      attributes.role_id = editForm.value.role_id || undefined
    }
    
    await serviceApi.updateServiceAttributes(props.id, attributes)
    ElMessage.success(t('common.saveSuccess'))
    showEditDialog.value = false
    // 重新加载服务数据
    loadData()
  } catch (error: unknown) {
    console.error('更新服务属性失败:', error)
    const axiosError = error as { response?: { data?: { detail?: string } } }
    const errorMessage = axiosError.response?.data?.detail || t('common.saveFailed')
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString(i18n.global.locale.value === 'zh-CN' ? 'zh-CN' : 'en-US')
}

function parseBuild(str = '') {
  const m = str.match(/^(\S+)\s+(\S+)\s+(.+)$/)
  if (!m) return { ver: '', bid: '', btime: '' }

  // 转格式 2025/12/16 16:51:44
  const formatTime = dayjs((m[3] || '').replace('CST', '')).format('YYYY/MM/DD HH:mm:ss')

  return {
    ver: m[1],
    bid: m[2],
    btime: formatTime,
  }
}

onMounted(() => {
  loadData()
  loadFilterOptions() // 加载筛选选项，用于获取角色名称
  window.addEventListener('resize', handleResize)
  const { pause } = useIntervalFn(async () => {
    try {
      const [metricsData, jobCountData] = await Promise.all([
        metricsApi.getAllMetrics(props.id),
        jobApi.getJobCount(props.id),
      ])
      metrics.value = metricsData
      jobCount.value = jobCountData
      /* 如果后端把 WriterPerf 单独放了一个接口，也在这里一起拉 */
      writerPerfList.value = await metricsApi.getWriterPerformance(props.id)
      collectorPerfList.value = await metricsApi.getCollectorPerformance(props.id)
    } catch (e) {
      console.error('定时刷新失败:', e)
    }
  }, 5000)
  onUnmounted(() => pause())
})
</script>

<style scoped>
.service-detail {
  padding: 20px;
}

@media (max-width: 768px) {
  .service-detail {
    padding: 10px;
  }
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .card-title {
    font-size: 14px;
  }
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

@media (max-width: 768px) {
  .stat-label {
    font-size: 12px;
  }
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

@media (max-width: 768px) {
  .stat-value {
    font-size: 20px;
  }
}

.stat-value.running {
  color: #67c23a;
}

.stat-value.completed {
  color: #409eff;
}

.stat-value.failed {
  color: #f56c6c;
}

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

:deep(.el-descriptions-item__label) {
  width: 120px;
}

@media (max-width: 768px) {
  :deep(.el-descriptions-item__label) {
    width: 100px;
    font-size: 12px;
  }

  :deep(.el-descriptions-item__content) {
    font-size: 12px;
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table .cell) {
    padding: 4px;
  }
}

.empty-field {
  color: #909399;
  font-style: italic;
}
</style>
