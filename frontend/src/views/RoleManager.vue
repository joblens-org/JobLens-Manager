<template>
  <div class="role-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="card-title">{{ $t('role.title') }}</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="showCreateRoleDialog = true">
              <el-icon><Plus /></el-icon>
              {{ $t('role.createRole') }}
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="showCreateRuleDialog = true"
              :disabled="!selectedRole"
            >
              <el-icon><Plus /></el-icon>
              {{ $t('role.createRule') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="role-content">
        <!-- 左侧：角色列表 -->
        <div class="role-panel">
          <div class="panel-header">
            <h3>{{ $t('role.roleList') }}</h3>
            <el-button link type="primary" @click="loadRoles" :loading="loadingRoles">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>

          <el-tree
            ref="roleTreeRef"
            :data="roleTreeData"
            node-key="id"
            :props="roleTreeProps"
            :expand-on-click-node="false"
            :highlight-current="true"
            :default-expand-all="true"
            @node-click="onRoleSelect"
            v-loading="loadingRoles"
            class="role-tree"
          >
            <template #default="{ data }">
              <div class="role-node">
                <div class="role-info">
                  <span class="role-name">{{ data.name }}</span>
                  <el-tag
                    v-if="data.default"
                    type="warning"
                    size="small"
                    class="default-tag"
                  >
                    {{ $t('role.default') }}
                  </el-tag>
                  <el-tag
                    v-if="data.parent_role_id"
                    type="info"
                    size="small"
                    @click.stop="jumpToParentRole(data.parent_role_id)"
                    class="inheritance-tag"
                  >
                    {{ $t('role.inheritedFrom') }}{{ getParentRoleName(data.parent_role_id) }}
                  </el-tag>
                </div>
                <div class="role-actions">
                  <el-dropdown @command="handleRoleCommand($event, data)" size="small">
                    <el-button link type="info" size="small">
                      {{ $t('role.manage') }}
                      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">{{ $t('role.editRole') }}</el-dropdown-item>
                        <el-dropdown-item command="setDefault" :disabled="data.default">
                          {{ $t('role.setDefault') }}
                        </el-dropdown-item>
                        <el-dropdown-item command="delete" divided>{{ $t('role.deleteRole') }}</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>
          </el-tree>
        </div>

        <!-- 右侧：规则列表和编辑器 -->
        <div class="rule-panel">
          <div class="panel-header">
            <h3>{{ $t('role.ruleManagement') }}</h3>
            <div v-if="selectedRole" class="selected-role-info">
              <span>{{ $t('role.currentRole') }}<strong>{{ selectedRole.name }}</strong></span>
              <el-tag v-if="selectedRole.parent_role_id" type="info" size="small">
                {{ $t('role.inheritedFrom') }}{{ getParentRoleName(selectedRole.parent_role_id) }}
              </el-tag>
            </div>
          </div>

          <!-- 规则列表 -->
          <div class="rule-list" v-loading="loadingRules">
            <el-table :data="ruleList" @row-click="onRuleSelect" class="rule-table">
              <el-table-column prop="name" :label="$t('role.ruleName')" width="180" />
              <el-table-column prop="rule_id" :label="$t('role.ruleId')" width="120">
                <template #default="{ row }">
                  <span class="rule-id">{{ row.rule_id?.substring(0, 8) }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('common.operation')" width="120">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click.stop="editRule(row)">
                    {{ $t('common.edit') }}
                  </el-button>
                  <el-button link type="danger" size="small" @click.stop="deleteRule(row)">
                    {{ $t('common.delete') }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- Lua规则编辑器 -->
          <div class="rule-editor" v-if="selectedRule">
            <div class="editor-header">
              <span>{{ $t('role.editingRule') }}{{ selectedRule.name }}</span>
              <div class="editor-actions">
                <el-button
                  type="info"
                  size="small"
                  @click="showExampleDialog = true"
                >
                  <el-icon><Document /></el-icon>
                  {{ $t('role.example') }}
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  @click="saveRule"
                  :loading="savingRule"
                  :disabled="!isLuaValid"
                >
                  <el-icon><Check /></el-icon>
                  {{ $t('common.save') }}
                </el-button>
              </div>
            </div>

            <el-tabs v-model="activeTab" class="editor-tabs">
              <el-tab-pane :label="$t('role.edit')" name="edit">
                <div class="editor-container" :class="{ 'has-error': luaError }">
                  <CodeEditor
                    v-model:value="luaContent"
                    language="lua"
                    theme="vs-dark"
                    :options="editorOptions"
                    @change="validateLua(luaContent)"
                  />
                </div>

                <div v-if="luaError" class="lua-error">
                  <el-alert :title="luaError" type="error" :closable="false" show-icon />
                </div>
              </el-tab-pane>

              <el-tab-pane :label="$t('role.preview')" name="preview">
                <div class="preview-container">
                  <pre class="preview-content">{{ luaContent }}</pre>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <div v-else class="rule-placeholder">
            <el-empty :description="$t('role.selectRuleToEdit')" />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建角色对话框 -->
    <el-dialog
      v-model="showCreateRoleDialog"
      :title="$t('role.createRole')"
      :width="isMobile ? '90%' : '500px'"
    >
      <el-form
        ref="createRoleFormRef"
        :model="createRoleForm"
        :rules="createRoleRules"
        label-width="100px"
      >
        <el-form-item :label="$t('role.roleName')" prop="name">
          <el-input v-model="createRoleForm.name" :placeholder="$t('role.roleNamePlaceholder')" maxlength="50" />
        </el-form-item>
        <el-form-item :label="$t('role.roleDesc')" prop="description">
          <el-input
            v-model="createRoleForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('role.roleDescPlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('role.parentRole')" prop="parent_role_id">
          <el-select
            v-model="createRoleForm.parent_role_id"
            :placeholder="$t('role.parentRolePlaceholder')"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="role in roleList"
              :key="role.role_id"
              :label="role.name"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('role.setDefault')" prop="default">
          <el-switch v-model="createRoleForm.default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRoleDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createRole" :loading="creatingRole">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- 编辑角色对话框 -->
    <el-dialog v-model="showEditRoleDialog" :title="$t('role.editRole')" :width="isMobile ? '90%' : '500px'">
      <el-form
        ref="editRoleFormRef"
        :model="editRoleForm"
        :rules="editRoleRules"
        label-width="100px"
      >
        <el-form-item :label="$t('role.roleName')" prop="name">
          <el-input v-model="editRoleForm.name" :placeholder="$t('role.roleNamePlaceholder')" maxlength="50" />
        </el-form-item>
        <el-form-item :label="$t('role.roleDesc')" prop="description">
          <el-input
            v-model="editRoleForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('role.roleDescPlaceholder')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('role.setDefault')" prop="default">
          <el-switch v-model="editRoleForm.default" :disabled="editRoleForm.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditRoleDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="updateRole" :loading="updatingRule">{{ $t('common.update') }}</el-button>
      </template>
    </el-dialog>

    <!-- 创建规则对话框 -->
    <el-dialog
      v-model="showCreateRuleDialog"
      :title="$t('role.createRule')"
      :width="isMobile ? '90%' : '600px'"
    >
      <el-form
        ref="createRuleFormRef"
        :model="createRuleForm"
        :rules="createRuleRules"
        label-position="top"
      >
        <el-form-item :label="$t('role.ruleName')" prop="name">
          <el-input v-model="createRuleForm.name" :placeholder="$t('role.ruleNamePlaceholder')" maxlength="50" />
        </el-form-item>
        <el-form-item :label="$t('role.luaContent')" prop="lua_content">
          <div class="lua-editor-dialog">
            <div class="editor-toolbar">
              <el-button type="primary" size="small" @click="triggerFileUpload">
                <el-icon><Upload /></el-icon>
                {{ $t('role.uploadLuaFile') }}
              </el-button>
              <input
                ref="fileInputRef"
                type="file"
                accept=".lua,.txt"
                style="display: none"
                @change="handleFileUpload"
              />
              <span class="upload-hint">{{ $t('role.fileFormatHint') }}</span>
            </div>
            <div style="height: 300px; border: 1px solid #dcdfe6; border-radius: 4px;">
              <CodeEditor
                v-model:value="createRuleForm.lua_content"
                language="lua"
                theme="vs-dark"
                :options="editorOptions"
              />
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateRuleDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createRule" :loading="creatingRule">{{ $t('common.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
  
  <!-- 示例对话框 -->
  <el-dialog
    v-model="showExampleDialog"
    :title="$t('role.luaExample')"
    :width="isMobile ? '90%' : '700px'"
  >
    <div class="example-content">
      <h4>{{ $t('role.ruleFormatHelp') }}</h4>
      <p>{{ $t('role.ruleRequiredFields') }}</p>
      <ul>
        <li><code>name</code>: {{ $t('role.fieldDesc.name') }}</li>
        <li><code>description</code>: {{ $t('role.fieldDesc.description') }}</li>
        <li><code>priority</code>: {{ $t('role.fieldDesc.priority') }}</li>
        <li><code>condition</code>: {{ $t('role.fieldDesc.condition') }}</li>
      </ul>
      
      <h4>{{ $t('role.exampleCode') }}</h4>
      <pre class="example-code">{{ exampleCode }}</pre>
      
      <h4>{{ $t('role.usageNotes') }}</h4>
      <ul>
        <li v-html="$t('role.usageNote1')"></li>
        <li v-html="$t('role.usageNote2')"></li>
        <li v-html="$t('role.usageNote3')"></li>
      </ul>
    </div>
    
    <template #footer>
      <el-button type="primary" @click="insertExampleCode">{{ $t('role.insertExample') }}</el-button>
      <el-button @click="showExampleDialog = false">{{ $t('common.close') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Check, Upload, Document, ArrowDown } from '@element-plus/icons-vue'
import { rolesApi, rulesApi } from '@/api'
import type { RoleInfo, RoleCreate, RoleUpdate } from '@/api/roles'
import type { RuleInfo, RuleCreate, RuleUpdate } from '@/api/rules'

// Monaco Editor 导入
import { CodeEditor } from 'monaco-editor-vue3'

const { t } = useI18n()


// 角色树节点接口
interface RoleTreeNode extends RoleInfo {
  children: RoleTreeNode[]
}

// API错误接口
interface ApiError {
  response?: {
    data?: {
      detail?: string
    }
  }
}

// 响应式状态
const loadingRoles = ref(false)
const loadingRules = ref(false)
const creatingRole = ref(false)
const updatingRule = ref(false)
const creatingRule = ref(false)
const savingRule = ref(false)
const isMobile = ref(window.innerWidth <= 768)

const roleList = ref<RoleInfo[]>([])
const roleTreeData = ref<RoleTreeNode[]>([])
const selectedRole = ref<RoleInfo | null>(null)
const ruleList = ref<RuleInfo[]>([])
const selectedRule = ref<RuleInfo | null>(null)
const luaContent = ref('')
const luaError = ref('')
const activeTab = ref('edit')

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
}

const showCreateRoleDialog = ref(false)
const showEditRoleDialog = ref(false)
const showCreateRuleDialog = ref(false)
const showExampleDialog = ref(false)

const roleTreeRef = ref()
const createRoleFormRef = ref()
const editRoleFormRef = ref()
const createRuleFormRef = ref()
const fileInputRef = ref<HTMLInputElement>()

// 表单数据
const createRoleForm = ref({
  name: '',
  description: '',
  parent_role_id: '',
  default: false,
})

const editRoleForm = ref({
  name: '',
  description: '',
  default: false,
  isDefault: false,
})

const createRuleForm = ref({
  name: '',
  lua_content: '',
})

// 计算属性
const isLuaValid = computed(() => validateLua(luaContent.value))

// 示例代码
const exampleCode = computed(() => `rule = {
    name = "default rule",
    description = "${t('role.exampleDefaultDesc')}",
    priority = 0,
    condition = function(data)
        return true
    end
}`)

// 示例方法
const insertExampleCode = () => {
  if (selectedRule.value) {
    luaContent.value = exampleCode.value
    showExampleDialog.value = false
    ElMessage.success(t('role.exampleInserted'))
  }
}

// 树配置
const roleTreeProps = {
  children: 'children',
  label: 'name',
}

// 验证规则
const createRoleRules = {
  name: [
    { required: true, message: t('role.validation.roleNameRequired'), trigger: 'blur' },
    { min: 2, max: 50, message: t('role.validation.roleNameLength'), trigger: 'blur' },
  ],
}

const editRoleRules = {
  description: [
    { required: false, message: t('role.roleDescPlaceholder'), trigger: 'blur' },
    { max: 200, message: t('role.validation.roleDescLength'), trigger: 'blur' },
  ],
}

const createRuleRules = {
  name: [
    { required: true, message: t('role.validation.ruleNameRequired'), trigger: 'blur' },
    { min: 2, max: 50, message: t('role.validation.ruleNameLength'), trigger: 'blur' },
  ],
  lua_content: [{ required: true, message: t('role.validation.luaContentRequired'), trigger: 'blur' }],
}

// Lua验证
const validateLua = (content: string): boolean => {
  try {
    // 简单的Lua语法验证
    if (content.trim() === '') {
      luaError.value = ''
      return true
    }

    // 检查基本的Lua语法
    const lines = content.split('\n')
    let bracketCount = 0

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]?.trim() || ''

      // 跳过注释
      if (line.startsWith('--')) {
        continue
      }

      // 检查括号匹配
      for (const char of line) {
        if (char === '(' || char === '{' || char === '[') {
          bracketCount++
        } else if (char === ')' || char === '}' || char === ']') {
          bracketCount--
        }
      }
    }

    if (bracketCount !== 0) {
      luaError.value = t('role.validation.bracketMismatch')
      return false
    }

    // 检查必需字段
    const requiredFields = ['name', 'description', 'priority', 'condition']
    const missingFields: string[] = []

    for (const field of requiredFields) {
      const regex = new RegExp(`${field}\\s*=`, 'i')
      if (!regex.test(content)) {
        missingFields.push(field)
      }
    }

    if (missingFields.length > 0) {
      luaError.value = t('role.ruleValidation.missingFields', { fields: missingFields.join(', ') })
      return false
    }

    // 检查condition函数
    if (!content.includes('condition') || !content.includes('function')) {
      luaError.value = t('role.validation.missingCondition')
      return false
    }

    luaError.value = ''
    return true
  } catch (error: unknown) {
    luaError.value = (error as Error).message || t('role.ruleValidation.syntaxError')
    return false
  }
}

// 方法
const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const response = await rolesApi.getRoles()
    roleList.value = response.roles

    // 构建树形数据 - 所有角色都作为根节点显示
    const treeData: RoleTreeNode[] = []

    response.roles.forEach((role) => {
      const node = {
        ...role,
        id: role.role_id,
        name: role.name,
        children: [],
      }
      treeData.push(node)
    })

    roleTreeData.value = treeData
  } catch (error: unknown) {
    console.error('加载角色列表失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.loadRolesFailed'))
  } finally {
    loadingRoles.value = false
  }
}

