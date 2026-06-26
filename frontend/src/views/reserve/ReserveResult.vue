<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { reserveApi } from '@/api/reserve'
import type { ReserveOrder } from '@/types'

const route = useRoute()
const router = useRouter()
const order = ref<ReserveOrder | null>(null)
const loading = ref(true)
const loadError = ref(false)

async function load() {
  const id = Number(route.query.reserve_id)
  if (!id) { loading.value = false; return }
  try {
    const { data: res } = await reserveApi.getById(id)
    if (res.code === 200) order.value = res.data
  } catch {
    loadError.value = true
    ElMessage.error('加载预约信息失败')
  }
  loading.value = false
}
onMounted(load)
</script>

<template>
  <div class="result-page">
    <div v-if="loading" class="loading">加载中...</div>

    <template v-else-if="order">
      <!-- 成功状态 -->
      <div class="result-header">
        <div class="success-icon">✓</div>
        <h1>预约成功</h1>
        <p class="tip">请在 <strong>15 分钟内</strong>完成支付，逾期将自动取消</p>
      </div>

      <!-- 就诊信息卡 -->
      <div class="info-card card">
        <h3 class="card-title">就诊信息</h3>
        <div class="info-rows">
          <div class="info-row">
            <span class="label">就诊医院</span>
            <span class="value">{{ order.hospital_name || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="label">就诊科室</span>
            <span class="value">{{ order.dept_name || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="label">出诊医生</span>
            <span class="value">{{ order.doctor_name || '—' }}</span>
          </div>
          <div class="info-row highlight">
            <span class="label">就诊时间</span>
            <span class="value time-val">
              {{ order.work_date || '—' }}
              <em>{{ order.time_period_text || '' }}</em>
            </span>
          </div>
          <div class="info-row">
            <span class="label">就诊人</span>
            <span class="value">{{ order.elder_name || '本人' }}</span>
          </div>
          <div class="info-row">
            <span class="label">号源类型</span>
            <span class="value">{{ order.source_type === 'elder' ? '老年优先' : '普通' }}</span>
          </div>
        </div>
      </div>

      <!-- 候诊编号卡 -->
      <div class="queue-card card" v-if="order.queue_code">
        <div class="queue-label">候诊编号</div>
        <div class="queue-code num">{{ order.queue_code }}</div>
        <div class="queue-hint">请妥善保存，就诊当天凭此编号签到</div>
      </div>

      <!-- 费用卡 -->
      <div class="fee-card card" v-if="order.register_fee">
        <div class="fee-row">
          <span>挂号费</span>
          <span class="fee-amount num">¥{{ order.register_fee }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button class="btn-primary" @click="router.push('/orders')">查看我的挂号</button>
        <button class="btn-secondary" @click="router.push('/')">返回首页</button>
      </div>
    </template>

    <div v-else class="empty">
      <p>{{ loadError ? '加载失败，请稍后重试' : '未找到预约信息' }}</p>
      <button class="btn-secondary" @click="router.push('/')">返回首页</button>
    </div>
  </div>
</template>

<style scoped>
.result-page {
  max-width: 480px;
  margin: 0 auto;
  padding: 32px 20px 80px;
}
.loading { text-align: center; padding: 60px 0; color: var(--c-ink-300); }

.result-header {
  text-align: center;
  margin-bottom: 28px;
}
.success-icon {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #fff;
  font-size: 36px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}
.result-header h1 {
  font-size: 24px;
  margin: 0 0 8px;
  color: var(--c-ink-900);
}
.tip {
  font-size: 14px;
  color: var(--c-danger);
  background: #FEF2F2;
  padding: 10px 16px;
  border-radius: var(--r-md);
  margin: 0;
}

.info-card { margin-bottom: 16px; }
.card-title {
  font-size: 18px;
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--c-line);
}
.info-rows { display: flex; flex-direction: column; gap: 14px; }
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.label {
  font-size: 15px;
  color: var(--c-ink-500);
}
.value {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-ink-900);
}
.info-row.highlight {
  background: var(--c-primary-bg);
  margin: 4px -16px;
  padding: 12px 16px;
  border-radius: var(--r-md);
}
.time-val {
  font-size: 17px;
  color: var(--c-primary);
}
.time-val em {
  font-style: normal;
  margin-left: 6px;
  background: var(--c-primary);
  color: #fff;
  padding: 2px 10px;
  border-radius: var(--r-pill);
  font-size: 13px;
}

.queue-card {
  text-align: center;
  margin-bottom: 16px;
  background: var(--c-primary-bg);
}
.queue-label {
  font-size: 14px;
  color: var(--c-ink-500);
  margin-bottom: 8px;
}
.queue-code {
  font-size: 48px;
  font-weight: 900;
  color: var(--c-primary);
  letter-spacing: 4px;
  line-height: 1.2;
}
.queue-hint {
  font-size: 13px;
  color: var(--c-ink-500);
  margin-top: 8px;
}

.fee-card { margin-bottom: 24px; }
.fee-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}
.fee-amount {
  font-size: 24px;
  color: var(--c-primary);
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.btn-primary {
  width: 100%;
  height: 52px;
  border: none;
  border-radius: var(--r-pill);
  background: var(--c-primary);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
}
.btn-secondary {
  width: 100%;
  height: 52px;
  border: 2px solid var(--c-line-2);
  border-radius: var(--r-pill);
  background: transparent;
  color: var(--c-ink-700);
  font-size: 17px;
  font-weight: 700;
  cursor: pointer;
}

.empty {
  text-align: center;
  padding: 60px 0;
  color: var(--c-ink-300);
}
</style>
