<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  const authCode = route.query.auth_code as string
  if (!authCode) {
    ElMessage.error('支付宝授权失败：未收到授权码')
    return router.replace('/login')
  }
  try {
    await userStore.alipayLogin(authCode)
    ElMessage.success('登录成功')
    router.replace('/home')
  } catch {
    ElMessage.error('支付宝登录失败，请重试')
    router.replace('/login')
  }
})
</script>

<template>
  <div class="callback-wrap">
    <div class="callback-card">
      <div class="spinner"></div>
      <p>正在完成支付宝登录...</p>
    </div>
  </div>
</template>

<style scoped>
.callback-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: var(--c-bg); }
.callback-card { text-align: center; padding: 40px; }
.callback-card p { margin-top: 16px; font-size: 16px; color: var(--c-ink-700); }
.spinner { width: 40px; height: 40px; margin: 0 auto; border: 4px solid var(--c-ink-100); border-top-color: var(--c-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
