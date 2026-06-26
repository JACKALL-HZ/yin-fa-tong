<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const user = useUserStore()
const app = useAppStore()

function handleLogout() {
  user.logout()
  router.push('/login')
}
</script>

<template>
  <div class="page-wrap">
    <div class="profile-card card-xl">
      <div class="avatar">{{ (user.info?.nickname || '用')[0] }}</div>
      <h2 class="serif">{{ user.info?.nickname || '用户' }}</h2>
      <p class="uid">{{ user.info?.username }}</p>
      <span class="pill" :class="user.isAdmin ? 'pill-accent' : 'pill-primary'">
        {{ user.isAdmin ? '管理员' : '普通用户' }}
      </span>
    </div>

    <div class="menu-list card">
      <div class="menu-item" @click="router.push('/profile-info')">
        <span>📝</span> 信息登记 <span class="arrow">→</span>
      </div>
      <div class="menu-item" @click="router.push('/elders')">
        <span>👨‍👩‍👧</span> 长辈管理 <span class="arrow">→</span>
      </div>
      <div class="menu-item" @click="router.push('/orders')">
        <span>📅</span> 我的挂号 <span class="arrow">→</span>
      </div>
      <div class="menu-item" @click="router.push('/accompany-orders')">
        <span>🤝</span> 我的陪诊 <span class="arrow">→</span>
      </div>
      <div class="menu-item" @click="router.push('/messages')">
        <span>🔔</span> 消息中心 <span class="arrow">→</span>
      </div>
      <div class="menu-item" @click="app.toggleMode()">
        <span>🔤</span> 切换{{ app.isElderMode ? '子女' : '长者' }}模式 <span class="arrow">→</span>
      </div>
      <div v-if="user.isAdmin" class="menu-item accent" @click="router.push('/admin/dashboard')">
        <span>⚙️</span> 后台管理 <span class="arrow">→</span>
      </div>
    </div>

    <button class="btn-outline" style="width:100%;height:var(--tap-min);font-size:18px;font-weight:700" @click="handleLogout">退出登录</button>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 720px; margin: 0 auto; padding: 32px 32px 80px; }

.profile-card {
  text-align: center; padding: 40px 20px; margin-bottom: 20px;
}
.avatar {
  width: 88px; height: 88px; border-radius: 50%; margin: 0 auto 14px;
  background: linear-gradient(135deg, var(--c-primary), var(--c-gold));
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 40px; font-weight: 800;
}
.avatar :deep(.serif) { font-family: "Noto Serif SC", serif; }
.profile-card h2 { font-size: 28px; font-weight: 900; color: var(--c-ink-900); margin-bottom: 4px; }
.uid { color: var(--c-ink-500); margin-bottom: 12px; font-size: 16px; }

.menu-list { overflow: hidden; margin-bottom: 20px; padding: 0; }
.menu-item {
  display: flex; align-items: center; gap: 12px; padding: 20px 24px;
  border-bottom: 1px solid var(--c-line); font-size: 20px; font-weight: 600;
  color: var(--c-ink-700); cursor: pointer; transition: .15s;
}
.menu-item:hover { background: var(--c-primary-bg); }
.menu-item:last-child { border-bottom: 0; }
.menu-item .arrow { margin-left: auto; color: var(--c-ink-300); }
.menu-item.accent { color: var(--c-accent); }
</style>
