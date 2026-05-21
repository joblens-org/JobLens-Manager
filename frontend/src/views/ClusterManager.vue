<template>
  <div class="cluster-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ $t('cluster.title') }}</span>
          <div class="header-actions">
            <el-button :icon="Refresh" @click="loadClusters" :loading="loading">{{ $t('common.refresh') }}</el-button>
          </div>
        </div>
      </template>

      <div class="content-area" v-loading="loading">
        <el-row :gutter="20">
          <!-- 左侧：集群树 -->
          <el-col :span="isMobile ? 24 : 10">
            <div class="tree-panel">
              <div class="tree-search">
                <el-input
                  v-model="searchKeyword"
                  :placeholder="$t('common.search')"
                  clearable
                  :prefix-icon="Search"
                  :size="isMobile ? 'small' : 'default'"
                />
              </div>

              <div class="tree-container" v-if="filteredTreeData.length > 0">
                <el-tree
                  ref="treeRef"
                  :data="filteredTreeData"
                  :props="treeProps"
                  node-key="id"
                  highlight-current
                  :expand-on-click-node="true"
                  @node-click="handleNodeClick"
                  :default-expand-all="!isMobile"
                >
                  <template #default="{ data }">
                    <div class="tree-node-content">
                      <template v-if="data.type === 'cluster'">
                        <el-tag :type="getClusterTypeTag(data.clusterType)" size="small" class="cluster-type-tag">
                          {{ data.clusterType }}
                        </el-tag>
                        <span class="node-label">{{ data.label }}</span>
                        <el-tag v-if="data.missingCount > 0" type="warning" size="small" effect="dark">
                          {{ $t('cluster.missingBadge', { n: data.missingCount }) }}
                        </el-tag>
                        <el-tag v-if="!data.enabled" type="danger" size="small" effect="plain">{{ $t('common.disabled') }}</el-tag>
                      </template>
                      <template v-else>
                        <el-icon class="tag-icon"><Link /></el-icon>
                        <span class="node-label tag-label">{{ data.label }}</span>
                      </template>
                    </div>
                  </template>
                </el-tree>
              </div>

              <el-empty v-else :description="$t('common.noData')" :image-size="80" />

              <div class="tree-summary" v-if="clusters.length > 0">
                {{ $t('cluster.summary', { clusters: totalClusters, tags: totalTags, missing: clustersWithMissing }) }}
              </div>
            </div>
          </el-col>

          <!-- 右侧：配置编辑面板 -->
          <el-col :span="isMobile ? 24 : 14">
            <div class="config-panel" v-if="selectedCluster">
              <div class="config-header">
                <h3 class="config-title">
                  {{ $t('cluster.configTitle') }}
                  <el-tag :type="getClusterTypeTag(selectedCluster.cluster_type)" size="small" class="ml-2">
                    {{ selectedCluster.cluster_type }}
                  </el-tag>
                </h3>
              </div>

              <!-- 缺失必填字段告警 -->
              <el-alert
                v-if="selectedCluster.missing_fields.length > 0"
                type="warning"
                :closable="false"
                show-icon
                class="missing-alert"
              >
                <template #title>
                  <span>{{ $t('cluster.missingAlert', { n: selectedCluster.missing_fields.length, fields: selectedCluster.missing_fields.join(', ') }) }}</span>
                </template>
              </el-alert>

              <!-- 基本信息展示 -->
              <el-descriptions :column="1" border size="small" class="info-descriptions">
                <el-descriptions-item :label="$t('cluster.clusterName')">
                  {{ selectedCluster.cluster_name }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('cluster.clusterType')">
                  {{ selectedCluster.cluster_type }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('cluster.tags')">
                  <el-tag
                    v-for="tag in selectedCluster.tags"
                    :key="tag"
                    size="small"
                    class="tag-item"
                  >
                    {{ tag }}
                  </el-tag>
                  <span v-if="selectedCluster.tags.length === 0" class="text-muted">{{ $t('cluster.noTags') }}</span>
                </el-descriptions-item>
              </el-descriptions>

              <!-- 配置编辑表单 -->
              <el-divider content-position="left">{{ $t('cluster.basicConfig') }}</el-divider>
              <el-form
                :model="configForm"
                label-width="80px"
                label-position="left"
                :size="isMobile ? 'small' : 'default'"
                class="config-form"
              >
                <el-form-item :label="$t('cluster.alias')">
                  <el-input
                    v-model="configForm.alias"
                    :placeholder="$t('cluster.aliasPlaceholder')"
                    clearable
                  />
                </el-form-item>

                <el-form-item :label="$t('cluster.descriptionLabel')">
                  <el-input
                    v-model="configForm.description"
                    type="textarea"
                    :rows="2"
                    :placeholder="$t('cluster.descriptionPlaceholder')"
                  />
                </el-form-item>

                <el-form-item :label="$t('cluster.enable')">
                  <el-switch v-model="configForm.enabled" :active-text="$t('common.enabled')" :inactive-text="$t('common.disabled')" />
                </el-form-item>
              </el-form>

              <!-- 必填字段 -->
              <el-divider content-position="left">{{ $t('cluster.requiredConfig') }}</el-divider>
              <el-form
                :model="extraForm"
                label-width="120px"
                label-position="left"
                :size="isMobile ? 'small' : 'default'"
                class="config-form"
              >
                <el-form-item
                  :class="{ 'required-field': isFieldMissing('es_url') }"
                >
                  <template #label>
                    <span>{{ $t('cluster.field.esUrl') }} <el-tag v-if="isFieldMissing('es_url')" type="danger" size="small">{{ $t('common.required') }}</el-tag></span>
                  </template>
                  <el-input v-model="extraForm.es_url" :placeholder="$t('cluster.placeholder.esUrl')" clearable />
                </el-form-item>

                <el-form-item
                  :class="{ 'required-field': isFieldMissing('es_username') }"
                >
                  <template #label>
                    <span>{{ $t('cluster.field.esUsername') }} <el-tag v-if="isFieldMissing('es_username')" type="danger" size="small">{{ $t('common.required') }}</el-tag></span>
                  </template>
                  <el-input v-model="extraForm.es_username" :placeholder="$t('cluster.placeholder.esUsername')" clearable />
                </el-form-item>

                <el-form-item
                  :class="{ 'required-field': isFieldMissing('es_password') }"
                >
                  <template #label>
                    <span>{{ $t('cluster.field.esPassword') }} <el-tag v-if="isFieldMissing('es_password')" type="danger" size="small">{{ $t('common.required') }}</el-tag></span>
                  </template>
                  <el-input
                    v-model="extraForm.es_password"
                    :type="showPassword ? 'text' : 'password'"
                    :placeholder="$t('cluster.placeholder.esPassword')"
                    clearable
                  >
                    <template #suffix>
                      <el-icon class="password-toggle" @click="showPassword = !showPassword">
                        <View v-if="!showPassword" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                </el-form-item>

                <el-form-item
                  :class="{ 'required-field': isFieldMissing('default_node_port') }"
                >
                  <template #label>
                    <span>{{ $t('cluster.field.defaultNodePort') }} <el-tag v-if="isFieldMissing('default_node_port')" type="danger" size="small">{{ $t('common.required') }}</el-tag></span>
                  </template>
                  <el-input-number
                    v-model="extraForm.default_node_port"
                    :min="0"
                    :max="65535"
                    placeholder="8080"
                    controls-position="right"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item
                  :class="{ 'required-field': isFieldMissing('script_path') }"
                >
                  <template #label>
                    <span>{{ $t('cluster.field.scriptPath') }} <el-tag v-if="isFieldMissing('script_path')" type="danger" size="small">{{ $t('common.required') }}</el-tag></span>
                  </template>
                  <el-input v-model="extraForm.script_path" :placeholder="$t('cluster.placeholder.scriptPath')" clearable />
                </el-form-item>
              </el-form>

              <!-- 自定义扩展配置 -->
              <el-divider content-position="left">{{ $t('cluster.customConfig') }}</el-divider>
              <div class="extra-editor-wrapper">
                <div class="extra-editor-actions">
                  <el-button size="small" @click="formatExtra">{{ $t('cluster.formatJson') }}</el-button>
                  <el-button size="small" type="warning" @click="resetExtra">{{ $t('cluster.resetJson') }}</el-button>
                </div>
                <el-input
                  v-model="extraCustomText"
                  type="textarea"
                  :rows="6"
                  placeholder="{}"
                  class="extra-editor"
                  :class="{ 'json-error': extraError }"
                />
                <div v-if="extraError" class="json-error-msg">
                  {{ extraError }}
                </div>
              </div>

              <div class="form-actions">
                <el-button type="primary" @click="saveConfig" :loading="saving">
                  {{ $t('common.save') }}
                </el-button>
                <el-button @click="resetConfigForm">{{ $t('common.reset') }}</el-button>
              </div>

              <div class="config-meta" v-if="selectedCluster.updated_at">
                {{ $t('cluster.lastUpdate') }}: {{ selectedCluster.updated_at }}
              </div>
            </div>

            <!-- 未选择集群时的占位 -->
            <div v-else class="empty-config">
              <el-empty :description="$t('cluster.selectHint')" :image-size="100" />
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Refresh, Search, Link, View, Hide } from '@element-plus/icons-vue'
import { clusterApi, type ClusterDetail, type ClusterConfigUpdate } from '@/api'

const { t } = useI18n()

const loading = ref(false)
const saving = ref(false)
const clusters = ref<ClusterDetail[]>([])
const selectedCluster = ref<ClusterDetail | null>(null)
const searchKeyword = ref('')
const extraCustomText = ref('{}')
const extraError = ref('')
const showPassword = ref(false)
const isMobile = ref(window.innerWidth <= 768)
const treeRef = ref()

const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  loadClusters()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

const configForm = reactive({
  alias: '',
  description: '',
  enabled: true,
})

const REQUIRED_FIELDS = [
  'es_url', 'es_username', 'es_password',
  'default_node_port', 'script_path',
] as const

interface ExtraFields {
  es_url: string
  es_username: string
  es_password: string
  default_node_port: number
  script_path: string
}

const extraForm = reactive<ExtraFields>({
  es_url: '',
  es_username: '',
  es_password: '',
  default_node_port: 0,
  script_path: '',
})

const treeProps = { children: 'children', label: 'label' }

interface TreeNode {
  id: string
  label: string
  type: 'cluster' | 'tag'
  clusterName: string
  clusterType?: string
  enabled?: boolean
  missingCount?: number
  children?: TreeNode[]
}

const treeData = computed<TreeNode[]>(() => {
  return clusters.value.map((c) => ({
    id: c.cluster_name,
    label: c.alias ? `${c.alias} (${c.cluster_name})` : c.cluster_name,
    type: 'cluster' as const,
    clusterName: c.cluster_name,
    clusterType: c.cluster_type,
    enabled: c.enabled,
    missingCount: c.missing_fields.length,
    children: c.tags.map((tag) => ({
      id: `${c.cluster_name}:${tag}`,
      label: tag,
      type: 'tag' as const,
      clusterName: c.cluster_name,
    })),
  }))
})

const filteredTreeData = computed(() => {
  if (!searchKeyword.value.trim()) return treeData.value
  const kw = searchKeyword.value.toLowerCase()
  return treeData.value.filter(
    (node) =>
      node.clusterName.toLowerCase().includes(kw) ||
      (node.label && node.label.toLowerCase().includes(kw)) ||
      node.children?.some((child) => child.label.toLowerCase().includes(kw)),
  )
})

const totalClusters = computed(() => clusters.value.length)
const totalTags = computed(() => clusters.value.reduce((sum, c) => sum + c.tags.length, 0))
const clustersWithMissing = computed(() => clusters.value.filter((c) => c.missing_fields.length > 0).length)

function getClusterTypeTag(clusterType: string | undefined) {
  if (!clusterType) return 'info'
  const type = clusterType.toLowerCase()
  if (type === 'condor') return ''
  if (type === 'slurm') return 'success'
  return 'info'
}

function isFieldMissing(field: string) {
  return selectedCluster.value?.missing_fields.includes(field) ?? false
}

async function loadClusters() {
  loading.value = true
  try {
    const res = await clusterApi.getClusters()
    clusters.value = res.clusters

    if (selectedCluster.value) {
      const found = res.clusters.find(
        (c) => c.cluster_name === selectedCluster.value!.cluster_name,
      )
      if (found) {
        selectedCluster.value = found
        syncForm()
      } else {
        selectedCluster.value = null
      }
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err?.response?.data?.detail || t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

function handleNodeClick(data: TreeNode) {
  if (data.type === 'cluster') {
    const cluster = clusters.value.find((c) => c.cluster_name === data.clusterName)
    if (cluster) {
      selectedCluster.value = cluster
      syncForm()
    }
  }
}

function syncForm() {
  syncConfigForm()
  syncExtraForm()
}

function syncConfigForm() {
  if (!selectedCluster.value) return
  configForm.alias = selectedCluster.value.alias || ''
  configForm.description = selectedCluster.value.description || ''
  configForm.enabled = selectedCluster.value.enabled !== false
}

function syncExtraForm() {
  showPassword.value = false
  if (!selectedCluster.value) {
    extraForm.es_url = ''
    extraForm.es_username = ''
    extraForm.es_password = ''
    extraForm.default_node_port = 0
    extraForm.script_path = ''
    extraCustomText.value = '{}'
    return
  }

  const extra = selectedCluster.value.extra || {}

  extraForm.es_url = typeof extra.es_url === 'string' ? extra.es_url : ''
  extraForm.es_username = typeof extra.es_username === 'string' ? extra.es_username : ''
  extraForm.es_password = typeof extra.es_password === 'string' ? extra.es_password : ''
  extraForm.default_node_port = typeof extra.default_node_port === 'number' ? extra.default_node_port : 0
  extraForm.script_path = typeof extra.script_path === 'string' ? extra.script_path : ''

  const requiredSet = new Set<string>(REQUIRED_FIELDS)
  const customFields: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(extra)) {
    if (!requiredSet.has(k)) {
      customFields[k] = v
    }
  }
  try {
    extraCustomText.value = JSON.stringify(customFields, null, 2)
  } catch {
    extraCustomText.value = '{}'
  }
  extraError.value = ''
}

function formatExtra() {
  try {
    const parsed = JSON.parse(extraCustomText.value)
    extraCustomText.value = JSON.stringify(parsed, null, 2)
    extraError.value = ''
  } catch (e: unknown) {
    const err = e as Error
    extraError.value = `${t('cluster.jsonError')}: ${err.message}`
  }
}

function resetExtra() {
  extraCustomText.value = '{}'
  extraError.value = ''
}

function resetConfigForm() {
  syncForm()
}

async function saveConfig() {
  if (!selectedCluster.value) return

  // 校验自定义 JSON
  let customObj: Record<string, unknown> = {}
  try {
    customObj = JSON.parse(extraCustomText.value)
  } catch (e: unknown) {
    const err = e as Error
    extraError.value = `${t('cluster.jsonError')}: ${err.message}`
    ElMessage.error(t('cluster.jsonError'))
    return
  }
  extraError.value = ''

  // 合并 7 个必填字段 + 自定义字段
  const mergedExtra: Record<string, unknown> = { ...customObj }
  for (const key of REQUIRED_FIELDS) {
    mergedExtra[key] = extraForm[key]
  }

  saving.value = true
  try {
    const updateData: ClusterConfigUpdate = {
      alias: configForm.alias,
      description: configForm.description,
      enabled: configForm.enabled,
      extra: mergedExtra,
    }

    await clusterApi.updateClusterConfig(selectedCluster.value.cluster_name, updateData)
    ElMessage.success(t('common.saveSuccess'))

    // 刷新选中集群数据
    await loadClusters()
    // 保持选中状态
    const found = clusters.value.find(
      (c) => c.cluster_name === selectedCluster.value!.cluster_name,
    )
    if (found) {
      selectedCluster.value = found
      syncForm()
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    ElMessage.error(err?.response?.data?.detail || t('common.saveFailed'))
  } finally {
    saving.value = false
  }
}

watch(selectedCluster, () => {
  if (selectedCluster.value) {
    syncForm()
  }
})
</script>

<style scoped>
.cluster-manager {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.content-area {
  min-height: 400px;
}

.tree-panel {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  min-height: 300px;
}

.tree-search {
  margin-bottom: 12px;
}

.tree-container {
  max-height: 500px;
  overflow-y: auto;
}

.tree-node-content {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.cluster-type-tag {
  flex-shrink: 0;
}

.node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-label {
  font-size: 13px;
  color: #606266;
}

.tag-icon {
  flex-shrink: 0;
  color: #909399;
  font-size: 14px;
}

.tree-summary {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
  font-size: 13px;
  color: #909399;
  text-align: center;
}

.config-panel {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  min-height: 300px;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

.config-header {
  margin-bottom: 16px;
}

.config-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.ml-2 {
  margin-left: 8px;
}

.missing-alert {
  margin-bottom: 12px;
}

.info-descriptions {
  margin-bottom: 12px;
}

.tag-item {
  margin-right: 6px;
  margin-bottom: 4px;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

.config-form {
  margin-top: 0;
}

.required-field :deep(.el-form-item__label) {
  color: #f56c6c;
  font-weight: 600;
}

.password-toggle {
  cursor: pointer;
  color: #909399;
}

.password-toggle:hover {
  color: #409eff;
}

.extra-editor-wrapper {
  width: 100%;
  margin-bottom: 16px;
}

.extra-editor-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.extra-editor {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
}

.extra-editor.json-error :deep(textarea) {
  border-color: #f56c6c;
  background-color: #fef0f0;
}

.json-error-msg {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.config-meta {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #c0c4cc;
}

.empty-config {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

@media (max-width: 768px) {
  .content-area .el-row {
    flex-direction: column;
  }

  .tree-panel {
    margin-bottom: 16px;
    min-height: 200px;
  }

  .tree-container {
    max-height: 300px;
  }

  .config-panel {
    min-height: auto;
    max-height: none;
  }

  .card-title {
    font-size: 16px;
  }
}
</style>
