<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/locales'

const { t } = i18n.global
const router = useRouter()
const authStore = useAuthStore()

const password = ref('')

async function handleLogin() {
  if (!password.value) return
  const ok = await authStore.login(password.value)
  if (ok) {
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    router.push(redirect)
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">{{ t('app.title') }}</h1>
      <p class="login-subtitle">{{ t('auth.enterPassword') }}</p>

      <el-input
        v-model="password"
        type="password"
        :placeholder="t('auth.password')"
        show-password
        size="large"
        class="login-input"
        @keydown="onKeydown"
        @focus="authStore.clearError()"
      />

      <el-alert
        v-if="authStore.error"
        :title="authStore.error"
        type="error"
        show-icon
        :closable="false"
        class="login-error"
      />

      <el-button
        type="primary"
        size="large"
        :loading="authStore.loading"
        class="login-button"
        @click="handleLogin"
      >
        {{ t('auth.login') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 48px 40px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.login-title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  letter-spacing: 1px;
}

.login-subtitle {
  margin: 0 0 32px;
  font-size: 14px;
  color: #909399;
}

.login-input {
  margin-bottom: 16px;
}

.login-error {
  margin-bottom: 16px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
}
</style>
