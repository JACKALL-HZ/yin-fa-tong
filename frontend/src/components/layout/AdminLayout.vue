<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { House, DataAnalysis, OfficeBuilding, Tickets, User, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const user = useUserStore()

const menuItems = [
  { path: '/admin/dashboard', title: '数据看板', icon: DataAnalysis },
  { path: '/admin/hospitals', title: '医院管理', icon: OfficeBuilding },
  { path: '/admin/departments', title: '科室管理', icon: OfficeBuilding },
  { path: '/admin/doctors', title: '医生管理', icon: User },
  { path: '/admin/schedules', title: '排班管理', icon: Tickets },
  { path: '/admin/volunteers', title: '志愿者管理', icon: User },
  { path: '/admin/reserves', title: '挂号管理', icon: Tickets },
  { path: '/admin/accompany', title: '陪诊管理', icon: Tickets },
]
</script>

<template>
  <div class="admin-layout">
    <el-container>
      <el-header class="admin-header">
        <div class="admin-brand" @click="router.push('/admin/dashboard')">
          <img src="/logo.jpg" alt="银发通" class="brand-logo-img" />
          <span class="brand-zh serif">银发通</span>
          <span class="brand-tag">后台管理</span>
        </div>
        <div class="header-actions">
          <el-button text @click="router.push('/home')">
            <el-icon><House /></el-icon> 前台
          </el-button>
          <el-button text @click="user.logout(); router.push('/login')">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside width="220px">
          <el-menu
            :default-active="router.currentRoute.value.path"
            @select="(path: string) => router.push(path)"
          >
            <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
/* Element Plus 主题覆盖 */
.admin-layout {
  --el-color-primary: var(--c-primary);
  --el-color-primary-light-3: var(--c-primary-l);
  --el-color-primary-dark-2: var(--c-primary-d);
  --el-bg-color: var(--c-paper);
  --el-border-color: var(--c-line);
  --el-text-color-primary: var(--c-ink-900);
  --el-text-color-regular: var(--c-ink-700);
  min-height: 100vh;
}

/* Header */
.admin-header {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, var(--c-accent), #2F6B53) !important;
  border-bottom: 3px solid var(--c-gold);
  box-shadow: 0 6px 24px rgba(0,0,0,.25);
  height: 60px !important; padding: 0 24px !important;
}
.admin-header::before {
  content: ""; position: absolute; left: 0; right: 0; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(194,136,64,.6), transparent);
}
.admin-brand {
  display: flex; align-items: center; gap: 12px; cursor: pointer;
}
.brand-logo-img {
  width: 36px; height: 36px; border-radius: 8px; object-fit: cover;
}
.brand-zh {
  font-size: 22px; font-weight: 900; color: #FFF7E8; letter-spacing: 3px;
}
.brand-tag {
  font-size: 12px; color: var(--c-gold); letter-spacing: 1px;
  padding: 2px 10px; border: 1px solid rgba(194,136,64,.4); border-radius: var(--r-pill);
}
.header-actions .el-button { color: rgba(255,247,232,.85); }
.header-actions .el-button:hover { color: var(--c-gold); background: rgba(255,247,232,.08); }

/* Sidebar */
.el-aside {
  background: var(--c-paper) !important;
  border-right: 1px solid var(--c-line) !important;
}
/* 深层覆盖 el-menu 样式 */
.admin-layout :deep(.el-menu) {
  border-right: none !important;
  background: var(--c-paper);
}
.admin-layout :deep(.el-menu-item) {
  font-size: 15px; font-weight: 600; color: var(--c-ink-700);
  height: 52px; line-height: 52px;
}
.admin-layout :deep(.el-menu-item:hover) {
  background: var(--c-primary-bg); color: var(--c-primary);
}
.admin-layout :deep(.el-menu-item.is-active) {
  background: var(--c-primary-bg); color: var(--c-primary);
  border-right: 3px solid var(--c-primary); font-weight: 800;
}

/* Main */
.el-main {
  background: var(--c-bg);
  min-height: calc(100vh - 60px);
}
</style>
