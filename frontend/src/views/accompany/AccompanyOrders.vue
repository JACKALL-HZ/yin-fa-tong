<script setup lang="ts">
import { ref } from 'vue'
import { accompanyApi } from '@/api/accompany'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { AccompanyOrder } from '@/types'
import { accompanyStatusText } from '@/utils'

const orders = ref<AccompanyOrder[]>([])
const loading = ref(false)
const tab = ref(0)

async function load() {
  loading.value = true
  try {
    const params = tab.value > 0 ? { order_status: tab.value } : {}
    const r = await accompanyApi.listMy(params)
    orders.value = r.data.data || []
  } finally { loading.value = false }
}

async function doReview(order: AccompanyOrder) {
  const { value: score } = await ElMessageBox.prompt('请评分（1-5分）', '服务评价', { inputType: 'number', inputValidator: (v: string) => Number(v) >= 1 && Number(v) <= 5 })
  if (!score) return
  await accompanyApi.review(order.id, { service_score: Number(score), service_comment: '' })
  ElMessage.success('评价成功')
  load()
}

function switchTab(t: number) { tab.value = t; load() }
load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">我的陪诊</span>
      <span class="sec-head-en">My Companions</span>
    </div>

    <div class="tabs">
      <span v-for="(t,i) in ['全部','待审核','待服务','服务中','已完成']" :key="i"
            class="tab" :class="{ active: tab === i }" @click="switchTab(i)">{{ t }}</span>
    </div>

    <div v-loading="loading">
      <div v-if="orders.length === 0 && !loading" class="empty">暂无陪诊记录</div>
      <div v-for="o in orders" :key="o.id" class="order-card card">
        <div class="top">
          <span class="status" :class="'s' + o.order_status">{{ o.status_text }}</span>
          <span>{{ o.accompany_date }}</span>
        </div>
        <div class="body">
          <div>志愿者：{{ o.vol_name || '—' }}</div>
          <div>陪同长辈：{{ o.elder_name || (o.elder_bind_id ? '—' : '本人') }}</div>
        </div>
        <button v-if="o.order_status === 3" class="btn-gold review-btn" @click="doReview(o)">去评价</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.tabs { display: flex; gap: 8px; margin-bottom: 20px; overflow-x: auto; }
.tab { padding: 10px 20px; border-radius: var(--r-pill); font-size: 16px; font-weight: 600; cursor: pointer; background: var(--c-paper); color: var(--c-ink-500); white-space: nowrap; }
.tab.active { background: var(--c-primary); color: #fff; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }

.order-card { padding: 18px; margin-bottom: 12px; }
.top { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 15px; color: var(--c-ink-500); }
.status { font-weight: 700; padding: 4px 12px; border-radius: var(--r-pill); font-size: 14px; }
.status.s1 { background: var(--c-gold-bg); color: var(--c-gold); }
.status.s2 { background: #E8F0FE; color: #2B5876; }
.status.s3 { background: var(--c-accent-l); color: var(--c-accent); }
.status.s4 { background: var(--c-accent-l); color: var(--c-accent); }
.body { font-size: 16px; font-weight: 600; color: var(--c-ink-700); line-height: 2; }
.review-btn { margin-top: 12px; width: 100%; height: 48px; font-size: 18px; font-weight: 700; }
</style>