const loadRules = async () => {
  if (!selectedRole.value) return

  loadingRules.value = true
  try {
    // 获取角色规则（包括继承的规则）
    const response = await rolesApi.getRoleRules(selectedRole.value.role_id)
    ruleList.value = response.rules || []
    selectedRule.value = null
    luaContent.value = ''
  } catch (error: unknown) {
    console.error('加载规则列表失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.loadRulesFailed'))
  } finally {
    loadingRules.value = false
  }
}

const onRoleSelect = async (data: RoleInfo) => {
  selectedRole.value = data
  await loadRules()
}

const handleRoleCommand = (command: string, role: RoleInfo) => {
  switch (command) {
    case 'edit':
      editRole(role)
      break
    case 'setDefault':
      setDefaultRole(role)
      break
    case 'delete':
      deleteRole(role)
      break
  }
}

const onRuleSelect = (row: RuleInfo) => {
  selectedRule.value = row
  luaContent.value = row.lua_content
  luaError.value = ''
}

const getParentRoleName = (parentRoleId: string): string => {
  const parent = roleList.value.find((r) => r.role_id === parentRoleId)
  return parent?.name || parentRoleId.substring(0, 8)
}

const jumpToParentRole = (parentRoleId: string) => {
  // 查找父角色
  const parentRole = roleList.value.find((r) => r.role_id === parentRoleId)
  if (parentRole) {
    // 选中父角色
    selectedRole.value = parentRole
    // 加载父角色的规则
    loadRules()
    ElMessage.success(t('role.jumpToParent') + parentRole.name)
  } else {
    ElMessage.error(t('role.parentRoleNotFound'))
  }
}

