<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { hospitalApi } from '@/api/hospital'
import { ElMessage } from 'element-plus'
import type { Hospital } from '@/types'

const route = useRoute()
const router = useRouter()
const list = ref<Hospital[]>([])
const loading = ref(false)
const keyword = ref('')
const guidedDept = ref('')

onMounted(() => {
  const dept = route.query.dept as string
  if (dept) {
    guidedDept.value = dept
    ElMessage.success(`已为您定位到【${dept}】，请选择医院`)
  }
})

async function load() {
  loading.value = true
  try {
    const r = await hospitalApi.list()
    const data: any = r.data.data || []
    list.value = Array.isArray(data) ? data : data.items || []
  } finally { loading.value = false }
}

const filtered = ref<Hospital[]>([])
function doSearch() {
  if (!keyword.value.trim()) { filtered.value = []; return }
  const kw = keyword.value.trim().toLowerCase()
  filtered.value = list.value.filter((h: any) =>
    (h.hospital_name || h.name || '').toLowerCase().includes(kw) ||
    (h.address || '').toLowerCase().includes(kw)
  )
}

load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">选择医院</span>
      <span class="sec-head-en">Step 1 — Pick Hospital</span>
    </div>

    <!-- 导诊提示 -->
    <div v-if="guidedDept" class="guide-hint">
      <span class="guide-icon">🩺</span>
      <span>智能导诊推荐：<b>【{{ guidedDept }}】</b>，请选择一家医院后进入对应科室</span>
    </div>

    <!-- 搜索框 -->
    <div class="search-pill">
      <span class="search-icon">🔍</span>
      <input v-model="keyword" placeholder="搜索医院名称或地址…" @input="doSearch" />
    </div>

    <div v-loading="loading">
      <div
        v-for="h in (filtered.length ? filtered : list)"
        :key="(h as any).id"
        class="hosp-card card-hover"
        @click="router.push({ path: `/hospitals/${(h as any).id}/departments`, query: guidedDept ? { dept: guidedDept } : {} })"
      >
        <div class="hosp-av">🏥</div>
        <div class="hosp-info">
          <div class="hosp-name serif">{{ (h as any).hospital_name || (h as any).name }}</div>
          <div class="hosp-addr">{{ (h as any).address }}</div>
        </div>
        <span class="pill" :class="((h as any).hospital_level || (h as any).level) === '三级甲等' ? 'pill-primary' : ((h as any).hospital_level || (h as any).level) === '二级甲等' ? 'pill-accent' : 'pill-outline'">
          {{ (h as any).hospital_level || (h as any).level || '一级' }}
        </span>
        <span class="hosp-arrow">→</span>
      </div>
    </div>
    <div v-if="list.length === 0 && !loading" class="empty">暂无医院信息</div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }

/* 搜索 */
.search-pill {
  display: flex; align-items: center; gap: 10px;
  background: var(--c-paper); border: 1.5px solid var(--c-line);
  border-radius: var(--r-pill); padding: 0 20px; height: 52px; margin-bottom: 24px;
}
.search-pill:focus-within { border-color: var(--c-primary); box-shadow: var(--shadow-1); }
.search-pill input {
  flex: 1; border: none; outline: none; background: none;
  font-size: 17px; color: var(--c-ink-900);
}
.search-pill input::placeholder { color: var(--c-ink-300); }
.search-icon { font-size: 20px; opacity: .7; }

/* 卡片 */
.hosp-card {
  display: flex; align-items: center; gap: 16px; padding: 18px 20px;
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); box-shadow: var(--shadow-1);
  margin-bottom: 12px; cursor: pointer;
}
.hosp-av {
  width: 56px; height: 56px; border-radius: 16px; background: var(--c-primary-bg);
  display: flex; align-items: center; justify-content: center; font-size: 28px; flex-shrink: 0;
}
.hosp-info { flex: 1; min-width: 0; }
.hosp-name { font-size: 22px; font-weight: 900; margin-bottom: 4px; }
.hosp-addr { font-size: 14px; color: var(--c-ink-500); }
.hosp-arrow { font-size: 22px; color: var(--c-ink-300); }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }

/* 导诊提示 */
.guide-hint {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 20px; margin-bottom: 16px;
  background: var(--c-accent-l); border-radius: var(--r-md);
  border-left: 4px solid var(--c-accent);
  font-size: 15px; color: var(--c-ink-700);
}
.guide-hint b { color: var(--c-accent-d); }
.guide-icon { font-size: 20px; }
</style>
