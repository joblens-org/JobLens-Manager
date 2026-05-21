<script setup lang="ts">
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import 'highlight.js/lib/languages/bash'
import { RouterView } from 'vue-router'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion, CopyDocument, MagicStick, Menu, ArrowDown } from '@element-plus/icons-vue'
import { switchLang, i18n } from '@/locales'

const { t } = i18n.global
const currentLang = computed(() => i18n.global.locale.value)
const currentLangLabel = computed(() => currentLang.value === 'zh-CN' ? t('app.langZh') : t('app.langEn'))

function handleLangChange(lang: string) {
  switchLang(lang as 'zh-CN' | 'en')
  location.reload()
}
const isMobile = ref(window.innerWidth <= 960)
const drawerVisible = ref(false)

const handleResize = () => {
  isMobile.value = window.innerWidth <= 960
}

const toggleDrawer = () => {
  drawerVisible.value = !drawerVisible.value
}

const closeDrawer = () => {
  drawerVisible.value = false
}

const headerStyle = computed(() => ({
  backgroundColor: '#409eff',
  color: 'white',
  display: 'flex',
  alignItems: 'center',
  padding: isMobile.value ? '0 15px' : '0 20px',
  height: isMobile.value ? '50px' : '60px',
}))

// const titleStyle = computed(() => ({
//   margin: '0',
//   fontSize: isMobile.value ? '18px' : '24px',
//   fontWeight: 'bold'
// }))

const menuItems = [
  { path: '/', icon: 'Monitor', label: t('nav.dashboard') },
  { path: '/services', icon: 'Service', label: t('nav.services') },
  { path: '/jobs', icon: 'Document', label: t('nav.jobs') },
  { path: '/configs', icon: 'Setting', label: t('nav.configs') },
  { path: '/roles', icon: 'User', label: t('nav.roles') },
  { path: '/clusters', icon: 'Monitor', label: t('nav.clusters') },
]

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

const CMD_InstallJobLens = ref(' wget -qO- <your-server>:8888/joblens/install.sh | bash')

const highlightedCode = computed(() => {
  const result = hljs.highlight(CMD_InstallJobLens.value, {
    language: 'bash',
  })
  return result.value
})

const copyCode = async (code: string) => {
  try {
    await navigator.clipboard.writeText(code as string)
    ElMessage.success(t('common.copySuccess'))
  } catch (err) {
    console.error(t('common.copyFailed'), err)
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = code
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success(t('common.copySuccess'))
  }
}
</script>