// 角色操作
const createRole = async () => {
  try {
    await createRoleFormRef.value.validate()
    creatingRole.value = true

    const roleData: RoleCreate = {
      name: createRoleForm.value.name,
      description: createRoleForm.value.description || undefined,
      parent_role_id: createRoleForm.value.parent_role_id || undefined,
    }

    const newRole = await rolesApi.createRole(roleData)

    // 如果设置为默认角色，更新默认角色
    if (createRoleForm.value.default) {
      await rolesApi.updateRole(newRole.role_id, { default: true })
    }

    ElMessage.success(t('role.createRoleSuccess'))
    showCreateRoleDialog.value = false
    createRoleForm.value = { name: '', description: '', parent_role_id: '', default: false }

    // 重新加载角色列表
    await loadRoles()
  } catch (error: unknown) {
    console.error('创建角色失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.createRoleFailed'))
  } finally {
    creatingRole.value = false
  }
}

const editRole = (role: RoleInfo) => {
  selectedRole.value = role
  editRoleForm.value = {
    name: role.name,
    description: role.description || '',
    default: role.default,
    isDefault: role.default,
  }
  showEditRoleDialog.value = true
}

const updateRole = async () => {
  if (!selectedRole.value) return

  try {
    await editRoleFormRef.value.validate()
    updatingRule.value = true

    const updateData: RoleUpdate = {
      description: editRoleForm.value.description || undefined,
      default: editRoleForm.value.default,
    }

    const updatedRole = await rolesApi.updateRole(selectedRole.value.role_id, updateData)

    ElMessage.success(t('role.updateRoleSuccess'))
    showEditRoleDialog.value = false

    // 更新本地数据
    selectedRole.value = updatedRole
    await loadRoles()
  } catch (error: unknown) {
    console.error('更新角色失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.updateRoleFailed'))
  } finally {
    updatingRule.value = false
  }
}

