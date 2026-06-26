<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { deptApi } from '@/api/department'
import { ElMessage } from 'element-plus'
import type { Department } from '@/types'

const route = useRoute()
const router = useRouter()
const list = ref<Department[]>([])
const loading = ref(false)
const guidedDept = ref('')

const sortedList = computed(() => {
  if (!guidedDept.value) return list.value
  const kw = guidedDept.value.toLowerCase()
  const matched: Department[] = []
  const rest: Department[] = []
  for (const d of list.value) {
    const name = ((d as any).dept_name || '').toLowerCase()
    if (name.includes(kw) || kw.includes(name)) {
      matched.push(d)
    } else {
      rest.push(d)
    }
  }
  return [...matched, ...rest]
})

function isMatched(d: Department) {
  if (!guidedDept.value) return false
  const name = ((d as any).dept_name || '').toLowerCase()
  const kw = guidedDept.value.toLowerCase()
  return name.includes(kw) || kw.includes(name)
}

function goDoctors(d: Department) {
  router.push(`/departments/${(d as any).id}/doctors`)
}

async function load() {
  loading.value = true
  const hid = Number(route.params.hid)
  try {
    const r = await deptApi.getByHospital(hid)
    list.value = r.data.data || []
  } finally { loading.value = false }
}

onMounted(() => {
  const dept = route.query.dept as string
  if (dept) {
    guidedDept.value = dept
    ElMessage.success(`已为您推荐【${dept}】相关科室`)
  }
  load()
})
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">选择科室</span>
      <span class="sec-head-en">Step 2 — Pick Department</span>
    </div>

    <!-- 导诊提示 -->
    <div v-if="guidedDept" class="guide-hint">
      <span class="guide-icon">🩺</span>
      <span>智能导诊推荐：<b>【{{ guidedDept }}】</b>，推荐科室已置顶显示</span>
    </div>

    <div class="dept-grid" v-loading="loading">
      <div
        v-for="d in sortedList"
        :key="(d as any).id"
        :class="['dept-card', 'card-hover', { 'dept-highlight': isMatched(d) }]"
        @click="goDoctors(d)"
      >
        <div class="dept-icon">{{ isMatched(d) ? '✅' : '🏥' }}</div>
        <div class="dept-name serif">{{ (d as any).dept_name }}</div>
        <div class="dept-sub">{{ isMatched(d) ? '推荐科室 — 点击查看医生' : '点击查看出诊医生' }}</div>
      </div>
    </div>
    <div v-if="list.length === 0 && !loading" class="empty">该医院暂无科室</div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }
.dept-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.dept-card {
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); padding: 32px 20px;
  text-align: center; box-shadow: var(--shadow-1);
  cursor: pointer; min-height: 170px;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px;
}
.dept-icon {
  width: 68px; height: 68px; border-radius: 20px;
  background: var(--c-primary-bg); color: var(--c-primary);
  display: flex; align-items: center; justify-content: center; font-size: 36px;
}
.dept-name { font-size: 22px; font-weight: 900; color: var(--c-ink-900); }
.dept-sub { font-size: 13px; color: var(--c-ink-500); }
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

/* 推荐科室高亮 */
.dept-highlight {
  border-color: var(--c-accent) !important;
  background: var(--c-accent-l) !important;
  box-shadow: 0 0 0 2px rgba(31,77,58,.15);
}
</style>
