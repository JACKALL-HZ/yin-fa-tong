<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { guideApi } from '@/api/guide'
import { ElMessage } from 'element-plus'
import type { GuideResult, GuideResponse } from '@/types'

const router = useRouter()
const symptomText = ref('')
const results = ref<GuideResult[]>([])
const guideData = ref<GuideResponse | null>(null)
const activePart = ref('')
const isListening = ref(false)
const loading = ref(false)
const streamSteps = ref<string[]>([])   // 已完成节点
const currentStep = ref('')              // 当前进行中节点

const bodyParts = [
  { id: 'head', label: '头 / 脑', top: '22px', left: '50%', tagClass: 'head' },
  { id: 'chest', label: '胸 / 心', top: '140px', right: '10px', tagClass: 'chest' },
  { id: 'belly', label: '腹 / 胃', top: '230px', left: '10px', tagClass: 'belly' },
]
const partSymptoms: Record<string, string> = {
  head: '头疼头晕脑胀',
  chest: '胸闷心慌胸痛',
  belly: '肚子疼胃疼腹胀',
}

function clickPart(id: string) {
  activePart.value = id
  symptomText.value = partSymptoms[id] || ''
  doDiagnose()
}

async function doDiagnose() {
  if (!symptomText.value.trim()) return
  loading.value = true
  streamSteps.value = []
  currentStep.value = ''
  guideData.value = null
  results.value = []
  try {
    await guideApi.streamDiagnose(symptomText.value, (event, data) => {
      if (event === 'node_end') {
        currentStep.value = data.label
        streamSteps.value.push(data.label)
      } else if (event === 'final') {
        guideData.value = data
        results.value = data.results || []
      } else if (event === 'error') {
        ElMessage.error(data.message || '导诊失败')
      }
    })
  } catch (err) {
    console.error('[GuideView] stream error:', err)
    ElMessage.error('导诊服务暂时不可用，请稍后重试')
  } finally { loading.value = false }
}

function toggleVoice() {
  isListening.value = !isListening.value
  if (isListening.value) setTimeout(() => { isListening.value = false }, 2000)
}

