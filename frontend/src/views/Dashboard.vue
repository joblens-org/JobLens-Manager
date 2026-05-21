<template>
  <div class="dashboard">
    <el-row :gutter="isMobile ? 10 : 20">
      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ $t('dashboard.totalServices') }}</span>
              <el-icon :size="isMobile ? 20 : 24"><Service /></el-icon>
            </div>
          </template>
          <div class="card-value">{{ stats.total_services }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ $t('dashboard.healthyServices') }}</span>
              <el-icon :size="isMobile ? 20 : 24"><SuccessFilled /></el-icon>
            </div>
          </template>
          <div class="card-value healthy">{{ stats.healthy_services }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ $t('dashboard.unhealthyServices') }}</span>
              <el-icon :size="isMobile ? 20 : 24"><WarningFilled /></el-icon>
            </div>
          </template>
          <div class="card-value unhealthy">{{ stats.unhealthy_services }}</div>
        </el-card>
      </el-col>
      <!-- <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">活跃服务</span>
              <el-icon :size="isMobile ? 20 : 24"><CircleCheckFilled /></el-icon>
            </div>
          </template>
          <div class="card-value active">{{ stats.active_services }}</div>
        </el-card>
      </el-col> -->
    </el-row>

    <el-row :gutter="isMobile ? 10 : 20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">{{ $t('dashboard.clusterTags') }}</span>
              <el-tag type="info" effect="plain" size="small">
                {{ $t('dashboard.tagCount', { n: clusterTags.length }) }}
              </el-tag>
            </div>
          </template>
          <div class="cluster-tags-wrapper">
            <el-tag
              v-for="tag in clusterTags"
              :key="tag"
              closable
              disable-transitions
              class="cluster-tag"
              :type="getTagType(tag)"
              effect="plain"
            >
              {{ tag }}
            </el-tag>
            <el-empty v-if="clusterTags.length === 0" :image-size="60" :description="$t('common.noData')" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="isMobile ? 10 : 20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <span class="card-title">{{ $t('dashboard.serviceDistribution') }}</span>
          </template>
          <div ref="serviceChart" :style="{ height: isMobile ? '250px' : '300px' }"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <span class="card-title">{{ $t('dashboard.recentServices') }}</span>
          </template>
          <div class="table-wrapper">
            <el-table :data="recentServices" style="width: 100%">
              <el-table-column
                prop="name"
                :label="$t('common.name')"
                min-width="120"
                :show-overflow-tooltip="true"
              />
              <el-table-column
                prop="host"
                :label="$t('common.host')"
                min-width="100"
                :show-overflow-tooltip="true"
              />
              <el-table-column :label="$t('common.port')" prop="port" width="80" />
              <el-table-column :label="$t('common.status')" width="80" fixed="right">
                <template #default="{ row }">
                  <el-tag :type="row.status == 'healthy' ? 'success' : 'danger'" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { serviceApi, metricsApi } from '@/api'
import type { ServiceInfo, RegistryStats } from '@/api'

const { t } = useI18n()

const tagColors = ['', 'success', 'warning', 'danger', 'info']

function getTagType(tag: string) {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }
  return tagColors[Math.abs(hash) % tagColors.length] as
    | ''
    | 'success'
    | 'warning'
    | 'danger'
    | 'info'
}

const stats = ref<RegistryStats>({
  total_services: 0,
  healthy_services: 0,
  unhealthy_services: 0,
  active_services: 0,
})

const clusterTags = ref<string[]>([])
const recentServices = ref<ServiceInfo[]>([])
const serviceChart = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let refreshTimer: number | null = null
const isMobile = ref(window.innerWidth <= 768)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
  if (chart) {
    chart.resize()
  }
}

const loadData = async () => {
  try {
    const [statsData, servicesData, tagsData] = await Promise.all([
      serviceApi.getRegistryStats(),
      serviceApi.getServices(),
      serviceApi.getClusterTags(),
    ])

    stats.value = statsData
    recentServices.value = (Array.isArray(servicesData) ? servicesData : servicesData.services).slice(0, 5)
    clusterTags.value = tagsData

    updateChart()
  } catch (error) {
    console.error(t('common.loadFailed'), error)
  }
}

const updateChart = () => {
  if (!chart || !serviceChart.value) return

  const option = {
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: isMobile.value ? 'horizontal' : 'vertical',
      left: isMobile.value ? 'center' : 'left',
      bottom: isMobile.value ? 0 : 'auto',
    },
    series: [
      {
        name: t('dashboard.serviceStatus'),
        type: 'pie',
        radius: isMobile.value ? '60%' : '50%',
        center: isMobile.value ? ['50%', '45%'] : ['50%', '50%'],
        data: [
          { value: stats.value.healthy_services, name: t('common.healthy') },
          { value: stats.value.unhealthy_services, name: t('common.unhealthy') },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }

  chart.setOption(option)
}

onMounted(() => {
  loadData()

  if (serviceChart.value) {
    chart = echarts.init(serviceChart.value)
  }

  refreshTimer = window.setInterval(loadData, 30000)
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  if (chart) {
    chart.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .card-title {
    font-size: 14px;
  }

  .stat-card {
    margin-bottom: 10px;
  }

  .stat-card:last-child {
    margin-bottom: 0;
  }
}

.card-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

@media (max-width: 768px) {
  .card-value {
    font-size: 24px;
  }
}

.card-value.healthy {
  color: #67c23a;
}

.card-value.unhealthy {
  color: #f56c6c;
}

.card-value.active {
  color: #409eff;
}

.cluster-tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 40px;
  align-items: center;
}

.cluster-tag {
  font-size: 13px;
  padding: 0 12px;
  height: 28px;
  line-height: 26px;
  border-radius: 14px;
  transition: all 0.2s ease;
}

.cluster-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-wrapper {
  overflow-x: auto;
}

:deep(.el-table) {
  min-width: 400px;
}

@media (max-width: 768px) {
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-table .cell) {
    padding: 4px;
  }
}
</style>
