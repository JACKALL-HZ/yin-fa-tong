<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { doctorApi } from '@/api/doctor'
import type { Doctor } from '@/types'

const route = useRoute()
const router = useRouter()
const list = ref<Doctor[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  const did = Number(route.params.did)
  try {
    const r = await doctorApi.list({ dept_id: did })
    const data: any = r.data.data
    list.value = Array.isArray(data) ? data : data?.items || data || []
  } finally { loading.value = false }
}
load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">选择医生</span>
      <span class="sec-head-en">Step 3 — Pick Doctor</span>
    </div>

    <div v-loading="loading">
      <div
        v-for="d in list" :key="(d as any).id"
        class="doc-card"
        @click="router.push(`/doctors/${(d as any).id}/schedules`)"
      >
        <div class="doc-av">{{ ((d as any).doctor_name || (d as any).doc_name || '医').charAt(0) }}</div>
        <div class="doc-info">
          <div class="doc-name serif">
            {{ (d as any).doctor_name || (d as any).doc_name }}
          </div>
          <div class="doc-title-row">
            <span class="pill pill-accent">{{ (d as any).doctor_title || (d as any).title }}</span>
            <span class="doc-dept">{{ (d as any).dept_name || (d as any).specialty }}</span>
          </div>
        </div>
        <div class="doc-right">
          <div class="doc-fee num">¥{{ (d as any).register_fee }}</div>
          <button class="btn-primary doc-btn">预约</button>
        </div>
      </div>
    </div>
    <div v-if="list.length === 0 && !loading" class="empty">该科室暂无医生</div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }

.doc-card {
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); padding: 20px 24px;
  display: flex; align-items: center; gap: 18px;
  box-shadow: var(--shadow-1); margin-bottom: 14px;
  cursor: pointer; transition: transform .2s, box-shadow .2s, border-color .2s;
}
.doc-card:hover {
  transform: translateY(-2px); box-shadow: var(--shadow-2);
  border-color: var(--c-primary);
}
.doc-av {
  width: 72px; height: 72px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, var(--c-primary), var(--c-primary-d));
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-family: "Noto Serif SC", serif; font-size: 30px; font-weight: 900;
}
.doc-info { flex: 1; min-width: 0; }
.doc-name { font-size: 22px; font-weight: 900; margin-bottom: 6px; }
.doc-title-row { display: flex; align-items: center; gap: 10px; }
.doc-dept { font-size: 14px; color: var(--c-ink-500); font-weight: 500; }
.doc-right { text-align: right; flex-shrink: 0; }
.doc-fee { font-size: 26px; color: var(--c-primary); margin-bottom: 4px; }
.doc-btn { padding: 8px 24px; font-size: 15px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
</style>
