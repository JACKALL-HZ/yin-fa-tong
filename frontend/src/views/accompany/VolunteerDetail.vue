<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { volunteerApi } from '@/api/volunteer'
import { accompanyApi } from '@/api/accompany'
import { userApi } from '@/api/user'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Volunteer, ElderBind } from '@/types'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const vol = ref<Volunteer | null>(null)
const elders = ref<ElderBind[]>([])
const loading = ref(false)

const isElder = computed(() => user.info?.user_type === 1)

async function load() {
  loading.value = true
  try {
    const [vRes, eRes] = await Promise.all([
      volunteerApi.getById(Number(route.params.vid)),
      isElder.value ? Promise.resolve(null) : userApi.listElders(),
    ])
    vol.value = vRes.data.data
    elders.value = eRes ? (eRes.data.data || []) : []
  } finally { loading.value = false }
}

async function book() {
  // 子女用户需先绑定长辈
  if (!isElder.value && elders.value.length === 0) {
    return ElMessage.warning('请先在"长辈管理"中添加长辈')
  }
  try {
    const { value: dateValue } = await ElMessageBox.prompt('选择陪诊日期', '预约陪诊', {
      inputType: 'date',
      inputValidator: (v: string) => !!v || '请选择日期',
    })
    if (!dateValue) return
    await accompanyApi.create({
      volunteer_id: (vol.value as any).id,
      elder_bind_id: isElder.value ? null : elders.value[0].id,
      accompany_date: dateValue,
    })
    ElMessage.success('申请已提交，等待审核')
    router.push('/accompany-orders')
  } catch {
    // 取消或网络错误
  }
}
load()
</script>

<template>
  <div class="page-wrap" v-if="vol">
    <div class="detail-hero grid-hero">
      <!-- 左：照片卡片 -->
      <div class="dark-card-accent" style="text-align:center">
        <div class="detail-av">{{ (vol as any).vol_name?.charAt(0) || '志' }}</div>
        <h1 class="serif" style="font-size:28px;color:var(--c-cream);margin:12px 0 6px">{{ (vol as any).vol_name }}</h1>
        <div style="display:flex;gap:8px;justify-content:center;margin-bottom:16px">
          <span class="pill pill-accent">{{ (vol as any).service_dept || '多科室' }}</span>
          <span class="pill pill-gold" v-if="(vol as any).status === 1">在岗</span>
          <span class="pill pill-outline" v-else>休息中</span>
        </div>
        <div class="detail-stats-row">
          <div class="dstat"><span class="num">⭐{{ (vol as any).service_score || '4.5' }}</span><span>评分</span></div>
          <div class="dstat"><span class="num">{{ (vol as any).service_count || 0 }}</span><span>服务次数</span></div>
          <div class="dstat"><span class="num" style="color:var(--c-gold)">金牌</span><span>等级</span></div>
        </div>
      </div>
      <!-- 右：详情 -->
      <div class="card">
        <h3 class="card-title serif">陪诊员简介</h3>
        <p style="font-size:16px;color:var(--c-ink-700);line-height:1.8;white-space:pre-wrap">{{ (vol as any).service_desc || '暂无简介' }}</p>
        <div class="divider-dash" style="margin:20px 0"></div>
        <div class="detail-contacts">
          <div class="dcontact"><span>📞</span><span>{{ (vol as any).vol_phone || '—' }}</span></div>
        </div>
      </div>
    </div>

    <button
      v-if="(vol as any).status === 1"
      class="btn-primary"
      style="width:100%;height:60px;font-size:22px;margin-top:24px;letter-spacing:2px"
      @click="book"
    >立即预约陪诊</button>
    <p v-else style="text-align:center;padding:40px;color:var(--c-ink-300);font-size:17px">该陪诊员当前暂不可预约</p>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }

.detail-av {
  width: 100px; height: 100px; border-radius: 50%;
  background: rgba(255,247,232,.2); color: var(--c-cream);
  display: inline-flex; align-items: center; justify-content: center;
  font-family: "Noto Serif SC", serif; font-size: 42px; font-weight: 900;
}
.detail-stats-row { display: flex; justify-content: center; gap: 24px; }
.dstat { display: flex; flex-direction: column; align-items: center; }
.dstat .num { font-size: 22px; font-weight: 800; color: var(--c-gold); }
.dstat span:last-child { font-size: 12px; color: rgba(255,247,232,.6); }

.card-title { font-size: 22px; font-weight: 900; margin-bottom: 16px; }
.dcontact { display: flex; align-items: center; gap: 10px; font-size: 16px; color: var(--c-ink-700); font-weight: 600; }
</style>
