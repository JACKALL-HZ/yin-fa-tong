<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { doctorApi } from '@/api/doctor'
import { userApi } from '@/api/user'
import { useWeather } from '@/composables/useWeather'
import type { ElderBind, Doctor } from '@/types'
import type { TodoItem, AlertItem, HealthReminderItem } from '@/api/user'

const router = useRouter()
const app = useAppStore()
const user = useUserStore()

const experts = ref<Doctor[]>([])

// 亲情成员 + 提醒数据
const familyMembers = ref<ElderBind[]>([])
const todos = ref<TodoItem[]>([])
const alerts = ref<AlertItem[]>([])
const healthReminders = ref<HealthReminderItem[]>([])

// Hero 区域展示的提醒文案
const heroReminderText = computed(() => {
  // 优先展示紧急待办
  const urgentTodo = todos.value.find(t => t.urgent)
  if (urgentTodo) return urgentTodo.text
  // 其次展示健康提醒
  if (healthReminders.value.length > 0) return healthReminders.value[0].desc
  // 再展示就诊提醒
  const visitAlert = alerts.value.find(a => a.title.includes('今日') || a.title.includes('明日'))
  if (visitAlert) return visitAlert.desc
  return '暂无待办，今天也要好好的'
})

// 实时天气（通过 wttr.in 获取）
const { weather } = useWeather()

// 健康资讯 mock
const articles = [
  { id: 1, tag: '慢病管理', title: '高血压患者夏季用药指南：血压正常也不能擅自停药', source: '健康报' },
  { id: 2, tag: '养生保健', title: '三伏天养生记住这四点：饮食清淡、适当午休、避免贪凉', source: '人民日报' },
  { id: 3, tag: '就医攻略', title: '带父母看病挂什么科？这份挂号指南请收好', source: '丁香医生' },
  { id: 4, tag: '医保新政', title: '2026 年医保异地结算新规：跨省就医可直接结算', source: '国家医保局' },
]

// 热门科室排行 mock
const topDepts = [
  { name: '心血管内科', count: 1286, pct: 100 },
  { name: '神经内科', count: 1102, pct: 86 },
  { name: '骨科', count: 980, pct: 76 },
  { name: '消化内科', count: 845, pct: 66 },
  { name: '眼科', count: 723, pct: 56 },
]

// 服务网格
const services = [
  { name: '预约挂号', desc: '一键挂号 · 四步搞定', icon: '🏥', color: 'primary', span: 'big' },
  { name: '智能导诊', desc: '说出症状 · 精准匹配科室', icon: '🤖', color: 'accent' },
  { name: '在线缴费', desc: '医保实时结算', icon: '💳', color: 'gold' },
  { name: '候诊排队', desc: '实时叫号 · 不慌不忙', icon: '📺', color: 'sky' },
  { name: '体检报告', desc: '上传即解读', icon: '📋', color: 'berry' },
  { name: '陪诊服务', desc: '专人陪同 · 子女放心', icon: '🤝', color: 'cream' },
  { name: '健康提醒', desc: '用药/复诊准时提醒', icon: '⏰', color: 'rose' },
  { name: '长辈管理', desc: '绑定父母 · 远程代办', icon: '👨‍👩‍👧', color: 'accent' },
  { name: '健康资讯', desc: '靠谱医学科普', icon: '📰', color: 'gold' },
]

const fallbackExperts = [
  { doctor_name: '王建华', doctor_title: '主任医师', dept_name: '心血管内科', register_fee: '50', specialty: '冠心病介入治疗' },
  { doctor_name: '林秀梅', doctor_title: '副主任医师', dept_name: '骨科', register_fee: '30', specialty: '关节置换术' },
  { doctor_name: '陈志强', doctor_title: '主任医师', dept_name: '神经内科', register_fee: '50', specialty: '脑血管病急性期治疗' },
  { doctor_name: '赵丽华', doctor_title: '主治医师', dept_name: '眼科', register_fee: '20', specialty: '白内障超声乳化' },
]

