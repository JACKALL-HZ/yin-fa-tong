<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reserveApi } from '@/api/reserve'
import { userApi } from '@/api/user'
import { authApi } from '@/api/auth'
import { scheduleApi } from '@/api/schedule'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import type { ElderBind, Schedule } from '@/types'

const route = useRoute()
const router = useRouter()
const scheduleId = Number(route.query.schedule_id) || 0
const schedule = ref<Schedule | null>(null)
const elders = ref<ElderBind[]>([])
const selectedElderId = ref<number | null>(null)
const sourceType = ref(1)
const loading = ref(false)

async function load() {
  if (!scheduleId) { ElMessage.warning('请先选择号源'); return }
  try {
    const [sRes, eRes] = await Promise.all([scheduleApi.getById(scheduleId), userApi.listElders()])
    schedule.value = sRes.data.data
    elders.value = eRes.data.data || []
  } catch { /* ignore */ }
}
load()

async function submit() {
  // 检查个人信息是否完善
  try {
    const { data: meRes } = await authApi.getMe()
    if (!meRes.data?.profile_complete) {
      ElMessage.warning('请先完善个人信息再预约挂号')
      return router.push('/profile-info')
    }
  } catch { /* token 异常时让后续请求失败 */ }

  loading.value = true
  try {
    const { data: res } = await reserveApi.create({
      schedule_id: scheduleId,
      elder_bind_id: selectedElderId.value || undefined,
      source_type: sourceType.value === 1 ? 'normal' : 'elder',
    })
    ElMessage.success('预约成功！请在 15 分钟内完成支付')
    const reserveId = res.data?.id
    router.push(reserveId ? `/reserve-result?reserve_id=${reserveId}` : '/orders')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || '预约失败')
  } finally { loading.value = false }
}
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">确认预约</span>
      <span class="sec-head-en">Confirm & Pay</span>
    </div>

    <div class="reserve-layout grid-hero">
      <!-- 左：信息确认 -->
      <div class="card">
        <h3 class="card-title serif">预约详情</h3>
        <div class="info-rows">
          <div class="info-row">
            <span class="info-label">就诊医院</span>
            <span class="info-val serif">{{ schedule?.hospital_name || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">就诊科室</span>
            <span class="info-val">{{ schedule?.dept_name || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">出诊医生</span>
            <span class="info-val serif">{{ schedule?.doctor_name || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">就诊日期</span>
            <span class="info-val num">{{ schedule?.work_date || '—' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">号源类型</span>
            <el-select v-model="sourceType" size="large" style="width:160px">
              <el-option :value="1" label="自主挂号" />
              <el-option :value="2" label="老年优先" />
              <el-option :value="3" label="子女代办" />
            </el-select>
          </div>
          <div class="info-row">
            <span class="info-label">就诊人</span>
            <el-select v-model="selectedElderId" size="large" placeholder="选择就诊人" style="width:200px">
              <el-option :value="null" label="为自己挂号" />
              <el-option v-for="e in elders" :key="e.id" :value="e.id" :label="e.elder_name" />
            </el-select>
          </div>
        </div>
      </div>

      <!-- 右：支付摘要 -->
      <div class="card" style="background:var(--c-accent);color:var(--c-cream);border:none">
        <h3 class="card-title serif" style="color:var(--c-cream)">费用明细</h3>
        <div class="price-big num">¥{{ schedule?.register_fee || '30' }}</div>
        <div class="price-sub">挂号费</div>
        <div class="divider-dash" style="border-color:rgba(255,247,232,.15);margin:16px 0"></div>
        <div class="price-rows">
          <div class="price-row"><span>医保统筹</span><span>¥{{ Math.floor((schedule?.register_fee || 30) * 0.6) }}</span></div>
          <div class="price-row"><span>个人账户</span><span>¥{{ Math.floor((schedule?.register_fee || 30) * 0.4) }}</span></div>
        </div>
        <button class="btn-gold" style="width:100%;margin-top:20px;font-size:18px" :disabled="loading" @click="submit">
          {{ loading ? '提交中...' : '确认预约并支付' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }

.card-title { font-size: 22px; font-weight: 900; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 2px solid var(--c-line); }

.info-rows { display: flex; flex-direction: column; gap: 4px; }
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0; border-bottom: 1px solid var(--c-line);
  font-size: 16px; color: var(--c-ink-700);
}
.info-label { font-weight: 500; color: var(--c-ink-500); }
.info-val { font-weight: 700; color: var(--c-ink-900); font-size: 17px; }

.price-big { font-size: 52px; color: var(--c-gold); text-align: center; }
.price-sub { text-align: center; font-size: 14px; opacity: .6; }
.price-rows { display: flex; flex-direction: column; gap: 8px; }
.price-row {
  display: flex; justify-content: space-between;
  font-size: 15px; opacity: .8;
}
</style>
