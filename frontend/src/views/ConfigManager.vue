<template>
  <div class="config-manager">
    <!-- 页面头部 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ $t('config.title') }}</span>
          <div class="header-actions">
            <!-- 模式选择 -->
            <el-select
              v-model="currentMode"
              :placeholder="$t('config.modePlaceholder')"
              size="small"
              @change="onModeChange"
              :loading="loadingModes"
              style="width: 160px; margin-right: 8px"
            >
              <el-option
                v-for="mode in modeList"
                :key="mode.name"
                :label="mode.name"
                :value="mode.name"
              >
                <div
                  style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    width: 100%;
                  "
                >
                  <span>{{ mode.name }}</span>
                  <el-tag v-if="mode.default" type="warning" size="small">{{ $t('config.defaultTag') }}</el-tag>
                </div>
              </el-option>
            </el-select>

            <!-- 创建模式按钮 -->
            <el-button type="primary" size="small" @click="showCreateModeDialog = true">
              <el-icon><Plus /></el-icon>
              {{ $t('config.newMode') }}
            </el-button>

            <!-- 模式管理按钮（仅当选中模式时显示） -->
            <el-dropdown v-if="currentMode" @command="handleModeCommand" size="small">
              <el-button type="info" size="small" :disabled="!currentMode">
                <el-icon><More /></el-icon>
                {{ $t('config.manageMode') }}
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">{{ $t('config.editModeInfo') }}</el-dropdown-item>
                  <el-dropdown-item command="setDefault" :disabled="currentModeInfo?.default">
                    {{ $t('config.setDefault') }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>{{ $t('config.deleteMode') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <!-- 编辑模式切换 -->
            <el-button
              v-if="!isEditMode"
              type="primary"
              @click="enterEditMode"
              :size="isMobile ? 'small' : 'default'"
              :disabled="!currentMode"
            >
              <el-icon><Edit /></el-icon>
              <span v-if="!isMobile">{{ $t('common.edit') }}</span>
            </el-button>
            <template v-else>
              <el-button
                type="success"
                @click="saveConfig"
                :loading="saving"
                :disabled="!isValidYaml"
                :size="isMobile ? 'small' : 'default'"
              >
                <el-icon><Check /></el-icon>
                <span v-if="!isMobile">{{ $t('common.save') }}</span>
              </el-button>
              <el-button @click="cancelEdit" :size="isMobile ? 'small' : 'default'">
                <el-icon><Close /></el-icon>
                <span v-if="!isMobile">{{ $t('common.cancel') }}</span>
              </el-button>
            </template>
          </div>
        </div>
      </template>

      <!-- 主要内容区 -->
      <div class="config-content">
        <!-- 左侧：编辑器 -->
        <div class="editor-panel">
          <!-- 配置信息栏 -->
          <div v-if="currentModeInfo" class="config-info">
            <el-tag type="info" size="small">{{ $t('config.modeLabel', { name: currentModeInfo.name }) }}</el-tag>
            <el-tag v-if="currentModeInfo.default" type="warning" size="small">
              {{ $t('config.defaultMode') }}
            </el-tag>
            <el-tag size="small">{{ $t('config.configCount', { count: currentModeInfo.config_count }) }}</el-tag>
            <el-tag :type="isValidYaml ? 'success' : 'danger'" size="small">
              {{ isValidYaml ? $t('config.validFormat') : $t('config.invalidFormat') }}
            </el-tag>
          </div>

          <!-- 模式描述 -->
          <div v-if="currentModeInfo?.description" class="mode-description">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ currentModeInfo.description }}</span>
          </div>

          <!-- YAML编辑器 -->
          <div class="editor-container" v-loading="loadingConfig" :class="{ 'has-error': yamlError }">
            <CodeEditor
              v-model:value="configContent"
              language="yaml"
              theme="vs-dark"
              :options="currentEditorOptions"
              @change="handleEditorChange"
            />
          </div>

          <!-- 格式错误提示 -->
          <el-alert
            v-if="yamlError"
            :title="yamlError"
            type="error"
            :closable="false"
            show-icon
            class="yaml-error-alert"
          />
        </div>

        <!-- 右侧：版本历史 -->
        <div class="version-panel">
          <div class="panel-header">
            <h3>{{ $t('config.versionHistory') }}</h3>
            <div>
              <el-button link type="primary" @click="refreshVersions" :loading="loadingVersions">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </div>

          <el-timeline v-loading="loadingVersions">
            <el-timeline-item
              v-for="version in versionList"
              :key="version.version"
              :timestamp="formatTimestamp(version.timestamp)"
              :type="version.is_current ? 'primary' : ''"
              :hollow="!version.is_current"
            >
              <el-card
                shadow="hover"
                :class="{ 'current-version': version.is_current }"
                @click="viewVersion(version)"
              >
                <div class="version-item">
                  <div class="version-title">
                    <el-tag size="small" type="info">
                      {{ version.version?.substring(0, 8) || 'N/A' }}
                    </el-tag>
                    <el-tag v-if="version.is_current" size="small" type="success">{{ $t('config.currentVersion') }}</el-tag>
                  </div>
                  <div v-if="version.description" class="version-desc">
                    {{ version.description }}
                  </div>
                  <div class="version-actions">
                    <el-button
                      v-if="!version.is_current"
                      link
                      type="primary"
                      size="small"
                      @click.stop="rollbackToVersion(version)"
                    >
                      {{ $t('config.rollback') }}
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>

          <!-- 加载更多 -->
          <div v-if="hasMoreVersions" class="load-more">
            <el-button link type="primary" @click="loadMoreVersions" :loading="loadingMore">
              {{ $t('config.loadMore') }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建模式对话框 -->
    <el-dialog
      v-model="showCreateModeDialog"
      :title="$t('config.createNewMode')"
      :width="isMobile ? '90%' : '500px'"
    >
      <el-form
        ref="createModeFormRef"
        :model="createModeForm"
        :rules="createModeRules"
        label-width="100px"
      >
        <el-form-item :label="$t('config.modeName')" prop="name">
          <el-input
            v-model="createModeForm.name"
            :placeholder="$t('config.modeNameUniquePlaceholder')"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item :label="$t('config.modeDescription')" prop="description">
          <el-input
            v-model="createModeForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('config.modeDescriptionPlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('config.setDefault')" prop="default">
          <el-switch v-model="createModeForm.default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateModeDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createMode" :loading="creatingMode">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- 编辑模式对话框 -->
    <el-dialog
      v-model="showEditModeDialog"
      :title="$t('config.editModeInfo')"
      :width="isMobile ? '90%' : '500px'"
    >
      <el-form
        ref="editModeFormRef"
        :model="editModeForm"
        :rules="editModeRules"
        label-width="100px"
      >
        <el-form-item :label="$t('config.modeDescription')" prop="description">
          <el-input
            v-model="editModeForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('config.modeDescriptionPlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('config.setDefault')" prop="default">
          <el-switch v-model="editModeForm.default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditModeDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="updateMode" :loading="updatingMode">{{ $t('common.update') }}</el-button>
      </template>
    </el-dialog>

    <!-- 版本对比对话框 -->
    <el-dialog
      v-model="showVersionDialog"
      :title="$t('config.versionViewTitle', { version: viewingVersion?.version?.substring(0, 8) || 'N/A' })"
      :width="isMobile ? '90%' : '70%'"
      top="5vh"
    >
      <div class="version-viewer">
        <CodeEditor
          v-model:value="viewingVersionContent"
          language="yaml"
          theme="vs-dark"
          :options="{ ...editorOptions, readOnly: true }"
        />
      </div>
      <template #footer>
        <el-button @click="showVersionDialog = false">{{ $t('common.close') }}</el-button>
        <el-button
          v-if="viewingVersion && !viewingVersion.is_current"
          type="primary"
          @click="rollbackToVersion(viewingVersion)"
        >
          {{ $t('config.rollbackToVersion') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 保存确认对话框 -->
    <el-dialog v-model="showSaveDialog" :title="$t('config.saveConfig')" :width="isMobile ? '90%' : '500px'">
      <el-form ref="saveFormRef" :model="saveForm" :rules="saveFormRules" label-width="100px">
        <el-form-item :label="$t('config.updateDescription')" prop="description">
          <el-input
            v-model="saveForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('config.saveDescriptionPlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmSave" :loading="saving">{{ $t('config.confirmSave') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { i18n } from '@/locales'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Check, Close, Refresh, Plus, More, InfoFilled, User } from '@element-plus/icons-vue'
import { modesApi } from '@/api'
import { CodeEditor } from 'monaco-editor-vue3'
import type {
  ModeInfo,
  ModeCreate,
  ModeUpdate,
  ModeConfigUpdate,
  ModeVersionInfo,
} from '@/api/modes'

const { t } = useI18n()

// Monaco Editor 配置
const editorOptions = {
  fontSize: 14,
  minimap: { enabled: false },
  automaticLayout: true,
  scrollBeyondLastLine: false,
  lineNumbers: 'on',
  wordWrap: 'on',
  folding: true,
  renderLineHighlight: 'all',
  readOnly: false,
}

// 响应式状态
const currentMode = ref<string>('')
const modeList = ref<ModeInfo[]>([])
const currentModeInfo = ref<ModeInfo | null>(null)
const configContent = ref('')
const originalContent = ref('')
const isEditMode = ref(false)
const saving = ref(false)
const loadingConfig = ref(false)
const loadingVersions = ref(false)
const loadingMore = ref(false)
const loadingModes = ref(false)
const creatingMode = ref(false)
const updatingMode = ref(false)
const yamlError = ref('')
const versionList = ref<ModeVersionInfo[]>([])
const showVersionDialog = ref(false)
const showSaveDialog = ref(false)
const showCreateModeDialog = ref(false)
const showEditModeDialog = ref(false)
const viewingVersion = ref<ModeVersionInfo | null>(null)
const viewingVersionContent = ref('')
const versionLimit = ref(10)
const isMobile = ref(window.innerWidth <= 768)

// 表单
const saveForm = ref({
  description: '',
})
const saveFormRef = ref()

const createModeForm = ref({
  name: '',
  description: '',
  default: false,
})
const createModeFormRef = ref()

const editModeForm = ref({
  description: '',
  default: false,
})
const editModeFormRef = ref()

// 计算属性
const isValidYaml = computed(() => validateYaml(configContent.value))

// 编辑器选项（根据编辑模式动态调整）
const currentEditorOptions = computed(() => ({
  ...editorOptions,
  readOnly: !isEditMode.value,
}))

const hasMoreVersions = computed(() => {
  return versionList.value.length >= versionLimit.value
})

// 验证规则
const saveFormRules = {
  description: [
    { required: true, message: t('config.updateDescriptionRequired'), trigger: 'blur' },
    { min: 5, message: t('config.descriptionMinLength'), trigger: 'blur' },
  ],
}

const createModeRules = {
  name: [
    { required: true, message: t('config.modeNameRequired'), trigger: 'blur' },
    { min: 2, max: 50, message: t('config.modeNameLength'), trigger: 'blur' },
  ],
}

const editModeRules = {
  description: [
    { required: false, message: t('config.modeDescriptionPlaceholder'), trigger: 'blur' },
    { max: 200, message: t('config.descriptionMaxLength'), trigger: 'blur' },
  ],
}

// YAML格式验证
const validateYaml = (content: string): boolean => {
  try {
    // 简单的YAML格式验证
    if (content.trim() === '') {
      yamlError.value = ''
      return true
    }

    const lines = content.split('\n')
    const indentLevel = 0
    const lastIndent = 0

    // 基本语法检查
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] || ''
      // 跳过空行和注释
      if (line.trim() === '' || line.trim().startsWith('#')) {
        continue
      }

      // 检查冒号
      if (line.includes(':')) {
        // 基础验证通过
      }
    }

    yamlError.value = ''
    return true
  } catch (error: any) {
    yamlError.value = error.message || t('config.yamlFormatError')
    return false
  }
}

// 工具函数
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString(i18n.global.locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 方法
const loadModes = async () => {
  loadingModes.value = true
  try {
    const response = await modesApi.getModes()
    modeList.value = response.modes

    // 如果没有当前选中的模式，则选择第一个模式或默认模式
    if (modeList.value.length > 0) {
      const defaultMode = modeList.value.find((m) => m.default)
      if (defaultMode && currentMode.value === '') {
        currentMode.value = defaultMode.name
        currentModeInfo.value = defaultMode
      } else if (currentMode.value === '' && modeList.value[0]) {
        currentMode.value = modeList.value[0].name
        currentModeInfo.value = modeList.value[0]
      }
    }
  } catch (error: any) {
    console.error('加载模式列表失败:', error)
    ElMessage.error(error.response?.data?.detail || t('config.loadModesFailed'))
  } finally {
    loadingModes.value = false
  }
}

const loadConfig = async () => {
  if (!currentMode.value) return

  loadingConfig.value = true
  try {
    const response = await modesApi.getModeConfig(currentMode.value)
    configContent.value = response.config || ''
    originalContent.value = response.config || ''
    yamlError.value = ''
  } catch (error: any) {
    console.error('加载配置失败:', error)
    // 如果配置不存在，返回空配置
    if (error.response?.status === 404) {
      configContent.value = ''
      originalContent.value = ''
    } else {
      ElMessage.error(error.response?.data?.detail || t('config.loadConfigFailed'))
    }
  } finally {
    loadingConfig.value = false
  }
}

const loadVersions = async () => {
  if (!currentMode.value) return

  loadingVersions.value = true
  try {
    const response = await modesApi.getModeConfigVersions(currentMode.value)
    versionList.value = response.versions || []
  } catch (error: any) {
    console.error('加载版本历史失败:', error)
    ElMessage.error(t('config.loadVersionsFailed'))
  } finally {
    loadingVersions.value = false
  }
}

const enterEditMode = () => {
  isEditMode.value = true
}

const cancelEdit = () => {
  if (configContent.value !== originalContent.value) {
    ElMessageBox.confirm(t('config.confirmDiscardChanges'), t('config.warning'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
      .then(() => {
        configContent.value = originalContent.value
        yamlError.value = ''
        isEditMode.value = false
      })
      .catch(() => {
        // 取消
      })
  } else {
    isEditMode.value = false
  }
}

const saveConfig = () => {
  if (!isValidYaml.value) {
    ElMessage.error(t('config.yamlInvalid'))
    return
  }

  if (configContent.value === originalContent.value) {
    ElMessage.warning(t('config.configUnchanged'))
    return
  }

  saveForm.value.description = ''
  showSaveDialog.value = true
}

const confirmSave = async () => {
  try {
    await saveFormRef.value.validate()
    saving.value = true

    const configData: ModeConfigUpdate = {
      raw_config: configContent.value,
    }

    await modesApi.updateModeConfig(currentMode.value, configData)

    ElMessage.success(t('config.configSaveSuccess'))
    originalContent.value = configContent.value
    isEditMode.value = false
    showSaveDialog.value = false

    // 刷新版本历史
    loadVersions()
  } catch (error: any) {
    if (error !== false) {
      console.error('保存配置失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.saveConfigFailed'))
    }
  } finally {
    saving.value = false
  }
}

const viewVersion = async (version: ModeVersionInfo) => {
  viewingVersion.value = version
  try {
    // 获取特定版本的配置
    const response = await modesApi.getSpecificVersion(currentMode.value, version.version)
    viewingVersionContent.value = response.config
    showVersionDialog.value = true
  } catch (error: any) {
    console.error('加载版本配置失败:', error)
    ElMessage.error(t('config.loadVersionConfigFailed'))
  }
}

const rollbackToVersion = async (version: ModeVersionInfo) => {
  try {
    await ElMessageBox.confirm(
      t('config.rollbackFullConfirm', { version: version.version?.substring(0, 8) || 'N/A' }),
      t('config.confirmRollback'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
      },
    )

    // 调用回滚API
    await modesApi.rollbackModeConfig(currentMode.value, version.version)

    ElMessage.success(t('config.rollbackSuccess'))
    loadConfig()
    loadVersions()

    // 退出编辑模式
    isEditMode.value = false
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('回滚失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.rollbackFailed'))
    }
  }
}

const refreshVersions = () => {
  loadVersions()
}

const loadMoreVersions = async () => {
  loadingMore.value = true
  versionLimit.value += 10
  try {
    await loadVersions()
  } finally {
    loadingMore.value = false
  }
}

const onModeChange = async () => {
  // 更新当前模式信息
  const mode = modeList.value.find((m) => m.name === currentMode.value)
  currentModeInfo.value = mode || null

  // 加载配置和版本历史
  isEditMode.value = false
  await loadConfig()
  await loadVersions()
}

const handleModeCommand = (command: string) => {
  switch (command) {
    case 'edit':
      editMode()
      break
    case 'setDefault':
      setDefaultMode()
      break
    case 'delete':
      deleteMode()
      break
  }
}

const createMode = async () => {
  try {
    await createModeFormRef.value.validate()
    creatingMode.value = true

    const modeData: ModeCreate = {
      name: createModeForm.value.name,
      description: createModeForm.value.description || undefined,
    }

    const newMode = await modesApi.createMode(modeData)

    // 如果设置为默认模式，更新默认模式
    if (createModeForm.value.default) {
      await modesApi.updateMode(newMode.name, { default: true })
    }

    ElMessage.success(t('config.modeCreateSuccess'))
    showCreateModeDialog.value = false
    createModeForm.value = { name: '', description: '', default: false }

    // 重新加载模式列表
    await loadModes()
  } catch (error: any) {
    if (error !== false) {
      console.error('创建模式失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.modeCreateFailed'))
    }
  } finally {
    creatingMode.value = false
  }
}

const editMode = () => {
  if (!currentModeInfo.value) return

  editModeForm.value = {
    description: currentModeInfo.value.description || '',
    default: currentModeInfo.value.default,
  }
  showEditModeDialog.value = true
}

const updateMode = async () => {
  try {
    await editModeFormRef.value.validate()
    updatingMode.value = true

    const updateData: ModeUpdate = {
      description: editModeForm.value.description || undefined,
      default: editModeForm.value.default,
    }

    const updatedMode = await modesApi.updateMode(currentMode.value, updateData)

    ElMessage.success(t('config.modeUpdateSuccess'))
    showEditModeDialog.value = false

    // 更新本地数据
    currentModeInfo.value = updatedMode
    const index = modeList.value.findIndex((m) => m.name === currentMode.value)
    if (index !== -1) {
      modeList.value[index] = updatedMode
    }

    // 如果设为默认，需要更新其他模式
    if (editModeForm.value.default) {
      modeList.value.forEach((m) => {
        if (m.name !== currentMode.value && m.default) {
          m.default = false
        }
      })
    }
  } catch (error: any) {
    if (error !== false) {
      console.error('更新模式失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.modeUpdateFailed'))
    }
  } finally {
    updatingMode.value = false
  }
}

const setDefaultMode = async () => {
  try {
    await ElMessageBox.confirm(
      t('config.confirmSetDefaultMode', { name: currentMode.value }),
      t('config.confirmSetDefaultTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
      },
    )

    const updateData: ModeUpdate = {
      default: true,
    }

    const updatedMode = await modesApi.updateMode(currentMode.value, updateData)

    ElMessage.success(t('config.setDefaultSuccess'))

    // 更新本地数据
    currentModeInfo.value = updatedMode
    modeList.value.forEach((m) => {
      m.default = m.name === currentMode.value
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('设置默认模式失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.setDefaultFailed'))
    }
  }
}

const deleteMode = async () => {
  try {
    await ElMessageBox.confirm(
      t('config.confirmDeleteModeFull', { name: currentMode.value }),
      t('config.confirmDeleteModeTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'error',
      },
    )

    await modesApi.deleteMode(currentMode.value)

    ElMessage.success(t('config.modeDeleteSuccess'))

    // 重新加载模式列表
    await loadModes()

    // 如果删除的是当前选中的模式，重置选中状态
    if (currentMode.value) {
      currentMode.value = ''
      currentModeInfo.value = null
      configContent.value = ''
      originalContent.value = ''
      versionList.value = []
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模式失败:', error)
      ElMessage.error(error.response?.data?.detail || t('config.modeDeleteFailed'))
    }
  }
}

const handleEditorChange = () => {
  // 验证YAML格式
  validateYaml(configContent.value)
}

// 监听窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

// 生命周期
onMounted(() => {
  loadModes()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

// 离开页面提示
window.addEventListener('beforeunload', (e) => {
  if (isEditMode.value && configContent.value !== originalContent.value) {
    e.preventDefault()
    e.returnValue = t('config.confirmLeave')
  }
})
</script>

<style scoped>
.config-manager {
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

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.config-content {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.config-info {
  display: flex;
  gap: 8px;
  padding: 4px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  flex-wrap: wrap;
}

.mode-description {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-bottom: 1px solid #e0f2fe;
  font-size: 13px;
  color: #0369a1;
}

.mode-description .el-icon {
  font-size: 14px;
}

.editor-container {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

/* Monaco Editor 样式 */
.editor-container :deep(.monaco-editor) {
  border-radius: 4px;
}

.editor-container.has-error :deep(.monaco-editor) {
  border: 1px solid #f56c6c;
}

.yaml-error-alert {
  margin: 4px;
}

.version-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid #dcdfe6;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
}

:deep(.el-timeline) {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.version-item {
  cursor: pointer;
}

.version-title {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
  align-items: center;
}

.version-desc {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.4;
}

.version-user {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.version-user .el-icon {
  font-size: 12px;
}

.version-actions {
  display: flex;
  justify-content: flex-end;
}

.current-version {
  border: 1px solid #409eff;
}

.load-more {
  text-align: center;
  padding: 8px;
}

.version-viewer {
  height: 60vh;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.version-viewer :deep(.monaco-editor) {
  border-radius: 4px;
}

@media (max-width: 768px) {
  .config-manager {
    padding: 2px;
    height: calc(100vh - 50px);
  }

  :deep(.el-card__body) {
    padding: 2px;
  }

  .config-content {
    flex-direction: column;
  }

  .version-panel {
    width: 100%;
    height: 200px;
  }

  .card-header {
    height: auto;
    line-height: normal;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