const greetName = user.info?.nickname || user.info?.username || '长辈'
const today = new Date()
const dateStr = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`
const weekDay = ['日', '一', '二', '三', '四', '五', '六'][today.getDay()]

onMounted(async () => {
  try {
    const [dr, reminderRes, elderRes] = await Promise.all([
      doctorApi.list({ page: 1, page_size: 4 }),
      userApi.getElderReminders().catch(() => null),
      userApi.listElders().catch(() => null),
    ])
    const list = (dr.data as any)?.data || (dr.data as any)?.items
    if (list && list.length) experts.value = list

    // 亲情成员
    if (elderRes?.data?.data) familyMembers.value = elderRes.data.data

    // 提醒数据
    const rd = reminderRes?.data?.data
    if (rd) {
      todos.value = rd.todos || []
      alerts.value = rd.alerts || []
      healthReminders.value = rd.health_reminders || []
    }
  } catch { /* keep fallback */ }
})

function goService(name: string) {
  const map: Record<string, string> = {
    '预约挂号': '/hospitals', '智能导诊': '/guide', '在线缴费': '/payment',
    '候诊排队': '/queue', '体检报告': '/reports', '陪诊服务': '/volunteers',
    '健康提醒': '/reminders', '长辈管理': '/elders', '健康资讯': '/reminders',
  }
  const path = map[name]
  if (path) router.push(path)
}
</script>

<template>
  <div class="home-page">
    <!-- ====== 1. Hero ====== -->
    <section class="hero grid-hero">
      <div class="hero-left dark-card">
        <span class="pill pill-gold date-pill">{{ dateStr }} 周{{ weekDay }}</span>
        <h1 class="hero-greet serif">早安，<em>{{ greetName }}</em></h1>
        <p class="hero-motto brush">今天也要好好的</p>
        <div class="hero-reminder">
          <span>{{ healthReminders.length > 0 ? healthReminders[0].icon : '🔔' }}</span>
          <span>{{ heroReminderText }}</span>
        </div>
        <div class="hero-ctas">
          <button class="btn-primary" @click="router.push('/reminders')">一键续方</button>
          <button class="btn-outline" style="border-color:rgba(255,247,232,.3);color:var(--c-cream)" @click="router.push('/orders')">就诊安排</button>
        </div>
        <div class="hero-stats">
          <div class="stat-item"><span class="num">12,386</span><span class="stat-lbl">已服务长者</span></div>
          <div class="stat-item"><span class="num">98.6<span class="stat-unit">%</span></span><span class="stat-lbl">满意度</span></div>
          <div class="stat-item"><span class="num">320<span class="stat-unit">+</span></span><span class="stat-lbl">合作医院</span></div>
          <div class="stat-item"><span class="num">7×24<span class="stat-unit">h</span></span><span class="stat-lbl">陪诊服务</span></div>
        </div>
      </div>

      <div class="hero-right">
        <div class="voice-card card" @click="router.push('/guide')">
          <div class="voice-ring"><div class="voice-mic">🎙</div></div>
          <p class="voice-hint">按住说话</p>
          <p class="voice-sub">说出科室或症状即可挂号</p>
        </div>
        <div class="weather-card card">
          <div class="weather-left">
            <span class="weather-temp num">{{ weather.temp }}°</span>
            <span class="weather-cond">{{ weather.condition }}</span>
          </div>
          <div class="weather-right">
            <p class="weather-city" v-if="weather.city">📍 {{ weather.city }}</p>
            <p>{{ weather.clothing }}</p>
            <p class="weather-extra" v-if="weather.humidity">
              湿度 {{ weather.humidity }}%
              <span v-if="weather.wind"> · {{ weather.wind }}</span>
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 2. 服务网格 ====== -->
    <section class="section">
      <div class="sec-head">
        <span class="sec-head-zh">就医服务</span>
        <span class="sec-head-en">Medical Services</span>
      </div>
      <div class="service-grid">
        <div v-for="svc in services" :key="svc.name"
          :class="['svc', `svc-${svc.span || 'normal'}`, `svc-${svc.color}`]"
          @click="goService(svc.name)">
          <span class="svc-icon">{{ svc.icon }}</span>
          <span class="svc-name">{{ svc.name }}</span>
          <span class="svc-desc">{{ svc.desc }}</span>
        </div>
      </div>
    </section>

    <!-- ====== 3. 推荐专家 ====== -->
    <section class="section">
      <div class="sec-head">
        <span class="sec-head-zh">推荐专家</span>
        <span class="sec-head-en">Top Doctors</span>
        <span class="sec-head-more" @click="router.push('/hospitals')">查看全部 →</span>
      </div>
      <div class="expert-grid">
        <div v-for="(doc, idx) in (experts.length ? experts.slice(0, 4) : fallbackExperts)" :key="(doc as any).id || (doc as any).doctor_name"
          class="expert-card card-hover">
          <div class="expert-photo">
            <span class="expert-av">{{ (doc as any).doctor_name?.charAt(0) || '医' }}</span>
          </div>
          <div class="expert-tags"><span class="pill pill-accent">重点专科</span></div>
          <h3 class="expert-name serif">{{ (doc as any).doctor_name }}</h3>
          <p class="expert-title">{{ (doc as any).doctor_title }}</p>
          <p class="expert-dept">{{ (doc as any).dept_name }}</p>
          <div class="expert-stars">⭐ {{ ['4.9','4.8','4.7','4.6'][idx % 4] }}</div>
          <div class="expert-bottom">
            <button class="btn-primary expert-btn" @click.stop="router.push('/hospitals')">预约</button>
            <span class="expert-fee num">¥{{ (doc as any).register_fee }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 4. 健康资讯 ====== -->
    <section class="section">
      <div class="sec-head">
        <span class="sec-head-zh">健康资讯</span>
        <span class="sec-head-en">Health News</span>
      </div>
      <div class="news-layout">
        <div class="card card-hover" style="padding:0;overflow:hidden">
          <div class="news-feat-img"><span style="font-size:64px">📰</span></div>
          <div class="news-feat-body">
            <span class="pill pill-rose" style="display:inline-block;margin-bottom:8px">{{ articles[0].tag }}</span>
            <h3 class="news-feat-title serif">{{ articles[0].title }}</h3>
            <span class="news-feat-meta">{{ articles[0].source }} · 2 小时前</span>
          </div>
        </div>
        <div class="news-list">
          <div v-for="(a, i) in articles.slice(1)" :key="a.id" class="news-item">
            <span class="news-num num">{{ String(i + 2).padStart(2, '0') }}</span>
            <div class="news-item-body">
              <p class="news-item-title">{{ a.title }}</p>
              <span class="news-item-src">{{ a.source }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 5. 热门科室 ====== -->
    <section class="section">
      <div class="card">
        <h3 class="widget-title serif">本周热门科室 <span class="widget-badge num">TOP 5</span></h3>
        <div class="rank-list">
          <div v-for="(d, i) in topDepts" :key="d.name" class="rank-row">
            <span class="rank-num num" :class="i < 3 ? 'rank-top' : ''">{{ i + 1 }}</span>
            <span class="rank-name">{{ d.name }}</span>
            <span class="rank-bar"><span :style="{width:d.pct+'%'}"></span></span>
            <span class="rank-count num">{{ d.count }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 8. Footer ====== -->
    <footer class="home-footer">
      <p class="footer-brand serif">银发通</p>
      <p class="footer-en display">YINFA-TONG</p>
      <p class="footer-icp">© 2026 银发通 · 适老化智慧就医服务平台 · ICP 备 2026000001 号</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page { max-width: 1320px; margin: 0 auto; padding: 32px 32px 80px; }
.section { margin-bottom: 56px; }

/* Hero */
.hero-left {
  display: flex; flex-direction: column; gap: 12px;
  background: linear-gradient(160deg, var(--c-ink-900), #2A2420);
}
.hero-left::after {
  content: "長"; position: absolute; right: 10px; bottom: -30px;
  font-family: "Noto Serif SC", serif; font-size: 200px; font-weight: 900;
  opacity: .04; line-height: 1; pointer-events: none; color: var(--c-cream);
}
.date-pill { align-self: flex-start; }
.hero-greet { font-size: 36px; font-weight: 900; line-height: 1.3; }
.hero-greet em { font-style: normal; color: var(--c-gold); }
.hero-motto { font-size: 28px; color: var(--c-cream); opacity: .85; letter-spacing: 4px; }
.hero-reminder {
  display: flex; align-items: center; gap: 8px; background: rgba(255,247,232,.08);
  padding: 10px 16px; border-radius: var(--r-md); font-size: 14px; color: rgba(255,247,232,.8);
}
.hero-reminder b { color: var(--c-gold); }
.hero-ctas { display: flex; gap: 12px; margin-top: 4px; }
.hero-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  margin-top: 8px; padding-top: 16px; border-top: 1px solid rgba(255,247,232,.1);
}
.stat-item { text-align: center; }
.stat-item .num { font-size: 28px; display: block; color: var(--c-gold); line-height: 1.1; }
.stat-unit { font-size: 16px; }
.stat-lbl { font-size: 11px; color: rgba(255,247,232,.55); font-weight: 500; }

.hero-right { display: flex; flex-direction: column; gap: 16px; }
.voice-card {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 8px; cursor: pointer; background: var(--c-primary-bg); text-align: center;
}
.voice-ring {
  width: 72px; height: 72px; border-radius: 50%; background: var(--c-primary);
  display: flex; align-items: center; justify-content: center; position: relative;
}
.voice-ring::before, .voice-ring::after {
  content: ""; position: absolute; inset: -4px; border-radius: 50%;
  border: 2px solid var(--c-primary); animation: ring 1.8s infinite;
}
.voice-ring::after { animation-delay: .9s; }
.voice-mic { font-size: 30px; }
.voice-hint { font-size: 20px; font-weight: 800; color: var(--c-primary); }
.voice-sub { font-size: 13px; color: var(--c-ink-500); }
.weather-card { display: flex; align-items: center; gap: 16px; padding: 20px 24px; }
.weather-temp { font-size: 42px; color: var(--c-ink-900); line-height: 1; }
.weather-cond { font-size: 14px; color: var(--c-ink-500); display: block; }
.weather-right p { font-size: 13px; color: var(--c-ink-500); line-height: 1.5; }
.weather-city { font-size: 12px; color: var(--c-primary); font-weight: 600; margin-bottom: 2px; }
.weather-extra { font-size: 12px; color: var(--c-ink-400); margin-top: 2px; }

/* Service Grid */
.service-grid {
  display: grid; grid-template-columns: 1.3fr 1fr 1fr 1fr 1fr;
  grid-template-rows: 180px 180px; gap: 16px;
}
.svc {
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); padding: 24px;
  display: flex; flex-direction: column; gap: 6px;
  cursor: pointer; transition: transform .25s, box-shadow .25s;
  position: relative; overflow: hidden;
}
.svc:hover { transform: translateY(-3px); box-shadow: var(--shadow-2); }
.svc-big { grid-row: span 2; justify-content: center; gap: 10px; }
.svc-icon { font-size: 36px; line-height: 1; }
.svc-name { font-weight: 800; font-size: 18px; }
.svc-desc { font-size: 13px; color: var(--c-ink-500); }
.svc-primary { background: var(--c-primary-bg); border-color: var(--c-primary-l); }
.svc-primary .svc-name { color: var(--c-primary); font-size: 22px; }
.svc-primary .svc-desc { color: var(--c-primary-d); }
.svc-accent { background: var(--c-accent-bg); border-color: var(--c-accent-l); }
.svc-gold { background: var(--c-gold-bg); border-color: var(--c-gold-l); }
.svc-sky { background: #EAF0F2; border-color: #CCD8DD; }
.svc-berry { background: #F5E8EB; border-color: #E2CCD2; }
.svc-cream { background: #FBFAF3; border-color: var(--c-cream); }
.svc-rose { background: #FBEFEC; border-color: #F4D2CA; }

/* Experts */
.expert-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.expert-card {
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-lg); padding: 24px; box-shadow: var(--shadow-1);
  text-align: center; position: relative;
}
.expert-photo { margin-bottom: 12px; }
.expert-av {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, var(--c-accent), var(--c-accent-d));
  color: var(--c-cream); display: inline-flex; align-items: center;
  justify-content: center; font-family: "Noto Serif SC", serif;
  font-size: 28px; font-weight: 900;
}
.expert-tags { margin-bottom: 8px; }
.expert-name { font-size: 20px; font-weight: 900; margin-bottom: 4px; }
.expert-title { font-size: 13px; color: var(--c-ink-500); }
.expert-dept { font-size: 13px; color: var(--c-ink-300); margin-bottom: 8px; }
.expert-stars { font-size: 14px; color: var(--c-gold); margin-bottom: 12px; }
.expert-bottom { display: flex; align-items: center; justify-content: center; gap: 12px; }
.expert-btn { padding: 8px 20px; font-size: 14px; }
.expert-fee { font-size: 22px; color: var(--c-primary); }

/* News */
.news-layout { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; }
.news-feat-img {
  height: 180px; background: var(--c-accent-bg);
  display: flex; align-items: center; justify-content: center;
}
.news-feat-body { padding: 24px; }
.news-feat-title { font-size: 22px; font-weight: 900; margin-bottom: 8px; line-height: 1.4; }
.news-feat-meta { font-size: 13px; color: var(--c-ink-300); }
.news-list { display: flex; flex-direction: column; gap: 1px; }
.news-item {
  display: flex; gap: 16px; padding: 16px; cursor: pointer;
  border-radius: var(--r-md); transition: transform .2s, border-color .2s;
  border: 1px solid transparent;
}
.news-item:hover { transform: translateX(4px); border-color: var(--c-primary); }
.news-num { font-size: 28px; color: var(--c-line-2); flex-shrink: 0; width: 36px; }
.news-item-title { font-size: 15px; font-weight: 700; color: var(--c-ink-700); line-height: 1.4; }
.news-item-src { font-size: 12px; color: var(--c-ink-300); }

/* Banners */
.banner-dual { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; }
.banner-card { border-radius: var(--r-xl); padding: 36px; position: relative; overflow: hidden; }
.banner-title { font-size: 28px; font-weight: 900; line-height: 1.3; color: var(--c-cream); }
.banner-desc { font-size: 15px; color: rgba(255,247,232,.75); margin-top: 8px; }

/* Ranking + Widget */
.widget-title { font-size: 22px; font-weight: 900; margin-bottom: 20px; }
.widget-badge {
  font-size: 16px; background: var(--c-gold-bg); color: var(--c-gold);
  padding: 2px 10px; border-radius: var(--r-pill); letter-spacing: 2px; vertical-align: middle;
}
.rank-list { display: flex; flex-direction: column; gap: 14px; }
.rank-row { display: flex; align-items: center; gap: 14px; }
.rank-num { font-size: 24px; width: 32px; text-align: center; color: var(--c-ink-300); }
.rank-top { color: var(--c-gold); }
.rank-name { flex: 1; font-weight: 700; font-size: 15px; }
.rank-bar { width: 120px; height: 6px; background: var(--c-line); border-radius: 3px; overflow: hidden; }
.rank-bar span { display: block; height: 100%; background: var(--c-primary); border-radius: 3px; }
.rank-count { font-size: 20px; color: var(--c-ink-700); width: 50px; text-align: right; }

.health-reminders { display: flex; flex-direction: column; gap: 12px; }
.hrem {
  display: flex; align-items: center; gap: 12px; padding: 12px;
  background: rgba(255,247,232,.06); border-radius: var(--r-md);
}
.hrem-icon { font-size: 24px; flex-shrink: 0; }
.hrem-info { flex: 1; display: flex; flex-direction: column; }
.hrem-title { font-size: 14px; font-weight: 700; color: var(--c-cream); }
.hrem-desc { font-size: 12px; color: rgba(255,247,232,.55); }
.hrem-btn {
  padding: 6px 16px; border-radius: var(--r-pill); font-size: 12px; font-weight: 700;
  border: 1px solid rgba(255,247,232,.2); background: transparent;
  color: var(--c-gold); cursor: pointer; white-space: nowrap;
}
.hrem-btn:hover { background: rgba(255,247,232,.1); }

/* Family */
.family-section { margin-top: 0; }
.family-intro { display: flex; flex-direction: column; justify-content: center; }
.family-cards { display: flex; flex-direction: column; gap: 12px; }
.family-card {
  display: flex; align-items: center; gap: 14px; padding: 16px;
  background: var(--c-paper); border: 1px solid var(--c-line);
  border-radius: var(--r-md); box-shadow: var(--shadow-1); cursor: pointer;
}
.fam-av {
  width: 48px; height: 48px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-weight: 800;
  font-size: 20px; color: #fff; flex-shrink: 0;
}
.fam-av-green { background: var(--c-accent); }
.fam-av-yellow { background: var(--c-gold); }
.fam-info { flex: 1; }
.fam-name { font-size: 16px; font-weight: 800; display: block; }
.fam-rel { font-size: 12px; color: var(--c-ink-500); }
.fam-status { font-size: 11px; color: var(--c-accent); font-weight: 600; }
.fam-status-yellow { color: var(--c-gold); }
.fam-online { width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background: var(--c-accent); }
.dot-yellow { background: var(--c-gold); }

/* Footer */
.home-footer { text-align: center; padding: 48px 0 32px; }
.footer-brand { font-size: 24px; font-weight: 900; color: var(--c-ink-500); letter-spacing: 4px; }
.footer-en { font-size: 14px; color: var(--c-gold); margin-bottom: 8px; }
.footer-icp { font-size: 12px; color: var(--c-ink-300); }
</style>