const deleteRole = async (role: RoleInfo) => {
  try {
    await ElMessageBox.confirm(
      t('role.confirmDeleteRoleWithRules', { name: role.name }),
      t('role.confirmDeleteRole', { name: role.name }),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'error',
      },
    )
    console.info(role)
    await rolesApi.deleteRole(role.role_id)

    ElMessage.success(t('role.deleteRoleSuccess'))

    // 重新加载角色列表
    await loadRoles()

    // 如果删除的是当前选中的角色，重置选中状态
    if (selectedRole.value?.role_id === role.role_id) {
      selectedRole.value = null
      ruleList.value = []
      selectedRule.value = null
    }
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error((error as ApiError).response?.data?.detail || t('role.deleteRoleFailed'))
    }
  }
}

const setDefaultRole = async (role: RoleInfo) => {
  try {
    await ElMessageBox.confirm(
      t('role.confirmSetDefaultRole', { name: role.name }),
      t('role.confirmSetDefaultRoleTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
      },
    )

    const updateData: RoleUpdate = {
      default: true,
    }

    const updatedRole = await rolesApi.updateRole(role.role_id, updateData)

    ElMessage.success(t('role.setDefaultRoleSuccess'))

    // 重新加载角色列表
    await loadRoles()

    // 如果选中的是当前角色，更新选中状态
    if (selectedRole.value?.role_id === role.role_id) {
      selectedRole.value = updatedRole
    }
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('设置默认角色失败:', error)
      ElMessage.error((error as ApiError).response?.data?.detail || t('role.setDefaultRoleFailed'))
    }
  }
}

