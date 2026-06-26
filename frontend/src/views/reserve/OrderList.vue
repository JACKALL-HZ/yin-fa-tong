<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { reserveApi } from '@/api/reserve'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ReserveOrder } from '@/types'
import { orderStatusText } from '@/utils'

const router = useRouter()
const orders = ref<ReserveOrder[]>([])
const loading = ref(false)
const tab = ref(0)

// 倒计时：每秒刷新当前时间
const now = ref(Date.now())
const timer = setInterval(() => { now.value = Date.now() }, 1000)
onUnmounted(() => clearInterval(timer))

/** 计算待支付订单剩余秒数（≤0 表示已超时） */
function getPayRemain(o: ReserveOrder): number {
  if (o.pay_status !== 1 || !o.pay_deadline) return -1
  return Math.floor((new Date(o.pay_deadline).getTime() - now.value) / 1000)
}

/** 格式化倒计时 mm:ss */
function fmtCountdown(seconds: number): string {
  if (seconds <= 0) return '已超时'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

async function load() {
  loading.value = true
  try {
    const params = tab.value > 0 ? { order_status: tab.value } : {}
    const r = await reserveApi.listMy(params)
    orders.value = r.data.data || []
  } catch {
    ElMessage.error('加载挂号记录失败')
  } finally { loading.value = false }
}
function doPay(o: ReserveOrder) {
  router.push({
    path: '/payment/confirm',
    query: {
      reserve_id: String(o.id),
      hospital: o.hospital_name,
      dept: o.dept_name,
      doctor: o.doctor_name,
      date: `${o.work_date || ''} ${o.time_period_text || ''}`,
      amount: String(o.register_fee || ''),
    },
  })
}
async function doCancel(id: number) {
  try {
    await ElMessageBox.confirm('确定取消该挂号？', '提示', { type: 'warning' })
    await reserveApi.cancel(id)
    ElMessage.success('已取消')
    load()
  } catch { /* user cancelled or handled by interceptor */ }
}
function switchTab(t: number) { tab.value = t; load() }
load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">我的挂号</span>
      <span class="sec-head-en">My Appointments</span>
    </div>

    <div class="tabs">
      <span v-for="(t,i) in ['全部','待支付','已预约','已就诊']" :key="i"
            class="tab" :class="{ active: tab === i }" @click="switchTab(i)">{{ t }}</span>
    </div>

    <div v-loading="loading">
      <div v-if="orders.length === 0 && !loading" class="empty">暂无挂号记录</div>
      <div v-for="o in orders" :key="o.id" class="order-card card">
        <div class="order-top">
          <span class="status-tag" :class="'s'+o.order_status">{{ orderStatusText(o.order_status) }}</span>
          <span v-if="getPayRemain(o) > 0" class="countdown">{{ fmtCountdown(getPayRemain(o)) }}</span>
          <span v-else-if="o.pay_status === 1 && o.pay_deadline" class="countdown expired">已超时</span>
          <span class="order-code">{{ o.queue_code }}</span>
        </div>
        <div class="order-info">
          <div class="oi-row">{{ o.hospital_name }}</div>
          <div class="oi-row">{{ o.dept_name }} · {{ o.doctor_name }}</div>
          <div class="oi-row" style="color:var(--c-ink-500);font-size:14px">
            {{ o.work_date || o.schedule_date }}
            <span v-if="o.time_period_text" style="margin-left:6px;background:var(--c-primary-bg);color:var(--c-primary);padding:2px 8px;border-radius:10px;font-size:12px">{{ o.time_period_text }}</span>
          </div>
        </div>
        <div class="order-actions" v-if="o.order_status === 1">
          <button class="act-btn pay" :disabled="getPayRemain(o) <= 0 && !!o.pay_deadline" @click="doPay(o)">
            {{ (getPayRemain(o) <= 0 && o.pay_deadline) ? '已超时' : '立即支付' }}
          </button>
          <button class="act-btn cancel" @click="doCancel(o.id)">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.tabs { display: flex; gap: 8px; margin-bottom: 20px; overflow-x: auto; }
.tab { padding: 10px 20px; border-radius: var(--r-pill); font-size: 16px; font-weight: 600; cursor: pointer; background: var(--c-paper); color: var(--c-ink-500); white-space: nowrap; transition: .15s; }
.tab.active { background: var(--c-primary); color: #fff; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }

.order-card { padding: 18px; margin-bottom: 12px; }
.order-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.status-tag { padding: 4px 14px; border-radius: var(--r-pill); font-size: 14px; font-weight: 700; }
.status-tag.s1 { background: var(--c-gold-bg); color: var(--c-gold); }
.status-tag.s2 { background: var(--c-accent-l); color: var(--c-accent); }
.status-tag.s3 { background: #E8F0FE; color: #2B5876; }
.status-tag.s4 { background: #FEE2E2; color: var(--c-danger); }
.order-code { font-size: 20px; font-weight: 800; color: var(--c-primary); letter-spacing: 1px; }
.countdown { font-size: 14px; font-weight: 700; color: #e6a23c; background: #fdf6ec; padding: 2px 10px; border-radius: 10px; font-variant-numeric: tabular-nums; }
.countdown.expired { color: #f56c6c; background: #fef0f0; }
.act-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.oi-row { font-size: 16px; font-weight: 600; color: var(--c-ink-700); margin-bottom: 4px; }
.order-actions { display: flex; gap: 10px; margin-top: 12px; }
.act-btn { flex: 1; height: 52px; border: none; border-radius: var(--r-pill); font-size: 18px; font-weight: 700; cursor: pointer; }
.act-btn.pay { background: var(--c-primary); color: #fff; }
.act-btn.cancel { background: var(--c-paper); color: var(--c-ink-500); border: 2px solid var(--c-line-2); }
</style>
