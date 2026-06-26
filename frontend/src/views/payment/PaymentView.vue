<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { paymentApi } from '@/api/payment'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const paying = ref(false)

const bill = {
  hospital: (route.query.hospital as string) || '—',
  dept: (route.query.dept as string) || '—',
  doctor: (route.query.doctor as string) || '—',
  date: (route.query.date as string) || '—',
  amount: Number(route.query.amount) || 0,
  reserve_id: Number(route.query.reserve_id) || 0,
}

const doPay = async () => {
  if (!bill.reserve_id) return
  paying.value = true
  try {
    const { data: res } = await paymentApi.create(bill.reserve_id)
    if (res.code === 200 && res.data) {
      if (res.data.pay_mode === 'sandbox' && res.data.pay_url) {
        // 沙箱模式：跳转到支付宝支付页面
        window.location.href = res.data.pay_url
      } else {
        // 模拟模式：直接完成
        ElMessage.success(`支付成功！金额：¥${res.data.amount}`)
        router.push({ path: '/pay-result', query: { reserve_id: String(bill.reserve_id) } })
      }
    } else {
      ElMessage.error(res.message || '支付失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '支付请求失败')
  } finally {
    paying.value = false
  }
}
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">确认支付</span>
      <span class="sec-head-en">Payment</span>
    </div>

    <div class="card">
      <div class="pay-row"><span>就诊医院</span><span class="v">{{ bill.hospital }}</span></div>
      <div class="pay-row"><span>就诊科室</span><span class="v">{{ bill.dept }}</span></div>
      <div class="pay-row"><span>就诊医生</span><span class="v">{{ bill.doctor }}</span></div>
      <div class="pay-row"><span>就诊时间</span><span class="v">{{ bill.date }}</span></div>
      <div class="pay-total">
        <span class="l">应付金额</span>
        <span class="v num"><small>¥</small>{{ bill.amount || '—' }}</span>
      </div>
      <div class="pay-actions">
        <el-button
          type="primary"
          size="large"
          :loading="paying"
          @click="doPay"
          class="pay-btn"
        >
          💳 确认支付
        </el-button>
        <el-button size="large" @click="router.back()" class="cancel-btn">
          取消
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 720px; margin: 0 auto; padding: 32px 32px 80px; }

.pay-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 0; border-bottom: 1px solid var(--c-line);
  font-size: 18px; color: var(--c-ink-700); font-weight: 500;
}
.pay-row .v { color: var(--c-ink-900); font-weight: 700; font-size: 20px; }
.pay-total {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 24px 0 20px;
}
.pay-total .l { font-size: 22px; font-weight: 700; }
.pay-total .v { font-size: 52px; color: var(--c-primary); }
.pay-total .v small { font-size: 22px; margin-right: 4px; }

.pay-actions { display: flex; gap: 12px; margin-top: 12px; }
.pay-actions .pay-btn {
  flex: 2; height: 72px; font-size: 20px; font-weight: 700;
  border-radius: var(--r-pill); letter-spacing: 1px;
}
.pay-actions .cancel-btn {
  flex: 1; height: 72px; font-size: 18px; border-radius: var(--r-pill);
}
</style>
