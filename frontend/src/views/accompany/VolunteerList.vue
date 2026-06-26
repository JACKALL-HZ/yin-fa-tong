<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { volunteerApi } from '@/api/volunteer'
import type { Volunteer } from '@/types'

const router = useRouter()
const list = ref<Volunteer[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r = await volunteerApi.list()
    const data: any = r.data.data
    list.value = Array.isArray(data) ? data : data?.items || data || []
  } finally { loading.value = false }
}
load()
</script>

<template>
  <div class="page-wrap">
    <!-- Hero Banner -->
    <div class="hero-banner dark-card-accent">
      <span class="watermark" style="right:30px;bottom:-40px;font-size:240px;color:rgba(255,247,232,.03)">陪</span>
      <div class="banner-content grid-hero">
        <div>
          <span class="pill pill-gold" style="display:inline-block;margin-bottom:16px">公益陪诊 · 政府补贴项目</span>
          <h1 class="banner-title serif">爸妈一个人去看病<br>有我们陪着</h1>
          <p class="banner-sub">专业陪诊员全程陪同，挂号、缴费、取药、送回家</p>
          <div class="banner-stats">
            <div class="bstat"><span class="num">3.2<span style="font-size:16px">万</span></span><span>累计服务长者</span></div>
            <div class="bstat"><span class="num">4.95</span><span>好评率</span></div>
            <div class="bstat"><span class="num">0</span><span>重大事故</span></div>
          </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:center">
          <div class="seal" style="width:80px;height:80px;font-size:16px">银发通<br>陪诊员<br>OFFICIAL</div>
        </div>
      </div>
    </div>

    <!-- 志愿者列表 -->
    <div class="sec-head" style="margin-top:40px">
      <span class="sec-head-zh">本周可预约 <b style="color:var(--c-primary)">{{ list.filter((v:any) => v.status === 1).length }}</b> 位</span>
      <span class="sec-head-en">Available Companions</span>
    </div>

    <div v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty">暂无在岗志愿者</div>
      <div class="vol-grid">
        <div v-for="v in list" :key="(v as any).id" class="vol-card card-hover" @click="router.push(`/volunteers/${(v as any).id}`)">
          <div class="vol-photo">
            <span class="vol-av">{{ ((v as any).vol_name || '志').charAt(0) }}</span>
            <span v-if="(v as any).service_score >= 4.8" class="vol-badge pill pill-gold">金牌</span>
          </div>
          <div class="vol-body">
            <h3 class="vol-name serif">{{ (v as any).vol_name }}</h3>
            <p class="vol-role">{{ (v as any).service_dept || '多科室' }}</p>
            <div class="vol-stats-row">
              <span>⭐ {{ (v as any).service_score || '4.5' }}</span>
              <span>{{ (v as any).service_count || 0 }} 次服务</span>
            </div>
            <p class="vol-quote">"{{ (v as any).service_desc || '热心服务每一位长者' }}"</p>
          </div>
          <div class="vol-action">
            <div class="vol-price num">¥0<span class="vol-subsidy">政府补贴</span></div>
            <button
              class="btn-primary"
              style="width:100%;padding:10px;font-size:14px"
              :disabled="(v as any).status !== 1"
            >
              {{ (v as any).status === 1 ? '立即预约' : '暂不可约' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 陪诊流程 -->
    <div class="sec-head" style="margin-top:56px">
      <span class="sec-head-zh">陪诊流程</span>
      <span class="sec-head-en">How It Works</span>
    </div>
    <div class="flow-steps">
      <div v-for="(s, i) in [
        { icon:'📱', title:'在线下单', desc:'选择陪诊员和日期' },
        { icon:'🚗', title:'上门接送', desc:'陪诊员准时到达' },
        { icon:'🏥', title:'全程陪同', desc:'挂号缴费取药全包' },
        { icon:'🏠', title:'安全送回', desc:'到家后汇报情况' },
      ]" :key="s.title" class="flow-step">
        <div class="flow-num">{{ i + 1 }}</div>
        <span class="flow-icon">{{ s.icon }}</span>
        <strong>{{ s.title }}</strong>
        <p>{{ s.desc }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }

/* Hero Banner */
.hero-banner { padding: 48px; border-radius: var(--r-xl); position: relative; }
.banner-title { font-size: 36px; font-weight: 900; color: var(--c-cream); line-height: 1.3; }
.banner-sub { font-size: 17px; color: rgba(255,247,232,.75); margin: 12px 0 24px; }
.banner-stats { display: flex; gap: 32px; }
.bstat { display: flex; flex-direction: column; }
.bstat .num { font-size: 32px; color: var(--c-gold); display: block; }
.bstat span:last-child { font-size: 13px; color: rgba(255,247,232,.6); }

/* 卡片网格 */
.vol-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.vol-card {
  display: grid; grid-template-columns: 120px 1fr 140px; gap: 16px;
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); padding: 24px; box-shadow: var(--shadow-1);
  cursor: pointer; transition: transform .25s, box-shadow .25s, border-color .25s;
}
.vol-card:hover { border-color: var(--c-gold); }
.vol-photo {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.vol-av {
  width: 96px; height: 120px; border-radius: var(--r-md);
  background: linear-gradient(160deg, var(--c-accent), var(--c-accent-d));
  color: var(--c-cream); display: flex; align-items: center; justify-content: center;
  font-family: "Noto Serif SC", serif; font-size: 40px; font-weight: 900;
}
.vol-badge { font-size: 10px; }
.vol-body { display: flex; flex-direction: column; gap: 6px; }
.vol-name { font-size: 22px; font-weight: 900; }
.vol-role { font-size: 14px; color: var(--c-ink-500); }
.vol-stats-row { display: flex; gap: 16px; font-size: 14px; color: var(--c-gold); font-weight: 600; }
.vol-quote { font-size: 13px; color: var(--c-ink-500); font-style: italic; margin-top: 4px; line-height: 1.5; }
.vol-action { display: flex; flex-direction: column; justify-content: center; text-align: center; gap: 8px; }
.vol-price { font-size: 24px; color: var(--c-primary); }
.vol-subsidy { display: block; font-size: 11px; color: var(--c-gold); font-family: "Noto Sans SC", sans-serif; }

/* Flow */
.flow-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.flow-step {
  text-align: center; padding: 28px 16px;
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); position: relative;
}
.flow-num {
  position: absolute; top: -16px; left: 50%; transform: translateX(-50%);
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--c-primary); color: #fff; font-family: "Bebas Neue", sans-serif;
  font-size: 18px; display: flex; align-items: center; justify-content: center;
}
.flow-icon { font-size: 40px; display: block; margin: 8px 0 10px; }
.flow-step strong { font-size: 16px; color: var(--c-ink-900); display: block; }
.flow-step p { font-size: 13px; color: var(--c-ink-500); margin-top: 4px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
</style>