function goReserve(dept: string) {
  console.log('[GuideView] goReserve called, dept:', dept)
  if (!dept) {
    ElMessage.warning('科室名称为空，无法跳转')
    return
  }
  const target = `/hospitals?dept=${encodeURIComponent(dept)}`
  console.log('[GuideView] navigating to:', target)
  router.push(target).catch(err => {
    console.error('[GuideView] navigation failed:', err)
  })
}
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">智能导诊</span>
      <span class="sec-head-en">AI Symptom Checker</span>
    </div>

    <!-- 人体图 -->
    <div class="card" style="margin-bottom:24px">
      <div class="body-q">您哪里不舒服？</div>
      <div class="body-q-sub">点击身体对应部位，我帮您推荐科室</div>
      <div class="body-svg-wrap">
        <svg class="body-svg" viewBox="0 0 200 360">
          <ellipse :class="['body-part', { active: activePart === 'head' }]" cx="100" cy="40" rx="32" ry="38" @click="clickPart('head')" />
          <rect :class="['body-part', { active: activePart === 'chest' }]" x="72" y="80" width="56" height="80" rx="20" @click="clickPart('chest')" />
          <rect :class="['body-part', { active: activePart === 'belly' }]" x="72" y="160" width="56" height="60" rx="14" @click="clickPart('belly')" />
          <rect class="body-part" x="40" y="86" width="28" height="100" rx="14" />
          <rect class="body-part" x="132" y="86" width="28" height="100" rx="14" />
          <rect class="body-part" x="76" y="220" width="22" height="120" rx="10" />
          <rect class="body-part" x="102" y="220" width="22" height="120" rx="10" />
        </svg>
        <div v-for="p in bodyParts" :key="p.id" :class="['body-tag', p.tagClass, { active: activePart === p.id }]">{{ p.label }}</div>
      </div>

      <!-- 科室推荐 -->
      <div class="body-suggest" v-if="results.length" @click="console.log('[GuideView] suggest area clicked')">
        <span class="lbl">已为您推荐 ↓</span>
        <div class="deck">
          <button v-for="(r, idx) in results" :key="r.dept_name" class="dept-chip" type="button"
            @click="goReserve(r.dept_name)"
            :data-dept="r.dept_name">
            {{ r.dept_name }}
            <span v-if="guideData?.engine === 'langgraph' && r.confidence" class="chip-conf">
              {{ (r.confidence * 100).toFixed(0) }}%
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 文字输入 -->
    <div style="margin-bottom:24px">
      <el-input v-model="symptomText" size="large" placeholder="说说哪里不舒服...（如：头疼三天、拉肚子）" clearable @keyup.enter="doDiagnose">
        <template #append>
          <el-button @click="doDiagnose" :loading="loading">查一查</el-button>
        </template>
      </el-input>
    </div>

    <!-- 加载态 + 流式进度 -->
    <div v-if="loading" class="loading-card card">
      <div class="stream-progress">
        <div v-for="(s, i) in streamSteps" :key="i" class="step done">
          <span class="step-dot">✓</span><span class="step-text">{{ s }}</span>
        </div>
        <div class="step active">
          <span class="step-dot spin">●</span><span class="step-text">{{ currentStep || '正在分析…' }}</span>
        </div>
      </div>
      <p class="loading-msg">AI 正在分析您的症状，请稍候…</p>
    </div>

    <!-- 结果区（加载完成后） -->
    <template v-if="guideData && !loading">

      <!-- 紧急提醒 -->
      <div v-if="guideData.emergency_flag" class="emergency-alert">
        <span class="emergency-icon">🚨</span>
        <div>
          <div class="emergency-title">紧急提醒：您的症状可能需要立即就医！</div>
          <div class="emergency-body">请尽快前往最近医院急诊科就诊，或拨打 120 急救电话。不要自行驾车。</div>
        </div>
      </div>

      <!-- AI 分析推理 -->
      <div v-if="guideData.engine === 'langgraph' && guideData.results.length" class="card reasoning-card">
        <h3 class="card-section-title">🩺 AI 分析说明</h3>
        <div v-for="r in guideData.results" :key="r.dept_name" class="reason-row">
          <div class="reason-dept-row">
            <span class="reason-dept">{{ r.dept_name }}</span>
            <span v-if="r.confidence" class="reason-conf">置信度 {{ (r.confidence * 100).toFixed(0) }}%</span>
          </div>
          <p v-if="r.reasoning" class="reason-text">{{ r.reasoning }}</p>
        </div>
      </div>

      <!-- OTC 用药参考 -->
      <div v-if="guideData.medications?.length" class="card med-card">
        <h3 class="card-section-title">
          💊 OTC 用药参考
          <span class="med-badge">非处方药</span>
        </h3>
        <p class="med-disclaimer">以下为非处方药建议，仅供参考。服用前请仔细阅读说明书或咨询药师，切勿多药同服。</p>
        <div v-for="med in guideData.medications" :key="med.drug_name" class="med-item">
          <div class="med-name">{{ med.drug_name }}</div>
          <div v-if="med.indication" class="med-detail"><span class="label">适应症：</span>{{ med.indication }}</div>
          <div v-if="med.dosage_note" class="med-detail"><span class="label">用法用量：</span>{{ med.dosage_note }}</div>
          <div v-if="med.elderly_precaution" class="med-detail caution"><span class="label">⚠ 老年注意：</span>{{ med.elderly_precaution }}</div>
          <div v-if="med.contraindication" class="med-detail contraind"><span class="label">🚫 禁忌：</span>{{ med.contraindication }}</div>
        </div>
      </div>

      <!-- 老年综合注意事项 -->
      <div v-if="guideData.elderly_precautions" class="card precaution-card">
        <h3 class="card-section-title">🛡 老年患者综合注意事项</h3>
        <p class="precaution-text">{{ guideData.elderly_precautions }}</p>
      </div>

      <!-- 生活建议 -->
      <div v-if="guideData.general_advice" class="card advice-card">
        <h3 class="card-section-title">📋 生活建议</h3>
        <p class="advice-text">{{ guideData.general_advice }}</p>
      </div>

      <!-- 引擎标签 -->
      <div class="engine-badge">
        <span v-if="guideData.engine === 'langgraph'" class="badge-ai">🤖 AI 智能分析</span>
        <span v-else class="badge-rule">📋 基础症状匹配</span>
      </div>
    </template>

    <!-- 语音（模拟） -->
    <div style="text-align:center;padding:24px 0">
      <div class="voice-btn" :class="{ listening: isListening }" @click="toggleVoice">🎙</div>
      <p style="font-size:18px;color:var(--c-ink-500);margin:12px 0 20px">按住说话</p>
      <div class="voice-help">
        <div class="h">💡 您可以这样说</div>
        <ul>
          <li>「我头疼三天了」</li>
          <li>「帮我挂个心血管内科」</li>
          <li>「明天上午的号」</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }

