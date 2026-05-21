<template>
  <div class="service-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ $t('service.title') }}</span>
        </div>
      </template>

      <div class="filter-section">
        <!-- 搜索框 - 最顶部 -->
        <div class="search-row">
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('service.searchPlaceholder')"
            clearable
            :size="isMobile ? 'small' : 'default'"
            class="search-input-full"
             @keyup.enter="handleSearch"
             @clear="handleSearch"
             @input="handleSearchInput"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 筛选控件行 -->
        <div class="filter-row">
          <div class="filter-group">
            <!-- 模式筛选 -->
            <el-select
              v-model="selectedMode"
              :placeholder="$t('service.filterByMode')"
              clearable
              @change="handleFilterChange"
              :size="isMobile ? 'small' : 'default'"
              class="filter-select"
              :loading="loadingFilterOptions"
            >
              <el-option
                v-for="mode in filterOptions.modes"
                :key="mode"
                :label="mode"
                :value="mode"
              />
            </el-select>

            <!-- 角色筛选 -->
            <el-select
              v-model="selectedRole"
              :placeholder="$t('service.filterByRole')"
              clearable
              @change="handleFilterChange"
              :size="isMobile ? 'small' : 'default'"
              class="filter-select"
              :loading="loadingFilterOptions"
            >
              <el-option
                v-for="role in filterOptions.roles"
                :key="role.id"
                :label="role.name"
                :value="role.id"
              />
            </el-select>
          </div>

          <div class="filter-group">
            <!-- 健康状态筛选 -->
            <el-checkbox-group v-model="healthStatusFilter" @change="handleFilterChange" class="health-checkbox-group">
              <el-checkbox label="healthy">{{ $t('service.healthyOnly') }}</el-checkbox>
              <el-checkbox label="unhealthy">{{ $t('service.unhealthyOnly') }}</el-checkbox>
            </el-checkbox-group>
          </div>

          <div class="filter-group filter-actions">
            <el-button
              type="info"
              @click="resetFilters"
              :size="isMobile ? 'small' : 'default'"
              class="reset-btn"
            >
              <el-icon><Refresh /></el-icon>
              {{ $t('service.resetFilters') }}
            </el-button>
            <el-button
              type="primary"
              @click="loadServices"
              :size="isMobile ? 'small' : 'default'"
              class="refresh-btn"
            >
              <el-icon><Refresh /></el-icon>
              <span v-if="!isMobile">{{ $t('common.refresh') }}</span>
            </el-button>
            <el-button
              type="default"
              @click="loadFilterOptions"
              :loading="loadingFilterOptions"
              :size="isMobile ? 'small' : 'default'"
              class="refresh-filter-btn"
            >
              <el-icon><Refresh /></el-icon>
              {{ $t('service.refreshFilterOptions') }}
            </el-button>
            <el-button
              type="warning"
              @click="handleExportUnhealthy"
              :loading="exporting"
              :size="isMobile ? 'small' : 'default'"
              class="export-btn"
            >
              <el-icon><Download /></el-icon>
              <span v-if="!isMobile">{{ $t('service.exportUnhealthy') }}</span>
            </el-button>
          </div>
        </div>
      </div>

      <div class="table-container">
         <el-table
           v-loading="loading"
           :data="services"
           style="width: 100%"
           @row-click="handleRowClick"
           @sort-change="handleSortChange"
           :size="isMobile ? 'small' : 'default'"
           :default-sort="{ prop: '', order: '' }"
         >
           <!-- <el-table-column prop="id" label="服务ID" min-width="250" :show-overflow-tooltip="true" /> -->
           <el-table-column
             prop="name"
             :label="$t('service.name')"
             min-width="150"
             :show-overflow-tooltip="true"
             sortable="custom"
           />
           <el-table-column
             prop="host"
             :label="$t('service.host')"
             min-width="120"
             :show-overflow-tooltip="true"
             sortable="custom"
           />
           <el-table-column prop="port" :label="$t('service.port')" width="80" sortable="custom" />
           <el-table-column prop="version" :label="$t('service.version')" width="100" sortable="custom">
             <template #default="{ row }">
               {{ parseBuild(row.version).ver }}
             </template>
           </el-table-column>

           <el-table-column prop="build_id" :label="$t('service.buildId')" width="120" sortable="custom">
             <template #default="{ row }">
               {{ parseBuild(row.version).bid }}
             </template>
           </el-table-column>

           <el-table-column prop="build_time" :label="$t('service.buildTime')" min-width="100" sortable="custom">
             <template #default="{ row }">
               {{ parseBuild(row.version).btime }}
             </template>
           </el-table-column>
           <el-table-column prop="mode" :label="$t('service.mode')" width="100" sortable="custom">
             <template #default="{ row }">
               <el-tag v-if="row.mode" type="info" size="small">{{ row.mode }}</el-tag>
               <span v-else class="empty-field">-</span>
             </template>
           </el-table-column>
           <el-table-column prop="role" :label="$t('service.role')" width="120" sortable="custom">
             <template #default="{ row }">
               <el-tag v-if="row.role_id" type="info" size="small">{{
                 getRoleName(row.role_id)
               }}</el-tag>
               <span v-else class="empty-field">-</span>
             </template>
           </el-table-column>
           <el-table-column prop="status" :label="$t('service.status')" width="80" sortable="custom">
             <template #default="{ row }">
               <el-tag :type="row.status == 'healthy' ? 'success' : 'danger'" size="small">
                 {{ row.status }}
               </el-tag>
             </template>
           </el-table-column>
           <el-table-column prop="last_heartbeat" :label="$t('service.lastHeartbeat')" width="160" :show-overflow-tooltip="true" sortable="custom">
             <template #default="{ row }">
               {{ formatDate(row.last_heartbeat) }}
             </template>
           </el-table-column>
           <el-table-column :label="$t('common.operation')" width="160" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  :size="isMobile ? 'small' : 'default'"
                  @click.stop="viewDetails(row.id)"
                  class="action-btn"
                >
                  {{ $t('service.detail') }}
                </el-button>
                <el-button
                  type="danger"
                  :size="isMobile ? 'small' : 'default'"
                  @click.stop="unregisterService(row.id, row.name)"
                  :disabled="row.status !== 'healthy'"
                  class="action-btn"
                >
                  {{ $t('service.unregister') }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页组件 -->
        <el-row justify="center" style="margin-top: 12px">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="totalServices"
            background
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </el-row>
      </div>
    </el-card>

    <!-- 导出不健康节点对话框 -->
    <el-dialog
      v-model="exportDialogVisible"
      :title="$t('service.exportUnhealthyTitle')"
      width="600px"
      destroy-on-close
    >
      <el-input
        v-model="exportResult"
        type="textarea"
        :rows="8"
        readonly
        resize="none"
      />
      <template #footer>
        <el-button @click="exportDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button type="primary" @click="copyExportResult">
          {{ $t('service.copyToClipboard') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { dayjs, ElMessage, ElMessageBox } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { serviceApi, modesApi, rolesApi } from '@/api'
import type { ServiceInfo } from '@/api'
import { useI18n } from 'vue-i18n'
import { i18n } from '@/locales'
import { compactNodeNames } from '@/utils/nodeExport'

const { t } = useI18n()
const router = useRouter()
const services = ref<ServiceInfo[]>([])
const loading = ref(false)
const healthStatusFilter = ref<string[]>([])
const isMobile = ref(window.innerWidth <= 768)
// 筛选相关变量
const filterOptions = ref({
  modes: [] as string[],
  roles: [] as Array<{ id: string; name: string }>,
})
const selectedMode = ref<string>('')
const selectedRole = ref<string>('')
const loadingFilterOptions = ref(false)
let refreshTimer: number | null = null

// 分页相关变量
const currentPage = ref(1)
const pageSize = ref(20)
const totalServices = ref(0)

// 搜索相关变量
const searchKeyword = ref('')
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

// 排序相关变量
const sortBy = ref<string | undefined>(undefined)
const sortOrder = ref<string | undefined>(undefined)

// 导出相关变量
const exporting = ref(false)
const exportDialogVisible = ref(false)
const exportResult = ref('')

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

const loadServices = async () => {
  loading.value = true
  try {
    // 根据 healthStatusFilter 决定筛选参数
    const healthyOnly = healthStatusFilter.value.includes('healthy') && !healthStatusFilter.value.includes('unhealthy')
    const unhealthyOnly = healthStatusFilter.value.includes('unhealthy') && !healthStatusFilter.value.includes('healthy')
    
    const searchParam = searchKeyword.value.trim() || undefined

    const result = await serviceApi.getServices(
      healthyOnly,
      unhealthyOnly,
      selectedMode.value || undefined,
      selectedRole.value || undefined,
      searchParam,
      currentPage.value,
      pageSize.value,
      sortBy.value,
      sortOrder.value,
    )
    
    if (Array.isArray(result)) {
      services.value = result
      totalServices.value = (await serviceApi.getServicesCount(
        healthyOnly,
        unhealthyOnly,
        selectedMode.value || undefined,
        selectedRole.value || undefined,
        searchParam,
      ))
    } else {
      services.value = result.services
      totalServices.value = result.total
    }
  } catch (error) {
    console.error('加载服务列表失败:', error)
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

const loadFilterOptions = async () => {
  loadingFilterOptions.value = true
  try {
    // 直接调用 modesApi 和 rolesApi 获取筛选选项
    const [modesResponse, rolesResponse] = await Promise.all([
      modesApi.getModes(), // 获取所有模式
      rolesApi.getRoles(), // 获取所有角色
    ])
    
    filterOptions.value = {
      modes: modesResponse.modes.map(mode => mode.name),
      roles: rolesResponse.roles.map(role => ({
        id: role.role_id,
        name: role.name,
      })),
    }
  } catch (error) {
    console.error('加载筛选选项失败:', error)
    ElMessage.error(t('common.loadFailed'))
  } finally {
    loadingFilterOptions.value = false
  }
}

const handleFilterChange = () => {
  currentPage.value = 1
  loadServices()
}

const handleSearch = () => {
  currentPage.value = 1
  loadServices()
}

const handleSearchInput = () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadServices()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadServices()
}

const handleSortChange = ({ prop, order }: { prop?: string; order?: string | null }) => {
  if (!prop || !order) {
    sortBy.value = undefined
    sortOrder.value = undefined
  } else {
    sortBy.value = prop
    sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  }
  currentPage.value = 1
  loadServices()
}

const resetFilters = () => {
  selectedMode.value = ''
  selectedRole.value = ''
  healthStatusFilter.value = []
  searchKeyword.value = ''
  loadServices()
}

const getRoleName = (roleId: string): string => {
  const role = filterOptions.value.roles.find((r) => r.id === roleId)
  return role ? role.name : roleId.substring(0, 8)
}

const viewDetails = (serviceId: string) => {
  router.push({
    name: 'service-detail',
    params: { id: serviceId },
  })
}

const unregisterService = async (serviceId: string, serviceName: string) => {
  try {
    await ElMessageBox.confirm(t('service.confirmUnregister', { name: serviceName }), t('common.warning'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })

    await serviceApi.deleteService(serviceId)
    ElMessage.success(t('service.unregisterSuccess'))
    loadServices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(t('service.unregisterFailed'), error)
      ElMessage.error(t('service.unregisterFailed'))
    }
  }
}

const handleRowClick = (row: ServiceInfo) => {
  viewDetails(row.id)
}

const handleExportUnhealthy = async () => {
  exporting.value = true
  try {
    const result = await serviceApi.getServices(
      false,
      true,
      undefined,
      undefined,
      undefined,
      1,
      9999,
    )
    const allServices: ServiceInfo[] = Array.isArray(result) ? result : result.services
    const unhealthyHosts = allServices
      .filter((s) => s.status !== 'healthy')
      .map((s) => s.host)

    if (unhealthyHosts.length === 0) {
      ElMessage.info(t('service.noUnhealthyNodes'))
      return
    }

    const shortNames: string[] = unhealthyHosts.map((host) => host.split('.')[0] ?? host)
    exportResult.value = compactNodeNames(shortNames)
    exportDialogVisible.value = true
  } catch {
    ElMessage.error(t('service.exportFailed'))
  } finally {
    exporting.value = false
  }
}

const copyExportResult = async () => {
  try {
    await navigator.clipboard.writeText(exportResult.value)
    ElMessage.success(t('service.copied'))
  } catch {
    ElMessage.error(t('service.copyFailed'))
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
  Promise.all([loadFilterOptions(), loadServices()])
  refreshTimer = window.setInterval(loadServices, 30000)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.service-list {
  padding: 20px;
}

@media (max-width: 768px) {
  .service-list {
    padding: 10px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

/* 筛选区域样式 */
.filter-section {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

/* 搜索行样式 */
.search-row {
  margin-bottom: 12px;
}

.search-input-full {
  width: 100%;
}

/* 筛选行样式 */
.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-select {
  width: 160px;
}

.health-checkbox-group {
  display: flex;
  gap: 16px;
}

.filter-actions {
  margin-left: auto;
}

.refresh-btn {
  margin-left: 0 !important;
}

.table-container {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

:deep(.el-table) {
  cursor: pointer;
  min-width: 800px;
}

.action-buttons {
  display: flex;
  gap: 5px;
}

@media (max-width: 768px) {
  .card-title {
    font-size: 14px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 2px;
  }

  .action-btn {
    padding: 2px 8px;
    margin-left: 0 !important;
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table .cell) {
    padding: 4px;
  }

  .filter-section {
    padding: 8px;
    margin-bottom: 8px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .filter-group {
    justify-content: center;
  }

  .filter-select {
    width: 140px;
  }

  .health-checkbox-group {
    flex-direction: column;
    gap: 8px;
  }

  .filter-actions {
    margin-left: 0;
    justify-content: center;
  }

  .empty-field {
    color: #909399;
    font-style: italic;
  }
}
</style>