<template>
  <el-container style="height: 100vh; width: 100%">
    <!-- 移动端遮罩层 -->
    <div v-if="isMobile && drawerVisible" class="drawer-overlay" @click="closeDrawer"></div>

    <!-- 头部 -->
    <el-header :style="headerStyle" class="custom-header">
      <!-- 左侧区域：移动端菜单按钮和标题 -->
      <div class="header-left">
        <!-- 移动端菜单按钮 -->
        <el-button v-if="isMobile" type="text" class="mobile-menu-btn" @click="toggleDrawer">
          <el-icon><Menu /></el-icon>
        </el-button>

        <!-- 标题 -->
        <h1 class="header-title">{{ t('app.title') }}</h1>
      </div>

      <!-- 右侧区域：操作按钮 -->
      <div class="header-right">
        <!-- 语言切换 -->
        <el-dropdown trigger="click" @command="handleLangChange">
          <el-button text class="lang-btn">
            {{ currentLangLabel }}
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh-CN">🇨🇳 {{ t('app.langZhFull') }}</el-dropdown-item>
              <el-dropdown-item command="en">🇺🇸 {{ t('app.langEnFull') }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <!-- 安装指令弹出框 -->
        <el-popover
          :width="650"
          trigger="click"
          placement="bottom"
          popper-class="code-popover-container"
        >
          <template #reference>
            <el-button type="primary" class="install-instruction-btn" size="large">
              <el-icon class="btn-icon"><Promotion /></el-icon>
              {{ $t('common.installCommand') }}
            </el-button>
          </template>

          <!-- 弹出框内容 -->
          <div class="popover-content">
            <!-- 头部 -->
            <!-- <div class="popover-header">
              <div class="header-left">
                <el-icon class="title-icon"><Document /></el-icon>
                <div class="header-text">
                  <h3 class="popover-title">JobLens 安装指令</h3>
                  <p class="popover-subtitle">默认安装最新版本</p>
                </div>
              </div>
              <el-button
                size="medium"
                type="primary"
                @click="copyCode(CMD_InstallJobLens)"
                class="copy-btn"
                :icon="DocumentCopy"
              >
                复制代码
              </el-button>
            </div> -->

            <!-- 主命令区域 -->
            <div class="primary-command-section">
              <div class="command-header">
                <!-- <el-tag type="success" size="small" effect="dark">主要命令</el-tag> -->
                <span class="command-desc">{{ $t('common.oneClickInstall') }}</span>
              </div>
              <div class="code-block primary-code">
                <div class="code-header">
                  <span class="language-badge">Bash</span>
                  <div class="code-actions">
                    <el-button
                      text
                      size="small"
                      :icon="CopyDocument"
                      @click="copyCode(CMD_InstallJobLens)"
                    >
                      {{ $t('common.copyCode') }}
                    </el-button>
                  </div>
                </div>
                <pre
                  class="code-content"
                ><code class="language-bash" v-html="highlightedCode"></code></pre>
              </div>
            </div>

            <!-- 版本选择区域 -->
            <div class="version-options-section">
              <div class="section-title">
                <el-icon><MagicStick /></el-icon>
                <span>{{ $t('common.versionOptions') }}</span>
              </div>
              <div class="options-grid">
                <div
                  class="option-card"
                  @click="copyCode('wget -qO- <your-server>:8888/joblens/install.sh | bash')"
                >
                  <div class="option-header">
                    <el-tag type="primary" size="small">{{ $t('common.standardVersion') }}</el-tag>
                    <el-icon class="copy-hint"><CopyDocument /></el-icon>
                  </div>
                  <p class="option-desc">{{ $t('common.standardDesc') }}</p>
                  <!-- <code class="option-command">wget -qO- <your-server>:8888/joblens/install.sh | bash</code> -->
                </div>

                <div
                  class="option-card"
                  @click="
                    copyCode('wget -qO- <your-server>:8888/joblens/install.sh | VERSION=test  bash')
                  "
                >
                  <div class="option-header">
                    <el-tag type="warning" size="small">{{ $t('common.testVersion') }}</el-tag>
                    <el-icon class="copy-hint"><CopyDocument /></el-icon>
                  </div>
                  <p class="option-desc">{{ $t('common.testDesc') }}</p>
                  <!-- <code class="option-command">VERSION=test wget -qO- ...</code> -->
                </div>

                <div
                  class="option-card"
                  @click="
                    copyCode(
                      'wget -qO- <your-server>:8888/joblens/install.sh | VERSION=0.0.11  bash',
                    )
                  "
                >
                  <div class="option-header">
                    <el-tag type="info" size="small">{{ $t('common.specVersion') }}</el-tag>
                    <el-icon class="copy-hint"><CopyDocument /></el-icon>
                  </div>
                  <p class="option-desc">{{ $t('common.specDesc') }}</p>
                  <!-- <code class="option-command">VERSION=0.0.11 wget -qO- ...</code> -->
                </div>

                <div
                  class="option-card"
                  @click="
                    copyCode(
                      'wget -qO- <your-server>:8888/joblens/install.sh | DEPLOY_PART=joblens bash',
                    )
                  "
                >
                  <div class="option-header">
                    <el-tag type="success" size="small">{{ $t('common.liteVersion') }}</el-tag>
                    <el-icon class="copy-hint"><CopyDocument /></el-icon>
                  </div>
                  <p class="option-desc">{{ $t('common.liteDesc') }}</p>
                  <!-- <code class="option-command">DEPLOY_PART=joblens wget -qO- ...</code> -->
                </div>
              </div>
            </div>

            <!-- 底部提示 -->
            <div class="popover-footer">
              <el-alert type="info" :closable="false" show-icon class="footer-alert">
                <template #title>
                  <div class="alert-content">
                    <!-- <el-icon><InfoFilled /></el-icon> -->
                    <span>{{ $t('common.clickToCopyTip') }}</span>
                  </div>
                </template>
              </el-alert>
            </div>
          </div>
        </el-popover>
      </div>
    </el-header>

    <el-container>
      <!-- 侧边栏 -->
      <el-aside
        v-if="!isMobile || drawerVisible"
        :width="isMobile ? '70%' : '200px'"
        :class="{ 'mobile-drawer': isMobile }"
        style="background-color: #f0f2f5"
      >
        <el-menu
          router
          default-active="/"
          :style="{ height: '100%' }"
          @select="isMobile && closeDrawer()"
        >
          <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.label }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main :style="{ padding: isMobile ? '10px' : '20px' }">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.full-flex {
  height: 100vh;
  width: 100%; /* 相对于父级 html/body 的 100%，不含滚动条 */
}

