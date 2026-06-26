<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { reportApi } from '@/api/report'
import type { ReportItem } from '@/types'
import { formatDate } from '@/utils'

const router = useRouter()
const list = ref<ReportItem[]>([])
const loading = ref(false)
async function load() {
  loading.value = true
  try {
    const r = await reportApi.list()
    if (r.data?.code === 200) list.value = r.data.data || []
  } catch { /* 静默 */ }
  finally { loading.value = false }
}
load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">体检报告</span>
      <span class="sec-head-en">Health Reports</span>
      <span class="sec-head-more">
        <el-button type="primary" size="large" @click="router.push('/reports/upload')">+ 上传报告</el-button>
      </span>
    </div>

    <div v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty">暂无报告</div>
      <div v-for="r in list" :key="r.id" class="report-card card-hover" @click="router.push(`/reports/${r.id}`)">
        <div class="r-icon">📋</div>
        <div class="r-info">
          <div class="r-name">{{ r.elder_name || '长辈' }} 的体检报告</div>
          <div class="r-date">{{ formatDate(r.create_time) }}</div>
          <div class="r-interp" v-if="r.interpretation">{{ r.interpretation.slice(0, 60) }}...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
.report-card {
  display: flex; gap: 16px; padding: 18px; background: var(--c-paper);
  border-radius: var(--r-md); box-shadow: var(--shadow-1); margin-bottom: 10px; cursor: pointer;
}
.r-icon { font-size: 40px; flex-shrink: 0; }
.r-info { flex: 1; }
.r-name { font-size: 18px; font-weight: 800; color: var(--c-ink-900); margin-bottom: 4px; }
.r-date { font-size: 14px; color: var(--c-ink-500); }
.r-interp { font-size: 14px; color: var(--c-ink-500); margin-top: 6px; line-height: 1.6; }
</style>
