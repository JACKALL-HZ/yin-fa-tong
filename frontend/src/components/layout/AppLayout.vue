<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'
import { searchApi } from '@/api/search'
import { msgApi } from '@/api/message'
import type { SearchResultItem } from '@/types'
import SearchDropdown from '@/components/search/SearchDropdown.vue'

const app = useAppStore()
const user = useUserStore()
const router = useRouter()
const route = useRoute()
const isListening = ref(false)
const unreadCount = ref(0)
const searchKeyword = ref('')
const showDropdown = ref(false)
const searchLoading = ref(false)
const searchResults = ref<SearchResultItem[]>([])
const searchError = ref(false)

const menuItems = [
  { path: '/home', label: '首页' },
  { path: '/hospitals', label: '预约挂号', hot: true },
  { path: '/guide', label: '智能导诊' },
  { path: '/volunteers', label: '陪诊服务' },
  { path: '/elders', label: '亲情账号' },
  { path: '/profile', label: '我的档案' },
]

function isActive(path: string) {
  if (path === '/home') return route.path === '/home'
  return route.path.startsWith(path)
}

function toggleVoice() {
  isListening.value = !isListening.value
  if (isListening.value) {
    setTimeout(() => {
      isListening.value = false
      router.push('/guide')
    }, 2000)
  }
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
let abortController: AbortController | null = null

function goSearch() {
  const kw = searchKeyword.value.trim()
  if (!kw) {
    showDropdown.value = false
    return
  }

  if (debounceTimer) clearTimeout(debounceTimer)

  debounceTimer = setTimeout(async () => {
    // 取消上一次未完成的请求，防止旧响应覆盖新结果
    if (abortController) abortController.abort()
    abortController = new AbortController()

    searchLoading.value = true
    showDropdown.value = true
    searchError.value = false
    try {
      const res = await searchApi.search(kw, 'all', abortController.signal)
      searchResults.value = res.data.data.results
      searchError.value = false
    } catch (err: any) {
      if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
        searchResults.value = []
        searchError.value = true
      }
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

function onResultSelect(_item: SearchResultItem) {
  showDropdown.value = false
  searchKeyword.value = ''
  searchResults.value = []
}

function onDropdownClose() {
  showDropdown.value = false
}

async function fetchUnread() {
  if (!user.isLoggedIn) return
  try {
    const r = await msgApi.unreadCount()
    const d = r.data?.data as any
    unreadCount.value = d?.count || 0
  } catch { /* 静默 */ }
}

let unreadTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchUnread()
  unreadTimer = setInterval(fetchUnread, 30000)
})

onUnmounted(() => {
  if (unreadTimer) clearInterval(unreadTimer)
  if (debounceTimer) clearTimeout(debounceTimer)
  if (abortController) abortController.abort()
})
</script>

<template>
  <div :class="{ 'elder-mode': app.isElderMode }" class="app-shell">
    <!-- 顶部运营条 -->
    <div class="topbar">
      <div class="topbar-inner">
        <div class="topbar-left">
          <span class="live-dot"></span>
          <span class="topbar-notice">适老化就医服务 · 数字鸿沟解决方案</span>
        </div>
        <div class="topbar-right">
          <span class="hotline">📞 24h 客服 400-888-0001</span>
          <a href="#" class="topbar-link">下载 App</a>
          <button class="mode-toggle" @click="app.toggleMode()">
            {{ app.isElderMode ? '标准版' : '长辈版' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 主导航 -->
    <header class="main-nav">
      <div class="nav-inner">
        <div class="brand" @click="router.push('/home')">
          <img src="/logo.jpg" alt="银发通" class="brand-logo-img" />
          <span class="brand-zh">银发通</span>
          <span class="brand-stamp brush">适老</span>
          <span class="brand-en display">YINFA-TONG</span>
        </div>

        <nav class="nav-menu">
          <a
            v-for="item in menuItems"
            :key="item.path"
            :class="{ active: isActive(item.path) }"
            @click="router.push(item.path)"
          >
            {{ item.label }}
            <span v-if="item.hot" class="hot-badge">HOT</span>
          </a>
        </nav>

        <div class="nav-tools">
          <div class="search-box">
            <input
              v-model="searchKeyword"
              placeholder="搜索医院、科室、医生…"
              @input="goSearch"
              @keyup.enter="goSearch"
              @focus="searchKeyword && goSearch()"
              @keyup.escape="showDropdown = false"
            />
            <span class="search-icon" @click="goSearch">🔍</span>
            <SearchDropdown
              :visible="showDropdown"
              :results="searchResults"
              :keyword="searchKeyword"
              :loading="searchLoading"
              :error="searchError"
              @close="onDropdownClose"
              @select="onResultSelect"
            />
          </div>
          <template v-if="user.isLoggedIn">
            <button class="btn-outline-sm msg-btn" @click="router.push('/messages'); fetchUnread()">
              📬
              <span v-if="unreadCount > 0" class="msg-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
            <div class="user-chip" @click="router.push('/profile')">
              <span class="chip-av">{{ (user.info?.nickname || user.info?.username || '我').charAt(0) }}</span>
            </div>
          </template>
          <template v-else>
            <button class="btn-primary-sm" @click="router.push('/login')">登录</button>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* === Top 运营条 === */
.topbar {
  background: var(--c-ink-900);
  border-bottom: 1px solid rgba(194,136,64,.3);
  color: rgba(255,247,232,.85);
  font-size: 12px;
  font-weight: 700;
  position: sticky; top: 0; z-index: 1001;
}
.topbar-inner {
  max-width: 1320px; margin: 0 auto; padding: 0 32px;
  display: flex; justify-content: space-between; align-items: center;
  height: 32px;
}
.topbar-left, .topbar-right { display: flex; align-items: center; gap: 16px; }
.live-dot {
  width: 6px; height: 6px; background: var(--c-gold); border-radius: 50%;
  animation: pulse 1.5s infinite;
}
.hotline { color: var(--c-gold); }
.topbar-link { color: rgba(255,247,232,.7); text-decoration: none; font-size: 12px; }
.topbar-link:hover { color: var(--c-gold); }
.mode-toggle {
  background: var(--c-primary); color: var(--c-cream); border: none;
  padding: 2px 10px; border-radius: var(--r-pill); font-size: 11px;
  font-weight: 700; cursor: pointer; letter-spacing: 1px;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }

/* === 主导航 === */
.main-nav {
  background: linear-gradient(135deg, var(--c-accent), #2F6B53);
  border-bottom: 3px solid var(--c-gold);
  box-shadow: 0 6px 24px rgba(0,0,0,.25);
  position: sticky; top: 32px; z-index: 1000;
}
.main-nav::before {
  content: ""; position: absolute; left: 0; right: 0; top: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(194,136,64,.6), transparent);
}
.nav-inner {
  max-width: 1320px; margin: 0 auto; padding: 0 32px;
  display: flex; align-items: center; height: 64px; gap: 24px;
}

/* 品牌 */
.brand {
  display: flex; flex-direction: column; gap: 1px; cursor: pointer; flex-shrink: 0;
  position: relative; align-items: center; flex-direction: row; gap: 10px;
}
.brand-logo-img {
  width: 36px; height: 36px; border-radius: 8px; object-fit: cover;
}
.brand-zh {
  font-family: "Noto Serif SC", serif; font-weight: 900; font-size: 22px;
  color: #FFF7E8; letter-spacing: 3px; line-height: 1.2;
}
.brand-stamp {
  display: inline-block; font-size: 12px; color: #FFF7E8; background: var(--c-primary);
  padding: 1px 8px; border-radius: 4px; transform: rotate(-2deg); letter-spacing: 1px;
  position: absolute; top: 0; right: -52px;
}
.brand-en {
  font-size: 10px; color: var(--c-gold); letter-spacing: 2px;
}
.brand { position: relative; }

/* 菜单 */
.nav-menu {
  display: flex; gap: 4px; flex: 1; justify-content: center;
}
.nav-menu a {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; cursor: pointer; color: rgba(255,247,232,.65);
  font-size: 14px; font-weight: 700; border-radius: 10px;
  transition: all .2s; border: 1px solid transparent;
  text-decoration: none; white-space: nowrap;
}
.nav-menu a:hover {
  color: #FFF7E8; background: rgba(255,247,232,.08);
  border-color: rgba(255,247,232,.15);
}
.nav-menu a.active {
  color: #FFF7E8; background: var(--c-primary);
  border-color: rgba(255,247,232,.25);
  box-shadow: 0 4px 14px -4px rgba(184,69,31,.6);
}
.hot-badge {
  font-family: "Bebas Neue", sans-serif; font-size: 10px; color: var(--c-gold);
  background: rgba(0,0,0,.3); padding: 1px 5px; border-radius: 4px;
  letter-spacing: 1px;
}

/* 工具区 */
.nav-tools {
  display: flex; align-items: center; gap: 12px; flex-shrink: 0;
}
.search-box {
  display: flex; align-items: center; background: rgba(255,247,232,.12);
  border: 1px solid rgba(255,247,232,.2); border-radius: var(--r-pill);
  padding: 0 14px; height: 38px; gap: 6px;
}
.search-box input {
  background: none; border: none; outline: none; color: #FFF7E8;
  font-size: 13px; width: 160px;
}
.search-box input::placeholder { color: rgba(255,247,232,.5); }
.search-icon { cursor: pointer; font-size: 16px; opacity: .8; }

.btn-primary-sm {
  padding: 8px 18px; border-radius: var(--r-pill);
  background: var(--c-primary); color: var(--c-cream);
  font-weight: 700; font-size: 13px; border: none; cursor: pointer;
  letter-spacing: 1px;
}
.btn-outline-sm {
  width: 38px; height: 38px; border-radius: 50%;
  background: rgba(255,247,232,.08); border: 1px solid rgba(255,247,232,.2);
  color: #FFF7E8; font-size: 18px; cursor: pointer; display: flex;
  align-items: center; justify-content: center;
}
.msg-btn { position: relative; }
.msg-badge {
  position: absolute; top: -4px; right: -4px;
  min-width: 18px; height: 18px; padding: 0 5px;
  background: #f56c6c; color: #fff; font-size: 11px; font-weight: 700;
  border-radius: 9px; display: flex; align-items: center; justify-content: center;
  line-height: 1; box-shadow: 0 0 0 2px #1a1a2e;
}

.user-chip { cursor: pointer; }
.chip-av {
  width: 38px; height: 38px; border-radius: 50%;
  background: var(--c-primary); color: var(--c-cream);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 16px;
}

/* === 内容 === */
.app-main {
  min-height: calc(100vh - 96px);
}
</style>