body {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
}

.el-main {
  min-width: 0;
  overflow-x: auto;
}

.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.mobile-drawer {
  position: fixed !important;
  top: 50px;
  left: 0;
  bottom: 0;
  z-index: 1000;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

:deep(.el-main) {
  overflow-x: hidden;
}

/* 头部容器样式 */
.custom-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 左侧区域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  color: white !important;
  font-size: 20px;
  padding: 8px;
  transition: all 0.3s ease;
}

.mobile-menu-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

/* 标题样式 */
.header-title {
  margin: 0;
  color: white;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 右侧区域 */
.header-right {
  display: flex;
  align-items: center;
}

.lang-btn {
  color: white !important;
  font-size: 13px;
  margin-right: 8px;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  border-radius: 4px;
}

/* 安装指令按钮 */
.install-instruction-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 14px;
  padding: 8px 20px !important;
  height: 40px;
  transition: all 0.3s ease;
}

.install-instruction-btn .btn-icon {
  font-size: 18px;
}

/* 弹出框容器 */
.code-popover-container {
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 弹出框内容 */
.popover-content {
  padding: 0;
}

/* 弹出框头部 */
.popover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  border-radius: 8px 8px 0 0;
}

.popover-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  color: #2c3e50;
}

/* 复制按钮 */
.copy-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px !important;
}

/* 代码块样式 */
.code-block {
  padding: 20px;
  background: #ffffff8c;
  margin: 0;
  border-radius: 0;
  max-height: 400px;
  overflow-y: auto;
}

.code-block pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.code-block code {
  color: #d4d4d4;
  font-family: inherit;
}

/* 弹出框底部 */
.popover-footer {
  padding: 12px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  border-radius: 0 0 8px 8px;
}

.popover-footer .el-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .custom-header {
    padding: 0 15px;
  }

  .header-title {
    font-size: 18px;
  }

  .install-instruction-btn span:not(.el-icon) {
    display: none;
  }

  .install-instruction-btn .btn-icon {
    margin-right: 0;
  }

  .code-popover-container {
    width: 95vw !important;
    max-width: 95vw;
    margin: 0 2.5vw;
  }
}

/* 弹出框容器 */
.code-popover-container {
  padding: 16px !important;
  border-radius: 12px !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid #e4e7ed;
}

.popover-content {
  font-family:
    'Inter',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
}

/* 头部样式 */
.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #409eff, #337ecc);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.popover-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2d3d;
}

.popover-subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #8492a6;
}

.copy-btn {
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 500;
}

/* 主命令区域 */
.primary-command-section {
  margin-bottom: 24px;
}

.command-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.command-desc {
  color: #5e6c82;
  font-size: 14px;
}

.primary-code {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #ffffff;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #a6b1bd;
  border-bottom: 1px solid #e0e6ed;
}

.language-badge {
  background: #5d6c7d;
  color: rgb(255, 255, 255);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.code-actions .el-button {
  padding: 6px 8px;
  background: #434c54;
  color: #ffffff;
}

.code-content {
  margin: 0;
  padding: 20px;
  background: #434c54;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  overflow-x: auto;
}

/* 版本选项区域 */
.version-options-section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: #1f2d3d;
  font-weight: 600;
  font-size: 15px;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.option-card {
  background: #f8fafc;
  border: 1px solid #e0e6ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.option-card:hover {
  background: #f0f7ff;
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.option-card:hover .copy-hint {
  opacity: 1;
  color: #409eff;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.copy-hint {
  opacity: 0.5;
  transition: all 0.2s ease;
}

.option-desc {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #5e6c82;
}

.option-command {
  display: block;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 11px;
  color: #666;
  background: white;
  padding: 6px 10px;
  border-radius: 4px;
  border: 1px solid #e0e6ed;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 底部提示 */
.footer-alert {
  border-radius: 8px;
  background: #f0f7ff;
  border: 1px solid #d9ecff;
}

.footer-alert .el-alert__title {
  font-size: 13px;
}

.alert-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 按钮样式优化 */
.install-instruction-btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.install-instruction-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.btn-icon {
  margin-right: 6px;
  font-size: 16px;
}
</style>
