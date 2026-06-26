<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { scheduleApi } from '@/api/schedule'
import type { Schedule } from '@/types'

const route = useRoute()
const router = useRouter()
const slots = ref<Schedule[]>([])
const selectedId = ref(0)
const loading = ref(false)

// time_period 后端值为 "AM"/"PM"/"ALL"
const PERIOD_ORDER = ['AM', 'PM', 'ALL'] as const

const groupedSlots = computed(() => {
  const groups: Record<string, Schedule[]> = { AM: [], PM: [], ALL: [] }
  slots.value.forEach(s => {
    const tp = s.time_period || 'AM'
    if (groups[tp]) groups[tp].push(s)
  })
  return groups
})

async function load() {
  loading.value = true
  const did = Number(route.params.did)
  try {
    const r = await scheduleApi.list({ doctor_id: did })
    const data: any = r.data.data
    slots.value = Array.isArray(data) ? data : data?.items || data || []
  } finally { loading.value = false }
}

function selectSlot(s: Schedule) {
  const nr = s.normal_remain ?? 0
  const er = s.elder_remain ?? 0
  if (nr <= 0 && er <= 0) return
  selectedId.value = s.id
}

function goReserve() {
  if (!selectedId.value) return
  router.push(`/reserve?schedule_id=${selectedId.value}`)
}

function periodText(p: string) {
  return { AM: '上午', PM: '下午', ALL: '全天' }[p] || p
}
function periodTime(p: string) {
  return { AM: '08:00 — 12:00', PM: '14:00 — 17:30', ALL: '08:00 — 17:30' }[p] || ''
}

load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">选择号源</span>
      <span class="sec-head-en">Step 4 — Pick Time Slot</span>
    </div>

    <div v-loading="loading">
      <template v-for="p in PERIOD_ORDER" :key="p">
        <div class="slot-section" v-if="groupedSlots[p]?.length">
          <div class="slot-head">
            <span class="slot-period serif">{{ periodText(p) }}</span>
            <span class="slot-time">{{ periodTime(p) }}</span>
          </div>
          <div class="slot-grid">
            <div
              v-for="s in groupedSlots[p]" :key="(s as any).id"
              class="slot-item"
              :class="{
                selected: (s as any).id === selectedId,
                full: (s.normal_remain ?? 0) <= 0 && (s.elder_remain ?? 0) <= 0,
                limited: (s.normal_remain ?? 0) + (s.elder_remain ?? 0) <= 3 && (s.normal_remain ?? 0) + (s.elder_remain ?? 0) > 0,
              }"
              @click="selectSlot(s)"
            >
              <div class="slot-date num">{{ (s as any).work_date || (s as any).schedule_date }}</div>
              <div class="slot-weekday">{{ periodText(p) }}</div>
              <div class="slot-status">
                <template v-if="(s.normal_remain ?? 0) <= 0 && (s.elder_remain ?? 0) <= 0">
                  <span class="status-full">已满</span>
                </template>
                <template v-else-if="(s.normal_remain ?? 0) + (s.elder_remain ?? 0) <= 3">
                  <span class="status-few">余 {{ (s.normal_remain ?? 0) + (s.elder_remain ?? 0) }}</span>
                </template>
                <template v-else>
                  <span class="status-ok">普通{{ (s as any).normal_remain }} 老年{{ (s as any).elder_remain }}</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div v-if="slots.length === 0 && !loading" class="empty">暂无号源</div>

    <!-- 底部确认 -->
    <div class="bottom-bar" v-if="selectedId">
      <button class="btn-primary confirm-btn" @click="goReserve">确认选择 →</button>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 120px; }

.slot-section { margin-bottom: 24px; }
.slot-head {
  display: flex; align-items: center; gap: 10px;
  padding: 0 4px 12px; margin-bottom: 14px;
  border-bottom: 2px solid var(--c-line);
}
.slot-period { font-size: 24px; font-weight: 900; color: var(--c-ink-900); }
.slot-time { color: var(--c-ink-500); font-size: 15px; font-weight: 500; }

.slot-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }

.slot-item {
  background: var(--c-paper); border: 2px solid var(--c-line);
  border-radius: var(--r-md); padding: 18px 14px; text-align: center;
  cursor: pointer; transition: all .2s; min-height: 90px;
  display: flex; flex-direction: column; justify-content: center; gap: 6px;
}
.slot-item:hover { border-color: var(--c-primary); box-shadow: var(--shadow-1); }
.slot-item.selected {
  background: var(--c-primary); border-color: var(--c-primary-d);
  color: #fff; box-shadow: 0 6px 16px rgba(184,69,31,.35);
}
.slot-item.selected .slot-date,
.slot-item.selected .slot-weekday,
.slot-item.selected .slot-status { color: rgba(255,255,255,.9); }
.slot-item.full {
  background: #F5F0E8; border-style: dashed; cursor: not-allowed; opacity: .6;
}
.slot-item.limited { border-color: var(--c-gold); background: var(--c-gold-bg); }

.slot-date { font-size: 18px; color: var(--c-ink-900); line-height: 1; }
.slot-weekday { font-size: 13px; color: var(--c-ink-500); font-weight: 700; }
.slot-status { font-size: 13px; font-weight: 700; }

.status-ok { color: var(--c-accent); }
.status-few { color: var(--c-gold); }
.status-full { color: var(--c-ink-300); }
.slot-item.selected .status-ok,
.slot-item.selected .status-few { color: var(--c-gold-l); }

.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }

.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 16px 32px; background: var(--c-paper); border-top: 1px solid var(--c-line); z-index: 50; }
.confirm-btn { width: 100%; height: 56px; font-size: 20px; letter-spacing: 2px; }
</style>
