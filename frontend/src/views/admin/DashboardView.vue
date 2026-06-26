<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { statsApi } from '@/api/statistics'

const data = ref<any>({})
onMounted(async () => {
  try { const r = await statsApi.dashboard(); data.value = r.data.data || {} } catch {}
})
</script>

<template>
  <div>
    <div class="sec-head">
      <span class="sec-head-zh">数据看板</span>
      <span class="sec-head-en">Dashboard</span>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-num num">{{ data.total_reserves || 0 }}</div>
        <div class="stat-label">挂号总量</div>
      </div>
      <div class="stat-card">
        <div class="stat-num num">{{ data.today_reserves || 0 }}</div>
        <div class="stat-label">今日挂号</div>
      </div>
      <div class="stat-card">
        <div class="stat-num num">{{ data.total_accompany || 0 }}</div>
        <div class="stat-label">陪诊订单</div>
      </div>
      <div class="stat-card">
        <div class="stat-num num">{{ data.elder_source_rate || 0 }}%</div>
        <div class="stat-label">老年号占比</div>
      </div>
    </div>

    <div class="sec-head" style="margin-top:32px">
      <span class="sec-head-zh">科室热度 TOP 10</span>
    </div>
    <div v-if="data.dept_top10" class="card" style="padding:0;overflow:hidden">
      <div v-for="(d, i) in data.dept_top10" :key="i" class="top-item">
        <span class="rank num">#{{ i + 1 }}</span>
        <span>{{ d.dept_name }}</span>
        <span class="count">{{ d.count }} 次</span>
      </div>
    </div>
    <div v-else class="empty">暂无数据</div>
  </div>
</template>

<style scoped>
.sec-head { margin-bottom: 20px; }
.sec-head-zh { font-size: 26px; }
.sec-head-en { font-size: 14px; }
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.stat-card {
  background: var(--c-paper); border-radius: var(--r-md); padding: 24px; text-align: center;
  box-shadow: var(--shadow-1);
}
.stat-num { font-size: 40px; color: var(--c-primary); }
.stat-label { font-size: 14px; color: var(--c-ink-500); margin-top: 6px; }
.top-item {
  display: flex; align-items: center; padding: 14px 20px; border-bottom: 1px solid var(--c-line);
  font-size: 16px; font-weight: 600;
}
.top-item:last-child { border-bottom: 0; }
.rank { color: var(--c-primary); font-weight: 800; width: 48px; font-size: 18px; }
.count { margin-left: auto; color: var(--c-ink-500); }
.empty { text-align: center; padding: 40px; color: var(--c-ink-300); }
</style>