// 文件上传相关函数
const triggerFileUpload = () => {
  fileInputRef.value?.click()
}

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) return

  // 检查文件类型
  const allowedExtensions = ['.lua', '.txt']
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()

  if (!allowedExtensions.includes(fileExtension)) {
    ElMessage.error(t('role.unsupportedFileType'))
    return
  }

  // 读取文件内容
  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target?.result as string
    createRuleForm.value.lua_content = content
    ElMessage.success(t('role.fileLoaded'))
  }
  reader.onerror = () => {
    ElMessage.error(t('role.fileReadFailed'))
  }
  reader.readAsText(file)

  // 清空文件输入，允许重复选择同一文件
  input.value = ''
}

// 规则操作
const createRule = async () => {
  if (!selectedRole.value) return

  try {
    await createRuleFormRef.value.validate()
    creatingRule.value = true

    const ruleData: RuleCreate = {
      role_id: selectedRole.value.role_id,
      name: createRuleForm.value.name,
      lua_content: createRuleForm.value.lua_content,
    }

    await rulesApi.createRule(ruleData)

    ElMessage.success(t('role.createRuleSuccess'))
    showCreateRuleDialog.value = false
    createRuleForm.value = { name: '', lua_content: '' }

    // 重新加载规则列表
    await loadRules()
  } catch (error: unknown) {
    console.error('创建规则失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.createRuleFailed'))
  } finally {
    creatingRule.value = false
  }
}

