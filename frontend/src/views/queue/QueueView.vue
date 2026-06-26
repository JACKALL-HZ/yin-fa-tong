<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { reserveApi } from '@/api/reserve'
import { queueApi, type QueuePosition } from '@/api/queue'
import type { ReserveOrder } from '@/types'

const router = useRouter()
const orders = ref<ReserveOrder[]>([])
const loading = ref(false)
const now = ref(new Date())
let refreshTimer: ReturnType<typeof setInterval> | undefined
let clockTimer: ReturnType<typeof setInterval> | undefined

// 排队位置缓存 + 展开状态
const queueMap = ref<Record<string, QueuePosition>>({})
const expandedId = ref<number | null>(null)

async function loadOrders() {
  loading.value = true
  try {
    const { data: res } = await reserveApi.listMy({ order_status: 2 })
    if (res.code === 200 && res.data) {
      orders.value = [...res.data].sort((a, b) => {
        const da = (a.work_date || '') + (a.time_period || '')
        const db = (b.work_date || '') + (b.time_period || '')
        return da.localeCompare(db)
      })
      // 加载所有排队信息
      for (const o of orders.value) {
        if (o.queue_code) loadQueue(o.queue_code)
      }
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function loadQueue(code: string) {
  try {
    const { data: res } = await queueApi.myPosition(code)
    if (res.code === 200 && res.data) {
      queueMap.value[code] = res.data
    }
  } catch { /* ignore */ }
}

function toggleExpand(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

onMounted(() => {
  loadOrders()
  refreshTimer = setInterval(loadOrders, 15000)
  clockTimer = setInterval(() => now.value = new Date(), 30000)
})
onUnmounted(() => {
  clearInterval(refreshTimer)
  clearInterval(clockTimer)
})

function padTime(n: number) { return String(n).padStart(2, '0') }
const timeStr = computed(() => `${padTime(now.value.getHours())}:${padTime(now.value.getMinutes())}`)

function fmtDate(d?: string) {
  if (!d) return '—'
  // d = "2026-06-25"
  const parts = d.split('-')
  if (parts.length === 3) return `${parts[1]}月${parts[2]}日`
  return d
}

function isToday(d?: string) {
  if (!d) return false
  const today = new Date()
  const y = today.getFullYear()
  const m = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  return d === `${y}-${m}-${dd}`
}

function isTomorrow(d?: string) {
  if (!d) return false
  const t = new Date()
  t.setDate(t.getDate() + 1)
  const y = t.getFullYear()
  const m = String(t.getMonth() + 1).padStart(2, '0')
  const dd = String(t.getDate()).padStart(2, '0')
  return d === `${y}-${m}-${dd}`
}

function dateLabel(d?: string) {
  if (isToday(d)) return '今天'
  if (isTomorrow(d)) return '明天'
  return fmtDate(d)
}

function statusBadge(o: ReserveOrder) {
  if (o.queue_status === 1) return { text: '候诊中', cls: 'badge-wait' }
  if (o.queue_status === 2) return { text: '正在就诊', cls: 'badge-ing' }
  if (o.order_status === 3) return { text: '已就诊', cls: 'badge-done' }
  return { text: '已预约', cls: 'badge-ok' }
}
</script>

<template>
  <div class="queue-page" v-loading="loading">
    <!-- 顶部状态条 -->
    <div class="queue-topbar">
      <span class="live-dot"></span>
      <span class="live-text">候诊排队</span>
      <span class="topbar-time">{{ timeStr }}</span>
      <span class="topbar-count">共 {{ orders.length }} 个预约</span>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && orders.length === 0" class="empty-card card">
      <span style="font-size:48px;display:block;margin-bottom:12px">📋</span>
      <p style="font-size:18px;font-weight:700;color:var(--c-ink-700);margin-bottom:8px">暂无预约记录</p>
      <p style="color:var(--c-ink-500);margin-bottom:20px">完成挂号支付后，就诊信息将在此显示</p>
      <button class="btn-primary" @click="router.push('/hospitals')">去挂号</button>
    </div>

    <!-- 预约列表 -->
    <div v-for="o in orders" :key="o.id" class="visit-card card">
      <!-- 卡片头部 -->
      <div class="visit-header">
        <div class="visit-date">
          <span class="date-label">{{ dateLabel(o.work_date) }}</span>
          <span class="date-full">{{ fmtDate(o.work_date) }}</span>
        </div>
        <span :class="['badge', statusBadge(o).cls]">{{ statusBadge(o).text }}</span>
      </div>

      <!-- 就诊信息 -->
      <div class="visit-body">
        <div class="visit-main">
          <h3 class="visit-hospital">{{ o.hospital_name || '—' }}</h3>
          <div class="visit-meta">
            <span class="meta-tag">{{ o.dept_name || '—' }}</span>
            <span class="meta-sep">·</span>
            <span class="meta-tag">{{ o.doctor_name || '—' }}</span>
            <span v-if="o.time_period_text" class="meta-period">{{ o.time_period_text }}</span>
          </div>
        </div>

        <div class="visit-details">
          <div class="detail-row" v-if="o.elder_name">
            <span class="detail-label">就诊人</span>
            <span class="detail-value">{{ o.elder_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">挂号费</span>
            <span class="detail-value fee">¥{{ o.register_fee || '—' }}</span>
          </div>
          <div class="detail-row" v-if="o.queue_code">
            <span class="detail-label">排队号</span>
            <span class="detail-value queue-code">{{ o.queue_code }}</span>
          </div>
        </div>
      </div>

      <!-- 排队详情（可展开） -->
      <div v-if="expandedId === o.id && o.queue_code && queueMap[o.queue_code]" class="queue-detail">
        <div class="queue-hero-row">
          <div class="qhr-block">
            <span class="qhr-label">当前叫号</span>
            <span class="qhr-num accent">{{ queueMap[o.queue_code].current_number || '—' }}</span>
          </div>
          <div class="qhr-block">
            <span class="qhr-label">我的号码</span>
            <span class="qhr-num primary">{{ queueMap[o.queue_code].my_number || o.queue_code }}</span>
          </div>
          <div class="qhr-block">
            <span class="qhr-label">前面等候</span>
            <span class="qhr-num">{{ queueMap[o.queue_code].before_you ?? '—' }}</span>
            <span class="qhr-unit">人</span>
          </div>
          <div class="qhr-block">
            <span class="qhr-label">预计等待</span>
            <span class="qhr-num gold">{{ queueMap[o.queue_code].estimated_minutes ?? '—' }}</span>
            <span class="qhr-unit">分钟</span>
          </div>
        </div>
        <div class="queue-tip">💡 页面每 15 秒自动刷新排队进度</div>
      </div>

      <!-- 底部操作 -->
      <div class="visit-footer">
        <span class="visit-id">订单号 {{ o.id }}</span>
        <button
          v-if="o.queue_code"
          class="btn-primary btn-sm"
          @click="toggleExpand(o.id)"
        >
          {{ expandedId === o.id ? '收起排队' : '查看排队' }}
        </button>
      </div>
    </div>

    <!-- 底部提示 -->
    <div v-if="orders.length > 0" class="footer-tip">
      <span>💡</span> 页面每 15 秒自动刷新 · 排队信息实时更新
    </div>
  </div>
</template>

<style scoped>
.queue-page { max-width: 960px; margin: 0 auto; padding: 24px 24px 80px; }

/* Top bar */
.queue-topbar {
  background: var(--c-accent); color: var(--c-cream);
  border-radius: var(--r-pill); padding: 12px 28px;
  display: flex; align-items: center; gap: 16px;
  font-size: 14px; font-weight: 700; margin-bottom: 24px;
}
.live-dot { width: 6px; height: 6px; background: var(--c-gold); border-radius: 50%; animation: pulse 1.5s infinite; }
.live-text { color: var(--c-gold); }
.topbar-time { margin-left: auto; font-family: "Bebas Neue", sans-serif; font-size: 18px; }
.topbar-count { opacity: .8; }

/* Empty */
.empty-card {
  text-align: center; padding: 60px 24px;
}

/* Visit card */
.visit-card {
  margin-bottom: 16px; padding: 0; overflow: hidden;
  border: 1px solid var(--c-line); border-radius: var(--r-lg);
  transition: box-shadow .2s;
}
.visit-card:hover { box-shadow: var(--shadow-2); }

.visit-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px;
  background: var(--c-bg); border-bottom: 1px solid var(--c-line);
}
.visit-date { display: flex; align-items: baseline; gap: 8px; }
.date-label {
  font-size: 18px; font-weight: 900; color: var(--c-ink-900);
}
.date-label:has(+ .date-full:not(:empty)) { }
.date-full { font-size: 13px; color: var(--c-ink-500); }

.badge {
  padding: 4px 14px; border-radius: var(--r-pill);
  font-size: 12px; font-weight: 700;
}
.badge-ok { background: var(--c-accent-bg); color: var(--c-accent-d); }
.badge-wait { background: #FFF3E0; color: #E65100; }
.badge-ing { background: #E3F2FD; color: #1565C0; }
.badge-done { background: var(--c-line); color: var(--c-ink-500); }

.visit-body { padding: 20px 24px; }
.visit-main { margin-bottom: 16px; }
.visit-hospital {
  font-size: 20px; font-weight: 900; color: var(--c-ink-900);
  margin-bottom: 8px;
}
.visit-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.meta-tag {
  font-size: 14px; font-weight: 600; color: var(--c-ink-700);
  background: var(--c-primary-bg); padding: 2px 10px; border-radius: var(--r-pill);
}
.meta-sep { color: var(--c-ink-300); }
.meta-period {
  font-size: 13px; font-weight: 700; color: #fff;
  background: var(--c-primary); padding: 2px 10px; border-radius: var(--r-pill);
}

.visit-details {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px;
  padding: 16px; background: var(--c-bg); border-radius: var(--r-md);
}
.detail-row { display: flex; justify-content: space-between; align-items: center; }
.detail-label { font-size: 13px; color: var(--c-ink-500); }
.detail-value { font-size: 14px; font-weight: 700; color: var(--c-ink-900); }
.detail-value.fee { color: var(--c-primary); font-size: 16px; }
.detail-value.queue-code {
  font-family: "Bebas Neue", monospace; font-size: 16px;
  color: var(--c-accent-d); letter-spacing: 1px;
}

.visit-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; border-top: 1px solid var(--c-line);
  background: var(--c-bg);
}
.visit-id { font-size: 12px; color: var(--c-ink-300); }
.btn-sm { padding: 6px 20px; font-size: 13px; font-weight: 700; border-radius: var(--r-pill); }

/* Queue detail */
.queue-detail {
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--c-primary-bg), #FFF8F0);
  border-top: 1px solid var(--c-line);
}
.queue-hero-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  text-align: center;
}
.qhr-block { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.qhr-label { font-size: 12px; color: var(--c-ink-500); font-weight: 600; }
.qhr-num { font-size: 36px; font-weight: 900; color: var(--c-ink-900); line-height: 1; }
.qhr-num.accent { color: var(--c-accent-d); }
.qhr-num.primary { color: var(--c-primary); }
.qhr-num.gold { color: var(--c-gold); }
.qhr-unit { font-size: 12px; color: var(--c-ink-500); }
.queue-tip {
  margin-top: 12px; text-align: center; font-size: 12px; color: var(--c-ink-500);
  background: rgba(255,255,255,.6); padding: 8px; border-radius: var(--r-md);
}

/* Footer tip */
.footer-tip {
  text-align: center; font-size: 13px; color: var(--c-ink-500);
  padding: 16px; display: flex; align-items: center; justify-content: center; gap: 6px;
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }
</style>
