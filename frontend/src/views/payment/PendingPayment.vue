<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { reserveApi } from '@/api/reserve'
import { paymentApi } from '@/api/payment'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ReserveOrder } from '@/types'

const router = useRouter()
const loading = ref(true)
const payingId = ref<number | null>(null)
const orders = ref<ReserveOrder[]>([])
const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

// 倒计时计算
function getRemaining(deadline: string): number {
  const end = new Date(deadline).getTime()
  return Math.max(0, end - now.value)
}

function formatCountdown(ms: number): string {
  const totalSec = Math.floor(ms / 1000)
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${String(sec).padStart(2, '0')}`
}

function isExpired(deadline: string): boolean {
  return getRemaining(deadline) <= 0
}

// 加载待缴费订单
async function loadOrders() {
  loading.value = true
  try {
    const { data: res } = await reserveApi.listMy()
    if (res.code === 200 && res.data) {
      // 只显示待支付且未过期的订单
      orders.value = (res.data as ReserveOrder[]).filter(
        o => o.pay_status === 1 && o.pay_deadline && !isExpired(o.pay_deadline)
      )
    }
  } catch (e) {
    console.error('加载待缴费订单失败:', e)
    ElMessage.error('加载订单失败')
  } finally {
    loading.value = false
  }
}

// 发起支付
async function handlePay(order: ReserveOrder) {
  if (!order.pay_deadline || isExpired(order.pay_deadline)) {
    ElMessage.warning('支付已超时，请重新预约')
    await loadOrders()
    return
  }

  payingId.value = order.id
  try {
    const { data: res } = await paymentApi.create(order.id)
    if (res.code === 200 && res.data) {
      if (res.data.pay_mode === 'sandbox' && res.data.pay_url) {
        window.location.href = res.data.pay_url
      } else {
        ElMessage.success(`支付成功！金额：¥${res.data.amount}`)
        await loadOrders()
      }
    } else {
      ElMessage.error(res.message || '支付失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '支付请求失败')
  } finally {
    payingId.value = null
  }
}

// 取消订单
async function handleCancel(order: ReserveOrder) {
  try {
    await ElMessageBox.confirm('确定取消该预约吗？取消后需重新预约。', '取消预约', {
      confirmButtonText: '确定取消',
      cancelButtonText: '继续支付',
      type: 'warning',
    })
    const { data: res } = await reserveApi.cancel(order.id)
    if (res.code === 200) {
      ElMessage.success('已取消预约')
      await loadOrders()
    } else {
      ElMessage.error(res.message || '取消失败')
    }
  } catch { /* 用户点了继续支付 */ }
}

// 时段文字
function periodText(p?: string): string {
  const map: Record<string, string> = { AM: '上午', PM: '下午', ALL: '全天' }
  return map[p || ''] || p || ''
}

onMounted(() => {
  loadOrders()
  timer = setInterval(() => { now.value = Date.now() }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="pending-page">
    <div class="sec-head">
      <span class="sec-head-zh">在线缴费</span>
      <span class="sec-head-en">Pending Payment</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="empty-state">
      <el-icon class="is-loading" :size="32"><i class="el-icon-loading" /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="orders.length === 0" class="empty-state">
      <span class="empty-icon">✅</span>
      <p class="empty-title">暂无待缴费订单</p>
      <p class="empty-sub">您当前没有需要支付的预约</p>
      <el-button type="primary" @click="router.push('/hospitals')" class="empty-btn">去预约挂号</el-button>
    </div>

    <!-- 订单列表 -->
    <div v-else class="order-list">
      <div v-for="order in orders" :key="order.id" class="order-card card">
        <!-- 倒计时条 -->
        <div class="countdown-bar" :class="{ urgent: order.pay_deadline && getRemaining(order.pay_deadline) < 3 * 60 * 1000 }">
          <span class="cd-icon">⏱</span>
          <span class="cd-text">支付剩余</span>
          <span class="cd-time num">
            {{ order.pay_deadline ? formatCountdown(getRemaining(order.pay_deadline)) : '--:--' }}
          </span>
          <span class="cd-hint">超时将自动取消</span>
        </div>

        <!-- 订单信息 -->
        <div class="order-body">
          <div class="order-row">
            <span class="order-label">就诊医院</span>
            <span class="order-value">{{ order.hospital_name || '—' }}</span>
          </div>
          <div class="order-row">
            <span class="order-label">就诊科室</span>
            <span class="order-value">{{ order.dept_name || '—' }}</span>
          </div>
          <div class="order-row">
            <span class="order-label">就诊医生</span>
            <span class="order-value">{{ order.doctor_name || '—' }}</span>
          </div>
          <div class="order-row">
            <span class="order-label">就诊时间</span>
            <span class="order-value">
              {{ order.work_date || '—' }}
              <span v-if="order.time_period_text" class="period-tag">{{ order.time_period_text }}</span>
            </span>
          </div>
          <div class="order-row">
            <span class="order-label">候诊编号</span>
            <span class="order-value code-value">{{ order.queue_code || '—' }}</span>
          </div>
        </div>

        <!-- 金额 + 操作 -->
        <div class="order-footer">
          <div class="order-amount">
            <span class="amount-label">应付金额</span>
            <span class="amount-value num">¥{{ order.register_fee || '—' }}</span>
          </div>
          <div class="order-actions">
            <el-button @click="handleCancel(order)" :disabled="payingId !== null">取消预约</el-button>
            <el-button
              type="primary"
              :loading="payingId === order.id"
              :disabled="payingId !== null"
              @click="handlePay(order)"
              class="pay-btn"
            >
              立即支付
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pending-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}
.empty-icon { font-size: 64px; display: block; margin-bottom: 16px; }
.empty-title { font-size: 20px; font-weight: 700; color: var(--c-ink-700); margin-bottom: 8px; }
.empty-sub { font-size: 14px; color: var(--c-ink-400); margin-bottom: 24px; }
.empty-btn { min-width: 160px; }

/* 订单卡片 */
.order-list { display: flex; flex-direction: column; gap: 20px; }

.order-card {
  padding: 0;
  overflow: hidden;
  border-radius: var(--r-lg);
}

/* 倒计时条 */
.countdown-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #FFF7E6, #FFF1D6);
  border-bottom: 1px solid var(--c-gold-l);
  font-size: 14px;
}
.countdown-bar.urgent {
  background: linear-gradient(135deg, #FFF0F0, #FFE4E4);
  border-bottom-color: #F4C6C6;
}
.cd-icon { font-size: 18px; }
.cd-text { color: var(--c-ink-600); }
.cd-time {
  font-size: 20px;
  font-weight: 900;
  color: var(--c-gold);
  letter-spacing: 2px;
}
.countdown-bar.urgent .cd-time { color: #E8453C; }
.cd-hint {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-ink-400);
}

/* 订单信息 */
.order-body { padding: 20px; }

.order-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--c-line);
}
.order-row:last-child { border-bottom: none; }

.order-label {
  font-size: 14px;
  color: var(--c-ink-500);
  flex-shrink: 0;
}
.order-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-ink-800);
  text-align: right;
}
.code-value {
  font-family: 'Courier New', monospace;
  color: var(--c-primary);
  letter-spacing: 1px;
}
.period-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  font-size: 12px;
  background: var(--c-primary-bg);
  color: var(--c-primary);
  border-radius: var(--r-sm);
}

/* 底部：金额 + 按钮 */
.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--c-paper);
  border-top: 1px solid var(--c-line);
}

.order-amount { display: flex; flex-direction: column; gap: 2px; }
.amount-label { font-size: 12px; color: var(--c-ink-400); }
.amount-value { font-size: 28px; color: var(--c-primary); font-weight: 900; }

.order-actions { display: flex; gap: 10px; }
.pay-btn {
  min-width: 120px;
  font-weight: 700;
  border-radius: var(--r-pill);
}
</style>
