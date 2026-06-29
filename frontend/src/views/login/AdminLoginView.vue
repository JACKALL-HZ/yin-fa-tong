<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value) return ElMessage.warning('请输入管理员账号')
  if (!password.value) return ElMessage.warning('请输入密码')
  loading.value = true
  try {
    await userStore.adminLogin(username.value, password.value)
    if (!userStore.isAdmin) {
      ElMessage.error('该账号不是管理员')
      userStore.logout()
      return
    }
    ElMessage.success('管理员登录成功')
    router.push('/admin')
  } catch (e: any) {
    ElMessage.error(e?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login-scene">
    <div class="admin-login-card">
      <div class="admin-head">
        <div class="badge">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <h2>管理员登录</h2>
        <p>银发通后台管理系统</p>
      </div>

      <div class="field">
        <div class="row">
          <span class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="8" r="4" />
              <path d="M4 21v-1a8 8 0 0 1 16 0v1" />
            </svg>
          </span>
          <input v-model="username" type="text" placeholder="管理员账号" @keyup.enter="handleLogin" />
        </div>
      </div>

      <div class="field">
        <div class="row">
          <span class="ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2V6a5 5 0 0 0-5-5zM9 6a3 3 0 0 1 6 0v3H9V6z" />
            </svg>
          </span>
          <input v-model="password" type="password" placeholder="登录密码" @keyup.enter="handleLogin" />
        </div>
      </div>

      <button class="submit" :disabled="loading" @click="handleLogin">
        {{ loading ? '登录中...' : '管理员登录' }}
      </button>

      <div class="foot">
        <a href="javascript:void(0)" @click="router.push('/login')">← 返回用户登录</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-scene {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.admin-login-card {
  width: 420px;
  background: #fff;
  border-radius: 20px;
  padding: 48px 40px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.admin-head {
  text-align: center;
  margin-bottom: 36px;
}

.admin-head .badge {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #1a1a2e, #0f3460);
  color: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.admin-head .badge svg {
  width: 32px;
  height: 32px;
}

.admin-head h2 {
  font-size: 24px;
  font-weight: 800;
  color: #1a1a2e;
  margin-bottom: 6px;
}

.admin-head p {
  font-size: 14px;
  color: #94a3b8;
}

.field {
  margin-bottom: 16px;
}

.field .row {
  display: flex;
  align-items: center;
  height: 56px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 0 16px;
  transition: all 0.2s;
}

.field .row:focus-within {
  border-color: #0f3460;
  box-shadow: 0 0 0 4px rgba(15, 52, 96, 0.1);
}

.field .row .ic {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #94a3b8;
  margin-right: 12px;
}

.field .row .ic svg {
  width: 100%;
  height: 100%;
}

.field .row input {
  flex: 1;
  border: 0;
  background: transparent;
  outline: 0;
  font-size: 16px;
  color: #1a1a2e;
  font-weight: 600;
}

.field .row input::placeholder {
  color: #cbd5e1;
  font-weight: 500;
}

.submit {
  width: 100%;
  height: 56px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #1a1a2e, #0f3460);
  color: #e2e8f0;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: 4px;
  cursor: pointer;
  margin-top: 8px;
  transition: all 0.2s;
}

.submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(15, 52, 96, 0.4);
}

.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.foot {
  text-align: center;
  margin-top: 24px;
}

.foot a {
  color: #94a3b8;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.foot a:hover {
  color: #0f3460;
}
</style>