/* ── 人体图 ── */
.body-q { font-size: 26px; font-weight: 800; text-align: center; margin-bottom: 6px; }
.body-q-sub { font-size: 16px; color: var(--c-ink-500); text-align: center; margin-bottom: 16px; }
.body-svg-wrap {
  position: relative; height: 340px; display: flex; justify-content: center;
  align-items: center; background: var(--c-bg); border-radius: var(--r-md);
}
.body-svg { height: 300px; }
.body-part { fill: var(--c-paper); stroke: var(--c-line-2); stroke-width: 2; cursor: pointer; transition: .2s; }
.body-part:hover { fill: var(--c-primary-l); stroke: var(--c-primary); }
.body-part.active { fill: var(--c-primary); stroke: var(--c-primary-d); }
.body-tag {
  position: absolute; background: var(--c-primary); color: #fff;
  padding: 6px 14px; border-radius: var(--r-pill); font-weight: 700; font-size: 14px;
}
.body-tag.head { top: 18px; left: 50%; transform: translateX(-50%); }
.body-tag.chest { top: 140px; right: 8px; }
.body-tag.belly { top: 230px; left: 8px; }

/* 科室推荐 chips */
.body-suggest { margin-top: 16px; padding: 16px; background: var(--c-accent-l); border-radius: var(--r-md); border-left: 6px solid var(--c-accent); }
.body-suggest .lbl { font-size: 16px; color: var(--c-accent-d); font-weight: 700; margin-bottom: 8px; display: block; }
.deck { display: flex; flex-wrap: wrap; gap: 10px; }
.dept-chip {
  padding: 10px 20px; background: var(--c-accent); color: #fff;
  border-radius: var(--r-pill); font-size: 18px; font-weight: 700; cursor: pointer; transition: .2s;
  display: inline-flex; align-items: center; gap: 8px;
  border: none; font-family: inherit; line-height: 1.4;
}
.dept-chip:hover { background: var(--c-accent-d); transform: translateY(-1px); }
.chip-conf { font-size: 13px; opacity: .85; font-weight: 500; }

/* ── 加载态 ── */
.loading-card { padding: 24px; margin-bottom: 24px; }
.loading-msg { text-align: center; color: var(--c-primary); margin-top: 16px; font-weight: 600; font-size: 16px; }
.stream-progress { display: flex; flex-direction: column; gap: 12px; }
.step { display: flex; align-items: center; gap: 10px; font-size: 16px; }
.step.done { color: var(--c-ink-500); }
.step.done .step-text { text-decoration: line-through; opacity: .7; }
.step.active { color: var(--c-primary); font-weight: 700; }
.step-dot { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0; }
.step.done .step-dot { background: var(--c-primary-l); color: var(--c-primary); }
.step.active .step-dot { background: var(--c-primary); color: #fff; }
.step-dot.spin { animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .4; } }