const editRule = (rule: RuleInfo) => {
  selectedRule.value = rule
  luaContent.value = rule.lua_content
  luaError.value = ''
}

const saveRule = async () => {
  if (!selectedRule.value) return

  try {
    if (!isLuaValid.value) {
      ElMessage.error(t('role.luaInvalid'))
      return
    }

    savingRule.value = true

    // 更新现有规则
    const updateData: RuleUpdate = {
      lua_content: luaContent.value,
    }

    await rulesApi.updateRule(selectedRule.value.rule_id, updateData)

    ElMessage.success(t('role.saveRuleSuccess'))

    // 重新加载规则列表
    await loadRules()
  } catch (error: unknown) {
    console.error('保存规则失败:', error)
    ElMessage.error((error as ApiError).response?.data?.detail || t('role.saveRuleFailed'))
  } finally {
    savingRule.value = false
  }
}

const deleteRule = async (rule: RuleInfo) => {
  try {
    await ElMessageBox.confirm(
      t('role.confirmDeleteRule', { name: rule.name }),
      t('role.confirmDeleteRuleTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'error',
      },
    )

    await rulesApi.deleteRule(rule.rule_id)

    ElMessage.success(t('role.deleteRuleSuccess'))

    // 重新加载规则列表
    await loadRules()

    // 如果删除的是当前选中的规则，重置选中状态
    if (selectedRule.value?.rule_id === rule.rule_id) {
      selectedRule.value = null
      luaContent.value = ''
    }
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('删除规则失败:', error)
      ElMessage.error((error as ApiError).response?.data?.detail || t('role.deleteRuleFailed'))
    }
  }
}

// 生命周期
onMounted(() => {
  loadRoles()
})

// 监听窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.role-manager {
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
}

.role-content {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.role-panel {
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
  gap: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
}

.selected-role-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.role-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.role-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.role-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.inheritance-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.inheritance-tag:hover {
  background-color: #409eff !important;
  color: white !important;
}

.role-name {
  font-weight: 500;
}

.role-actions {
  display: flex;
  gap: 2px;
}

.rule-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.rule-list {
  height: 200px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-bottom: 8px;
}

.rule-table {
  width: 100%;
}

.rule-id {
  font-family: 'Consolas', monospace;
  font-size: 12px;
  color: #909399;
}

.rule-editor {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.editor-container {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  border-radius: 4px;
}

/* Monaco Editor 样式 */
.editor-container :deep(.monaco-editor) {
  border-radius: 4px;
}

.editor-container.has-error :deep(.monaco-editor) {
  border: 1px solid #f56c6c;
}

/* Monaco Editor 在对话框中的样式 */
.lua-editor-dialog :deep(.monaco-editor) {
  border-radius: 4px;
}

.lua-error {
  padding: 8px;
  border-top: 1px solid #dcdfe6;
}

.inheritance-info {
  padding: 8px;
  border-top: 1px solid #dcdfe6;
}

.rule-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lua-editor-dialog {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.editor-toolbar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.editor-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-tabs :deep(.el-tabs__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-tabs :deep(.el-tab-pane) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-container {
  flex: 1;
  overflow: auto;
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.preview-content {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.example-content {
  padding: 10px;
}

.example-content h4 {
  margin: 15px 0 10px 0;
  color: #409eff;
}

.example-content ul {
  margin: 10px 0;
  padding-left: 20px;
}

.example-content code {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
}

.example-code {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .role-manager {
    padding: 2px;
    height: calc(100vh - 50px);
  }

  :deep(.el-card__body) {
    padding: 2px;
  }

  .role-content {
    flex-direction: column;
  }

  .role-panel {
    width: 100%;
    height: 200px;
  }

  .card-header {
    height: auto;
    line-height: normal;
  }
}
</style>
