<template>
  <div class="pay-result-page">
    <div class="result-card">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p>正在查询支付结果...</p>
      </div>

      <template v-else>
        <div v-if="result?.pay_status === 2" class="success-state">
          <el-icon :size="64" color="#67c23a"><CircleCheck /></el-icon>
          <h2>支付成功</h2>
          <p class="amount">¥{{ result.amount }}</p>
          <p class="time">支付时间：{{ result.pay_time }}</p>
        </div>

        <div v-else-if="result?.pay_status === 3" class="failed-state">
          <el-icon :size="64" color="#f56c6c"><CircleClose /></el-icon>
          <h2>支付已取消</h2>
          <p>订单超时未支付，已自动取消</p>
        </div>

        <div v-else class="pending-state">
          <el-icon :size="64" color="#e6a23c"><Warning /></el-icon>
          <h2>{{ pollFailed ? '查询超时' : '等待支付' }}</h2>
          <p>{{ pollFailed ? '请确认是否已完成支付' : '请在支付宝完成支付' }}</p>
          <el-button v-if="pollFailed" type="primary" style="margin-top:12px" @click="retryPoll">重新查询</el-button>
        </div>
      </template>

      <div class="actions">
        <el-button type="primary" @click="router.push('/orders')">查看订单</el-button>
        <el-button @click="router.push('/')">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'
import { paymentApi, type PaymentResultData } from '@/api/payment'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const result = ref<PaymentResultData | null>(null)
const pollFailed = ref(false)

const pollResult = async (outTradeNo: string, retries = 10) => {
  pollFailed.value = false
  for (let i = 0; i < retries; i++) {
    try {
      const { data: res } = await paymentApi.queryByTradeNo(outTradeNo)
      if (res.code === 200 && res.data) {
        result.value = res.data
        if (res.data.pay_status !== 1) {
          loading.value = false
          return
        }
      }
    } catch {
      // 单次失败继续重试
    }
    await new Promise(r => setTimeout(r, 2000))
  }
  loading.value = false
  pollFailed.value = true
}

const retryPoll = () => {
  const outTradeNo = route.query.out_trade_no as string
  if (outTradeNo) pollResult(outTradeNo)
}

onMounted(async () => {
  // 支付宝回调带 out_trade_no，从 OrderList 跳转带 reserve_id
  const outTradeNo = route.query.out_trade_no as string
  const reserveId = Number(route.query.reserve_id)
  if (outTradeNo) {
    // 先主动同步支付宝状态（notify 回调可能未到达）
    try {
      const { data: syncRes } = await paymentApi.syncStatus(outTradeNo)
      if (syncRes.code === 200 && syncRes.data && syncRes.data.pay_status !== 1) {
        // 同步成功，直接显示结果
        result.value = syncRes.data
        loading.value = false
        return
      }
    } catch {
      // 同步失败，降级为轮询
    }
    // 轮询兜底
    pollResult(outTradeNo)
  } else if (reserveId) {
    // 兼容从订单列表进入的场景（需登录）
    pollByReserveId(reserveId)
  } else {
    loading.value = false
  }
})

const pollByReserveId = async (reserveId: number, retries = 10) => {
  pollFailed.value = false
  for (let i = 0; i < retries; i++) {
    try {
      const { data: res } = await paymentApi.getResult(reserveId)
      if (res.code === 200 && res.data) {
        result.value = res.data
        if (res.data.pay_status !== 1) {
          loading.value = false
          return
        }
      }
    } catch {
      // 单次失败继续重试
    }
    await new Promise(r => setTimeout(r, 2000))
  }
  loading.value = false
  pollFailed.value = true
}
</script>

<style scoped>
.pay-result-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  padding: 20px;
}
.result-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.result-card h2 { margin: 16px 0 8px; font-size: 20px; }
.amount { font-size: 28px; font-weight: 700; color: #67c23a; margin: 8px 0; }
.time { color: #909399; font-size: 14px; }
.loading-state p { margin-top: 16px; color: #909399; }
.actions { margin-top: 32px; display: flex; gap: 12px; justify-content: center; }
</style>