/* ── 紧急提醒 ── */
.emergency-alert {
  background: #FFF1F0; border: 2px solid #FF4D4F; border-radius: 12px;
  padding: 20px; margin-bottom: 24px; display: flex; gap: 14px; align-items: flex-start;
}
.emergency-icon { font-size: 32px; flex-shrink: 0; }
.emergency-title { font-size: 20px; font-weight: 800; color: #FF4D4F; margin-bottom: 6px; }
.emergency-body { font-size: 16px; color: #820014; line-height: 1.7; }

/* ── 分析推理 ── */
.reasoning-card { padding: 20px; margin-bottom: 24px; border-left: 6px solid var(--c-primary); }
.reason-row { padding: 12px 0; }
.reason-row + .reason-row { border-top: 1px dashed var(--c-line-2); }
.reason-dept-row { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.reason-dept { font-size: 18px; font-weight: 800; color: var(--c-ink-800); }
.reason-conf {
  font-size: 13px; font-weight: 700; color: var(--c-primary); background: var(--c-primary-l);
  padding: 2px 10px; border-radius: var(--r-pill);
}
.reason-text { font-size: 16px; color: var(--c-ink-600); line-height: 1.8; margin: 0; }

/* ── OTC 用药 ── */
.med-card { padding: 20px; margin-bottom: 24px; border-left: 6px solid #52C41A; }
.med-badge { font-size: 12px; background: #52C41A; color: #fff; padding: 2px 12px; border-radius: 4px; margin-left: 8px; vertical-align: middle; }
.med-disclaimer { color: #8C8C8C; font-size: 14px; margin-bottom: 16px; line-height: 1.6; }
.med-item { padding: 14px 0; }
.med-item + .med-item { border-top: 1px dashed #D9D9D9; }
.med-name { font-size: 20px; font-weight: 700; color: #1A1A1A; margin-bottom: 4px; }
.med-detail { font-size: 16px; margin-top: 4px; color: var(--c-ink-600); line-height: 1.7; }
.med-detail .label { font-weight: 700; color: var(--c-ink-700); }
.med-detail.caution { color: #D46B08; background: #FFF7E6; padding: 8px 12px; border-radius: 6px; margin-top: 6px; }
.med-detail.contraind { color: #CF1322; font-weight: 500; }

/* ── 老年注意事项 ── */
.precaution-card { padding: 20px; margin-bottom: 24px; border-left: 6px solid #FA8C16; }
.precaution-text { font-size: 16px; line-height: 1.9; color: var(--c-ink-700); }

/* ── 生活建议 ── */
.advice-card { padding: 20px; margin-bottom: 24px; border-left: 6px solid var(--c-accent); }
.advice-text { font-size: 16px; line-height: 1.9; color: var(--c-ink-700); }

/* ── 通用 section title ── */
.card-section-title { font-family: "Noto Serif SC", serif; font-size: 20px; font-weight: 900; margin-bottom: 14px; color: var(--c-ink-800); }

/* ── 引擎标签 ── */
.engine-badge { text-align: center; padding: 16px 0 8px; }
.badge-ai, .badge-rule {
  display: inline-block; font-size: 13px; font-weight: 600; padding: 4px 16px;
  border-radius: var(--r-pill);
}
.badge-ai { color: var(--c-primary); background: var(--c-primary-l); }
.badge-rule { color: var(--c-ink-300); background: var(--c-bg); }

/* ── 语音 ── */
.voice-btn {
  width: 144px; height: 144px; border-radius: 50%; margin: 0 auto;
  background: linear-gradient(135deg, var(--c-primary), var(--c-primary-d));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 64px; box-shadow: 0 12px 40px rgba(184,69,31,.4);
  cursor: pointer; transition: .2s; user-select: none;
}
.voice-btn:active { transform: scale(.94); }
.voice-btn.listening { animation: ring 1.6s ease-out infinite; }
@keyframes ring {
  0% { box-shadow: 0 0 0 0 rgba(184,69,31,.6); }
  100% { box-shadow: 0 0 0 40px rgba(184,69,31,0); }
}
.voice-help {
  padding: 18px; background: var(--c-gold-bg); border-radius: var(--r-lg);
  border: 2px dashed var(--c-gold-l); text-align: left; max-width: 360px; margin: 0 auto;
}
.voice-help .h { font-size: 18px; font-weight: 800; color: var(--c-gold); margin-bottom: 8px; }
.voice-help ul { padding-left: 20px; font-size: 16px; color: var(--c-ink-700); line-height: 2.2; }
</style>
