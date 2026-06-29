<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const app = useAppStore()

// ========== 登录表单状态 ==========
const activeTab = ref<'sms' | 'phone'>('sms')
const phone = ref('')
const password = ref('')
const loading = ref(false)
const agreed = ref(true)

// ========== 验证码登录 ==========
const smsPhone = ref('')
const smsCode = ref('')
const smsLoading = ref(false)
const smsAgreed = ref(true)
const smsCountdown = ref(0)
let smsTimer: ReturnType<typeof setInterval> | null = null

async function handleSendCode() {
  if (!smsPhone.value) return ElMessage.warning('请输入手机号')
  if (smsPhone.value.length !== 11) return ElMessage.warning('请输入11位手机号')
  try {
    await authApi.sendSmsCode(smsPhone.value)
    ElMessage.success('验证码已发送')
    smsCountdown.value = 60
    smsTimer = setInterval(() => {
      smsCountdown.value--
      if (smsCountdown.value <= 0 && smsTimer) {
        clearInterval(smsTimer)
        smsTimer = null
      }
    }, 1000)
  } catch (e: any) {
    ElMessage.error(e?.message || '验证码发送失败')
  }
}

async function handleSmsLogin() {
  if (!smsAgreed.value) return ElMessage.warning('请阅读并同意用户协议')
  if (!smsPhone.value) return ElMessage.warning('请输入手机号')
  if (smsPhone.value.length !== 11) return ElMessage.warning('请输入11位手机号')
  if (!smsCode.value) return ElMessage.warning('请输入验证码')
  if (smsCode.value.length !== 6) return ElMessage.warning('验证码为6位数字')
  smsLoading.value = true
  try {
    await userStore.smsLogin(smsPhone.value, smsCode.value)
    ElMessage.success('欢迎回来')
    router.push('/home')
  } catch (e: any) {
    ElMessage.error(e?.message || '登录失败')
  } finally {
    smsLoading.value = false
  }
}

async function handleLogin() {
  if (!agreed.value) return ElMessage.warning('请阅读并同意用户协议')
  if (!phone.value) return ElMessage.warning('请输入手机号')
  if (phone.value.length !== 11) return ElMessage.warning('请输入11位手机号')
  if (!password.value) return ElMessage.warning('请输入密码')
  loading.value = true
  try {
    await userStore.login(phone.value, password.value)
    ElMessage.success('欢迎回来')
    router.push('/home')
  } catch (e: any) {
    ElMessage.error(e?.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// ========== 支付宝 OAuth 登录 ==========
const ALIPAY_OAUTH_URL = 'https://openauth.alipay.com/oauth2/publicAppAuthorize.htm'
const ALIPAY_APP_ID = '9021000164696230'
const ALIPAY_REDIRECT_URI = encodeURIComponent(window.location.origin + '/auth/callback')

function goAlipayLogin() {
  window.location.href = `${ALIPAY_OAUTH_URL}?app_id=${ALIPAY_APP_ID}&scope=auth_user&redirect_uri=${ALIPAY_REDIRECT_URI}`
}

// ========== 第三方登录（假数据） ==========
function goWxLogin() {
  ElMessage.info('微信登录功能开发中，敬请期待')
}

function goUnionLogin() {
  ElMessage.info('银联认证功能开发中，敬请期待')
}

// ========== 用户故事轮播 ==========
const stories = [
  { tag: '真实故事', q: '"妈终于肯自己用 App 挂号了，还给我发了语音说\'我也会了\'"', who: '陈女士 · 北京 · 68岁母亲' },
  { tag: '真实故事', q: '"上次妈半夜发烧，我在外地出差，是陪诊员王姐 15 分钟到家的"', who: '陈女士 · 北京 · 女儿' },
  { tag: '真实故事', q: '"挂号、缴费、查报告，一个 App 全搞定，字大看得清"', who: '王秀英奶奶 · 68岁 · 北京' },
]
const storyIdx = ref(0)
let storyTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  storyTimer = setInterval(() => {
    storyIdx.value = (storyIdx.value + 1) % stories.length
  }, 6000)
})

onUnmounted(() => {
  if (storyTimer) clearInterval(storyTimer)
  if (smsTimer) clearInterval(smsTimer)
})

</script>

<template>
  <div class="scene">
    <!-- 装饰水印 -->
    <div class="watermark wm1 serif">仁</div>
    <div class="watermark wm2 serif">守</div>
    <div class="watermark wm3 serif">安</div>

    <!-- 飘落银杏叶 -->
    <div class="leaves">
      <div v-for="i in 8" :key="i" :class="['leaf', `l${i}`]">
        <svg viewBox="0 0 100 100">
          <path d="M50 8 C20 30, 18 60, 50 92 C82 60, 80 30, 50 8 Z"
                :fill="i % 3 === 0 ? '#C28840' : i % 3 === 1 ? '#1F4D3A' : '#B8451F'"
                :opacity="0.5 + (i % 5) * 0.1" />
          <path v-if="i % 2 === 0" d="M50 14 L50 88" stroke="#8E5E20" stroke-width="1.2" fill="none" opacity=".6" />
        </svg>
      </div>
    </div>

    <!-- 慢速光束 -->
    <div class="beam b1"></div>
    <div class="beam b2"></div>
    <div class="beam b3"></div>

    <!-- 顶部状态条 -->
    <div class="topbar">
      <div class="left">
        <span class="dot"></span>
        <span>系统运行中 · 今日服务 <b class="stat-num">12,847</b> 人次 · 子女端同步正常</span>
      </div>
      <div class="right">
        <span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2 L12 22 M2 12 L22 12" />
          </svg>
          无障碍服务
        </span>
        <span class="sep"></span>
        <span>客服热线 <span class="tel">400-808-1985</span></span>
      </div>
    </div>

    <!-- 故事卡（左侧悬浮） -->
    <div class="story-card">
      <span class="tag">真实故事</span>
      <div class="q">{{ stories[storyIdx].q }}</div>
      <div class="who">
        <span class="av">{{ stories[storyIdx].who.charAt(0) }}</span>
        <span>{{ stories[storyIdx].who }}</span>
      </div>
    </div>

    <!-- 主舞台 -->
    <div class="stage">
      <!-- 左侧品牌区 -->
      <div class="brand-side">
        <div class="logo-row">
          <div class="badge">
            <span class="yin serif">医</span>
            <span class="seal-dot brush">福</span>
          </div>
          <div class="word">
            <span class="zh serif">银发通</span>
            <span class="en display">YINFA·TONG · FOR THE GOLDEN YEARS</span>
          </div>
        </div>

        <div class="slogan">
          <div class="line1 brush">
            让长者看病，<br>
            少一份<span class="red">慌张</span>，<br>
            多一份<span class="green">从容</span>。
          </div>
          <div class="line2 serif">陪 你 把 每 次 就 医 ， 走 慢 一 点</div>
          <div class="en-line fraunces">A hospital companion, <b>made with patience</b>, for those we love most.</div>
        </div>

        <div class="stamps">
          <div class="stamp-block">
            <div class="stamp-ink serif">适老</div>
            <div class="cap serif">设计</div>
          </div>
          <div class="stamp-block">
            <div class="stamp-ink gold serif">三甲</div>
            <div class="cap serif">认证</div>
          </div>
          <div class="stamp-block">
            <div class="stamp-ink green serif">医保</div>
            <div class="cap serif">直通</div>
          </div>
          <div class="quote">
            <div class="t serif">「父母在，人生尚有来处；<br>父母去，人生只剩归途。」</div>
            <div class="by">— 银发通 · 第 1,283 天</div>
          </div>
        </div>

        <div class="stats">
          <div class="cell">
            <div class="n fraunces">186<em>家</em></div>
            <div class="l">三甲医院直连</div>
          </div>
          <div class="cell">
            <div class="n fraunces">380<em>万</em></div>
            <div class="l">长者用户信赖</div>
          </div>
          <div class="cell">
            <div class="n fraunces">4.9<em>★</em></div>
            <div class="l">App Store 评分</div>
          </div>
        </div>
      </div>

      <!-- 右侧表单区 -->
      <div class="auth-side">
        <div class="auth-card">
          <div class="auth-head">
            <div class="hello">WELCOME BACK</div>
            <h2>欢迎回家，<span class="b">长者朋友</span> 👋</h2>
            <div class="sub">登录后可继续上次挂号、查看候诊进度、呼叫陪诊员</div>
          </div>

          <!-- Tab 切换 -->
          <div class="tab-row">
            <div :class="['tb', { on: activeTab === 'sms' }]" @click="activeTab = 'sms'">
              <span class="ic">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="5" y="2" width="14" height="20" rx="3" />
                  <circle cx="12" cy="18" r="1" fill="currentColor" />
                </svg>
              </span>
              验证码登录
            </div>
            <div :class="['tb', { on: activeTab === 'phone' }]" @click="activeTab = 'phone'">
              <span class="ic">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 1a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2V6a5 5 0 0 0-5-5zM9 6a3 3 0 0 1 6 0v3H9V6z" />
                </svg>
              </span>
              密码登录
            </div>
          </div>

          <!-- 验证码登录面板 -->
          <div v-show="activeTab === 'sms'" class="panel">
            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="5" y="2" width="14" height="20" rx="3" />
                    <circle cx="12" cy="18" r="1" fill="currentColor" />
                  </svg>
                </span>
                <span class="prel">+86</span>
                <input v-model="smsPhone" type="tel" placeholder="请输入手机号" maxlength="11" />
              </div>
            </div>
            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="10" rx="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </span>
                <input v-model="smsCode" type="text" placeholder="请输入验证码" maxlength="6" style="letter-spacing: 4px;" />
                <div class="suf">
                  <button
                    class="vcode"
                    :class="{ cd: smsCountdown > 0 }"
                    :disabled="smsCountdown > 0"
                    @click="handleSendCode"
                  >
                    {{ smsCountdown > 0 ? `${smsCountdown}s` : '获取验证码' }}
                  </button>
                </div>
              </div>
            </div>
            <div class="form-row">
              <label class="check">
                <input v-model="smsAgreed" type="checkbox" />
                <span class="box"></span>
                7 天内自动登录
              </label>
              <a href="javascript:void(0)">遇到问题？</a>
            </div>
            <button class="submit" :disabled="smsLoading" @click="handleSmsLogin">
              {{ smsLoading ? '请稍候...' : '登 录' }}
            </button>
            <div class="foot">
              首次登录自动注册 ·
              <a href="javascript:void(0)" @click="router.push('/register')">账号密码注册</a>
            </div>
          </div>

          <!-- 密码登录面板 -->
          <div v-show="activeTab === 'phone'" class="panel">
            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="5" y="2" width="14" height="20" rx="3" />
                    <circle cx="12" cy="18" r="1" fill="currentColor" />
                  </svg>
                </span>
                <span class="prel">+86</span>
                <input v-model="phone" type="tel" placeholder="请输入手机号" maxlength="11" />
              </div>
            </div>
            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2V6a5 5 0 0 0-5-5zM9 6a3 3 0 0 1 6 0v3H9V6z" />
                  </svg>
                </span>
                <input v-model="password" type="password" placeholder="请输入登录密码" />
              </div>
            </div>
            <div class="form-row">
              <label class="check">
                <input v-model="agreed" type="checkbox" />
                <span class="box"></span>
                7 天内自动登录
              </label>
              <a href="javascript:void(0)">遇到问题？</a>
            </div>
            <button class="submit" :disabled="loading" @click="handleLogin">
              {{ loading ? '请稍候...' : '登 录' }}
            </button>
            <div class="foot">
              还没账号？
              <a href="javascript:void(0)" @click="router.push('/register')">立即注册</a>
              ·
              <a href="javascript:void(0)">忘记密码？</a>
            </div>
          </div>

          <!-- 协议 -->
          <div class="agree">
            <span class="badge-ok">✓</span>
            <span>登录即表示您已阅读并同意
              <a href="javascript:void(0)">《银发通用户协议》</a>、
              <a href="javascript:void(0)">《适老化服务承诺书》</a> 和
              <a href="javascript:void(0)">《隐私政策》</a>。
              我们承诺：不读取通讯录、不读取短信、仅在就医必需时使用位置。
            </span>
          </div>

          <!-- 第三方登录 -->
          <div class="third">
            <div class="hd">
              <div class="ln"></div>
              <div class="t serif">其 他 登 录 方 式</div>
              <div class="ln"></div>
            </div>
            <div class="row">
              <div class="btn" @click="goWxLogin">
                <svg viewBox="0 0 24 24">
                  <path fill="#1AAD19" d="M9.5 4C5.36 4 2 7.36 2 11.5c0 2.4 1.16 4.54 2.96 5.86L4 21l3.84-2.04c.52.14 1.08.22 1.66.22 4.14 0 7.5-3.36 7.5-7.5C17 7.36 13.64 4 9.5 4z" />
                </svg>
                微信一键登录
              </div>
              <div class="btn" @click="goAlipayLogin">
                <svg viewBox="0 0 24 24">
                  <path fill="#1677FF" d="M18 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z" />
                </svg>
                支付宝登录
              </div>
              <div class="btn" @click="goUnionLogin">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M3 12h18 M12 3a14 14 0 0 1 0 18 M12 3a14 14 0 0 0 0 18" />
                </svg>
                银联认证
              </div>
            </div>
          </div>

          <!-- 安全徽章 -->
          <div class="safety">
            <span class="ok">● 等保三级</span>
            <span class="ok">● 隐私合规</span>
            <span class="ok">● 国密 SM4</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右下角悬浮助手 -->
    <div class="helper">
      <div class="lbl">不会操作？点这里 👆</div>
      <div class="b" title="语音客服">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2 M12 19v4 M8 23h8" />
        </svg>
      </div>
      <div class="b hot" title="人工陪诊">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============ 容器与背景 ============ */
.scene {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(1200px 800px at 12% 18%, rgba(194,136,64,.18), transparent 60%),
    radial-gradient(1000px 700px at 88% 12%, rgba(31,77,58,.16), transparent 60%),
    radial-gradient(900px 700px at 50% 100%, rgba(184,69,31,.10), transparent 60%),
    linear-gradient(180deg, #F5EBD8 0%, #EFE2C8 100%);
}

/* 噪点纸纹 */
.scene::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: .35;
  mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.55 0 0 0 0 0.46 0 0 0 0 0.36 0 0 0 0.10 0'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>");
}

/* 顶部柔光 */
.scene::after {
  content: "";
  position: absolute;
  left: 50%;
  top: -200px;
  width: 1400px;
  height: 600px;
  transform: translateX(-50%);
  pointer-events: none;
  z-index: 1;
  opacity: .5;
  background: radial-gradient(ellipse at center, rgba(255,247,232,.65), transparent 65%);
  filter: blur(20px);
}

/* ============ 飘落的银杏叶粒子 ============ */
.leaves {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  overflow: hidden;
}

.leaf {
  position: absolute;
  top: -80px;
  width: 46px;
  height: 46px;
  opacity: 0;
  will-change: transform, opacity;
}

.leaf svg {
  width: 100%;
  height: 100%;
  display: block;
}

@keyframes drift {
  0%   { transform: translate3d(0,-80px,0) rotate(0deg); opacity: 0; }
  8%   { opacity: .85; }
  50%  { transform: translate3d(140px,55vh,0) rotate(220deg); opacity: .9; }
  92%  { opacity: .8; }
  100% { transform: translate3d(-60px,110vh,0) rotate(540deg); opacity: 0; }
}

@keyframes sway {
  0%, 100% { margin-left: 0; }
  50%      { margin-left: 60px; }
}

.leaf.l1 { left: 8%;  animation: drift 22s linear infinite, sway 6s ease-in-out infinite; animation-delay: 0s; }
.leaf.l2 { left: 22%; animation: drift 28s linear infinite, sway 7s ease-in-out infinite; animation-delay: -6s; }
.leaf.l3 { left: 38%; animation: drift 24s linear infinite, sway 5s ease-in-out infinite; animation-delay: -12s; }
.leaf.l4 { left: 55%; animation: drift 30s linear infinite, sway 8s ease-in-out infinite; animation-delay: -3s; }
.leaf.l5 { left: 72%; animation: drift 26s linear infinite, sway 6s ease-in-out infinite; animation-delay: -15s; }
.leaf.l6 { left: 88%; animation: drift 32s linear infinite, sway 7s ease-in-out infinite; animation-delay: -9s; }
.leaf.l7 { left: 14%; animation: drift 36s linear infinite, sway 5s ease-in-out infinite; animation-delay: -20s; }
.leaf.l8 { left: 48%; animation: drift 25s linear infinite, sway 6s ease-in-out infinite; animation-delay: -18s; }

/* 慢速横向光束 */
.beam {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  z-index: 2;
  pointer-events: none;
  opacity: .5;
  background: linear-gradient(180deg, transparent, rgba(242,221,176,.7), transparent);
  filter: blur(1px);
}

.beam.b1 { left: 18%; animation: beam-move 18s linear infinite; }
.beam.b2 { left: 64%; animation: beam-move 24s linear infinite; animation-delay: -8s; }
.beam.b3 { left: 82%; animation: beam-move 30s linear infinite; animation-delay: -14s; }

@keyframes beam-move {
  0%   { transform: translateY(-100%); opacity: 0; }
  10%  { opacity: .55; }
  90%  { opacity: .55; }
  100% { transform: translateY(100%); opacity: 0; }
}

/* 几道书法水印 */
.watermark {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  color: rgba(31,77,58,.045);
  line-height: 1;
  user-select: none;
}

.wm1 { top: 6%; left: 4%; font-size: 260px; transform: rotate(-8deg); }
.wm2 { bottom: 4%; right: 4%; font-size: 340px; transform: rotate(6deg); color: rgba(184,69,31,.045); }
.wm3 { top: 38%; right: 42%; font-size: 180px; transform: rotate(-3deg); color: rgba(194,136,64,.05); }

/* ============ 顶部状态条 ============ */
.topbar {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 48px;
  color: var(--c-ink-700);
  font-size: 13px;
  font-weight: 700;
}

.topbar .left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.topbar .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-primary);
  box-shadow: 0 0 0 3px rgba(184,69,31,.18);
  animation: blink 1.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: .35; }
}

.stat-num {
  color: var(--c-primary);
  font-family: 'Bebas Neue', sans-serif;
  letter-spacing: 1px;
}

.topbar .right {
  display: flex;
  align-items: center;
  gap: 22px;
  color: var(--c-ink-500);
}

.topbar .right span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.topbar .sep {
  width: 1px;
  height: 12px;
  background: var(--c-line);
}

.topbar .tel {
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 600;
  color: var(--c-primary);
  font-size: 14px;
}

/* ============ 主舞台 ============ */
.stage {
  position: relative;
  z-index: 5;
  display: grid;
  grid-template-columns: 1.15fr .85fr;
  gap: 48px;
  align-items: center;
  padding: 24px 64px 56px;
  min-height: calc(100vh - 60px);
}

@media (max-width: 1100px) {
  .stage {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 16px 24px 40px;
  }
}

/* 左侧品牌区 */
.brand-side {
  position: relative;
  padding: 20px 12px;
}

.brand-side .logo-row {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 30px;
}

.logo-row .badge {
  width: 84px;
  height: 84px;
  border-radius: 22px;
  background: linear-gradient(160deg, var(--c-primary) 0%, var(--c-primary-d) 100%);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12px 32px -10px rgba(184,69,31,.55), inset 0 1px 0 rgba(255,255,255,.2);
  position: relative;
  flex-shrink: 0;
}

.logo-row .badge::after {
  content: "";
  position: absolute;
  inset: 6px;
  border: 1px solid rgba(255,247,232,.18);
  border-radius: 16px;
  pointer-events: none;
}

.logo-row .badge .yin {
  font-weight: 900;
  font-size: 36px;
  line-height: 1;
  letter-spacing: -1px;
  transform: translateY(-1px);
}

.logo-row .badge .seal-dot {
  position: absolute;
  right: -4px;
  bottom: -4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--c-gold);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  border: 2px solid var(--c-bg);
}

.logo-row .word {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-row .zh {
  font-weight: 900;
  font-size: 32px;
  letter-spacing: 4px;
  color: var(--c-ink-900);
  line-height: 1;
}

.logo-row .en {
  font-size: 13px;
  color: var(--c-gold);
  letter-spacing: 2.5px;
  margin-top: 6px;
}

/* 大标语 */
.slogan {
  position: relative;
  margin-bottom: 24px;
}

.slogan .line1 {
  font-size: 78px;
  line-height: 1.05;
  color: var(--c-ink-900);
  letter-spacing: 2px;
}

.slogan .line1 .red {
  color: var(--c-primary);
  position: relative;
  display: inline-block;
}

.slogan .line1 .red::after {
  content: "";
  position: absolute;
  left: -4px;
  right: -4px;
  bottom: 6px;
  height: 14px;
  background: rgba(184,69,31,.12);
  z-index: -1;
  border-radius: 4px;
}

.slogan .line1 .green {
  color: var(--c-accent);
  position: relative;
  display: inline-block;
}

.slogan .line1 .green::after {
  content: "";
  position: absolute;
  left: -4px;
  right: -4px;
  bottom: 6px;
  height: 14px;
  background: rgba(31,77,58,.14);
  z-index: -1;
  border-radius: 4px;
}

.slogan .line2 {
  margin-top: 12px;
  font-weight: 500;
  font-size: 30px;
  color: var(--c-ink-700);
  letter-spacing: 6px;
}

.slogan .en-line {
  margin-top: 18px;
  font-weight: 500;
  font-size: 18px;
  color: var(--c-ink-500);
  letter-spacing: 1px;
}

.slogan .en-line b {
  font-weight: 600;
  color: var(--c-primary);
  font-style: italic;
}

/* 印章组 */
.stamps {
  display: flex;
  gap: 14px;
  margin-top: 32px;
  align-items: flex-end;
}

.stamp-block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.stamp-ink {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: var(--c-primary);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 22px;
  box-shadow: 0 4px 12px -4px rgba(184,69,31,.45);
  transform: rotate(-3deg);
  position: relative;
}

.stamp-ink.gold {
  background: var(--c-gold);
  box-shadow: 0 4px 12px -4px rgba(194,136,64,.45);
  transform: rotate(2deg);
}

.stamp-ink.green {
  background: var(--c-accent);
  box-shadow: 0 4px 12px -4px rgba(31,77,58,.45);
  transform: rotate(-1deg);
}

.stamp-ink .lbl {
  font-weight: 900;
  font-size: 11px;
  margin-top: 2px;
}

.stamp-block .cap {
  font-size: 11px;
  color: var(--c-ink-500);
  font-weight: 700;
  letter-spacing: 1px;
  writing-mode: vertical-rl;
}

.stamps .quote {
  margin-left: 20px;
  padding: 14px 18px;
  border-left: 3px solid var(--c-primary);
  background: rgba(255,252,245,.6);
  border-radius: 0 12px 12px 0;
  backdrop-filter: blur(6px);
  max-width: 340px;
}

.stamps .quote .t {
  font-size: 15px;
  color: var(--c-ink-700);
  line-height: 1.7;
}

.stamps .quote .by {
  margin-top: 6px;
  font-size: 11px;
  color: var(--c-ink-500);
  font-weight: 700;
  letter-spacing: 1px;
}

/* 数据条 */
.stats {
  margin-top: 42px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  background: rgba(255,252,245,.7);
  border-radius: 18px;
  padding: 18px 8px;
  backdrop-filter: blur(8px);
  border: 1px solid rgba(216,200,168,.4);
  max-width: 560px;
}

.stats .cell {
  padding: 0 18px;
  border-right: 1px dashed var(--c-line-2);
  text-align: left;
}

.stats .cell:last-child {
  border-right: 0;
}

.stats .cell .n {
  font-weight: 600;
  font-size: 36px;
  color: var(--c-accent);
  line-height: 1;
  letter-spacing: -.5px;
}

.stats .cell .n em {
  font-style: normal;
  font-size: 18px;
  color: var(--c-gold);
  margin-left: 2px;
}

.stats .cell .l {
  font-size: 12px;
  color: var(--c-ink-500);
  font-weight: 700;
  letter-spacing: 1px;
  margin-top: 6px;
}

/* ============ 右侧表单区 ============ */
.auth-side {
  position: relative;
}

.auth-card {
  position: relative;
  background: #FFFCF5;
  border-radius: 28px;
  padding: 40px 44px 36px;
  box-shadow: var(--shadow-3);
  border: 1px solid rgba(216,200,168,.5);
  overflow: hidden;
}

.auth-card::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 5px;
  background: linear-gradient(90deg, var(--c-primary) 0%, var(--c-gold) 50%, var(--c-accent) 100%);
}

.auth-card::after {
  content: "";
  position: absolute;
  right: -30px;
  top: -30px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(194,136,64,.18), transparent 70%);
  pointer-events: none;
}

.auth-head {
  margin-bottom: 28px;
  position: relative;
}

.auth-head .hello {
  font-size: 13px;
  color: var(--c-gold);
  font-weight: 700;
  letter-spacing: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.auth-head .hello::before {
  content: "";
  width: 24px;
  height: 1px;
  background: var(--c-gold);
}

.auth-head h2 {
  font-family: "Noto Serif SC", serif;
  font-weight: 900;
  font-size: 34px;
  color: var(--c-ink-900);
  letter-spacing: 1px;
  line-height: 1.2;
}

.auth-head h2 .b {
  color: var(--c-primary);
}

.auth-head .sub {
  margin-top: 8px;
  font-size: 14px;
  color: var(--c-ink-500);
  font-weight: 500;
}

/* tab 切换 */
.tab-row {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  background: rgba(245,235,216,.6);
  border-radius: 14px;
  padding: 5px;
  position: relative;
}

.tab-row .tb {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--c-ink-500);
  border-radius: 10px;
  cursor: pointer;
  transition: all .25s;
  position: relative;
  letter-spacing: 1px;
}

.tab-row .tb.on {
  background: #FFFCF5;
  color: var(--c-ink-900);
  box-shadow: 0 2px 6px rgba(0,0,0,.06);
}

.tab-row .tb .ic {
  display: inline-block;
  width: 14px;
  height: 14px;
  vertical-align: -2px;
  margin-right: 6px;
}

.tab-row .tb .ic svg {
  width: 100%;
  height: 100%;
}

/* 表单 */
.form {
  position: relative;
}

.panel {
  animation: fadeUp .4s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.field {
  position: relative;
  margin-bottom: 14px;
}

.field .row {
  display: flex;
  align-items: center;
  gap: 0;
  height: 62px;
  background: #FFFCF5;
  border: 2px solid var(--c-line);
  border-radius: 14px;
  padding: 0 18px;
  transition: all .2s;
}

.field .row:focus-within {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 4px rgba(184,69,31,.08);
  background: #FFFEF9;
}

.field .row .ic {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  color: var(--c-ink-500);
}

.field .row .ic svg {
  width: 100%;
  height: 100%;
}

.field .row .prel {
  padding-right: 12px;
  margin-right: 12px;
  border-right: 1px solid var(--c-line);
  font-weight: 700;
  color: var(--c-ink-700);
  font-size: 17px;
}

.field .row input {
  flex: 1;
  border: 0;
  background: transparent;
  outline: 0;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 18px;
  color: var(--c-ink-900);
  font-weight: 600;
  letter-spacing: 1px;
  height: 100%;
  min-width: 0;
}

.field .row input::placeholder {
  color: var(--c-ink-300);
  font-weight: 500;
  letter-spacing: 0;
}

.field .row .suf {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.field .row .vcode {
  height: 42px;
  padding: 0 16px;
  border-radius: 10px;
  background: var(--c-primary-bg);
  color: var(--c-primary);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1px;
  border: 0;
  cursor: pointer;
  transition: all .2s;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.field .row .vcode:hover {
  background: var(--c-primary);
  color: #FFF7E8;
}

.field .row .vcode.cd {
  background: var(--c-line);
  color: var(--c-ink-500);
  cursor: default;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 6px 4px 18px;
  font-size: 14px;
  color: var(--c-ink-500);
}

.form-row .check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
}

.form-row .check input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.form-row .check .box {
  width: 18px;
  height: 18px;
  border: 2px solid var(--c-line-2);
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s;
  background: #FFFCF5;
}

.form-row .check input:checked + .box {
  background: var(--c-primary);
  border-color: var(--c-primary);
}

.form-row .check input:checked + .box::after {
  content: "";
  width: 5px;
  height: 9px;
  border: solid #FFF7E8;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(-1px, -1px);
}

.form-row a {
  color: var(--c-primary);
  text-decoration: none;
  font-weight: 700;
}

.form-row a:hover {
  text-decoration: underline;
}

/* 主按钮 */
.submit {
  width: 100%;
  height: 64px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-d) 100%);
  color: #FFF7E8;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 24px -8px rgba(184,69,31,.45);
  transition: transform .15s, box-shadow .2s;
}

.submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 32px -8px rgba(184,69,31,.55);
}

.submit:active {
  transform: translateY(0);
}

.submit::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent);
  transition: left .6s;
}

.submit:hover::after {
  left: 140%;
}

.submit:disabled {
  opacity: .6;
  cursor: not-allowed;
  transform: none;
}

.foot {
  text-align: center;
  margin-top: 18px;
  font-size: 14px;
  color: var(--c-ink-500);
}

.foot a {
  color: var(--c-primary);
  font-weight: 700;
  text-decoration: none;
}

.foot a:hover {
  text-decoration: underline;
}

/* 协议 */
.agree {
  margin-top: 18px;
  padding: 14px 16px;
  background: rgba(245,235,216,.5);
  border-radius: 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 12px;
  color: var(--c-ink-500);
  line-height: 1.7;
}

.agree .badge-ok {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  background: var(--c-accent);
  color: #FFF7E8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 900;
  margin-top: 1px;
}

.agree a {
  color: var(--c-primary);
  text-decoration: none;
  font-weight: 700;
}

/* 第三方登录 */
.third {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px dashed var(--c-line-2);
}

.third .hd {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.third .hd .ln {
  flex: 1;
  height: 1px;
  background: var(--c-line-2);
}

.third .hd .t {
  font-size: 12px;
  color: var(--c-ink-500);
  font-weight: 700;
  letter-spacing: 3px;
}

.third .row {
  display: flex;
  gap: 12px;
}

.third .btn {
  flex: 1;
  height: 56px;
  border-radius: 14px;
  border: 2px solid var(--c-line);
  background: #FFFCF5;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  color: var(--c-ink-700);
  transition: all .2s;
}

.third .btn:hover {
  border-color: var(--c-gold);
  background: var(--c-gold-bg);
  color: var(--c-ink-900);
}

.third .btn svg {
  width: 22px;
  height: 22px;
}

/* 亲情号登录特殊样式 */
.kin-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--c-accent-bg);
  border-radius: 14px;
  margin-bottom: 20px;
  border: 1px dashed var(--c-accent-l);
}

.kin-banner .av {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--c-accent);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 18px;
  flex-shrink: 0;
}

.kin-banner .info .n {
  font-weight: 900;
  font-size: 16px;
  color: var(--c-ink-900);
}

.kin-banner .info .d {
  font-size: 12px;
  color: var(--c-ink-500);
  margin-top: 2px;
}

.kin-banner .info .d b {
  color: var(--c-primary);
  font-weight: 700;
}

.kin-banner .switch {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-primary);
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 1px;
}

/* 扫码登录 */
.qr-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0 4px;
}

.qr-box {
  width: 200px;
  height: 200px;
  border-radius: 18px;
  background: #FFFCF5;
  padding: 14px;
  box-shadow: inset 0 0 0 2px var(--c-line), 0 6px 20px -8px rgba(0,0,0,.12);
  position: relative;
}

.qr-box .qr {
  width: 100%;
  height: 100%;
  background:
    conic-gradient(from 0deg, var(--c-ink-900) 25%, transparent 25% 50%, var(--c-ink-900) 50% 75%, transparent 75%),
    conic-gradient(from 45deg, var(--c-ink-900) 12.5%, transparent 12.5% 25%, var(--c-ink-900) 25% 37.5%, transparent 37.5% 50%, var(--c-ink-900) 50% 62.5%, transparent 62.5% 75%, var(--c-ink-900) 75% 87.5%, transparent 87.5%);
  background-size: 18px 18px;
  background-color: #FFFCF5;
  border-radius: 10px;
  position: relative;
}

.qr-box .qr::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 50%;
  width: 46px;
  height: 46px;
  background: #FFFCF5;
  border-radius: 8px;
  transform: translate(-50%, -50%);
}

.qr-box .qr::before {
  content: "医";
  position: absolute;
  left: 50%;
  top: 50%;
  width: 46px;
  height: 46px;
  background: var(--c-primary);
  color: #FFF7E8;
  border-radius: 8px;
  transform: translate(-50%, -50%);
  font-family: "Noto Serif SC", serif;
  font-weight: 900;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  box-shadow: 0 4px 12px -4px rgba(184,69,31,.5);
}

.qr-box .corner {
  position: absolute;
  width: 22px;
  height: 22px;
  border: 3px solid var(--c-ink-900);
  border-radius: 4px;
}

.qr-box .corner.tl { top: 8px; left: 8px; border-right: 0; border-bottom: 0; }
.qr-box .corner.tr { top: 8px; right: 8px; border-left: 0; border-bottom: 0; }
.qr-box .corner.bl { bottom: 8px; left: 8px; border-right: 0; border-top: 0; }
.qr-box .corner.br { bottom: 8px; right: 8px; border-left: 0; border-top: 0; }

.qr-hint {
  margin-top: 18px;
  text-align: center;
}

.qr-hint .t {
  font-weight: 700;
  font-size: 15px;
  color: var(--c-ink-700);
  letter-spacing: 1px;
}

.text-primary {
  color: var(--c-primary);
}

.qr-hint .d {
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-ink-500);
}

.qr-hint .d b {
  color: var(--c-primary);
  font-weight: 700;
}

.qr-refresh {
  margin-top: 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-ink-500);
  cursor: pointer;
}

.qr-refresh:hover {
  color: var(--c-primary);
}

/* 安全徽章 */
.safety {
  display: flex;
  gap: 18px;
  justify-content: center;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px dashed var(--c-line-2);
}

.safety span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--c-ink-500);
  font-weight: 700;
  letter-spacing: 1px;
}

.safety .ok {
  color: var(--c-accent);
}

/* 右下角悬浮客服 */
.helper {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

.helper .b {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: #FFFCF5;
  box-shadow: var(--shadow-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all .2s;
  border: 2px solid var(--c-line);
}

.helper .b:hover {
  transform: scale(1.08);
  border-color: var(--c-primary);
}

.helper .b svg {
  width: 24px;
  height: 24px;
  color: var(--c-ink-700);
}

.helper .b.hot {
  background: linear-gradient(135deg, var(--c-primary), var(--c-primary-d));
  border-color: transparent;
  color: #FFF7E8;
  position: relative;
}

.helper .b.hot::after {
  content: "";
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid rgba(184,69,31,.4);
  animation: ring 2.4s infinite;
}

@keyframes ring {
  0%   { transform: scale(1); opacity: .8; }
  100% { transform: scale(1.5); opacity: 0; }
}

.helper .lbl {
  font-size: 11px;
  color: var(--c-ink-500);
  font-weight: 700;
  background: #FFFCF5;
  padding: 4px 10px;
  border-radius: 8px;
  box-shadow: var(--shadow-1);
  border: 1px solid var(--c-line);
  white-space: nowrap;
}

/* 左下客户故事卡片 */
.story-card {
  position: absolute;
  left: -12px;
  bottom: 80px;
  z-index: 5;
  background: #FFFCF5;
  border-radius: 14px;
  padding: 14px 18px;
  width: 300px;
  box-shadow: var(--shadow-2);
  border: 1px solid var(--c-line);
  transform: rotate(-2deg);
  transition: opacity .4s;
}

.story-card .tag {
  display: inline-block;
  padding: 3px 10px;
  background: var(--c-gold-bg);
  color: var(--c-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.story-card .q {
  font-size: 15px;
  color: var(--c-ink-700);
  line-height: 1.7;
}

.story-card .who {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--c-ink-500);
  font-weight: 700;
}

.story-card .who .av {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--c-primary);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .story-card { display: none; }
  .topbar { padding: 12px 16px; font-size: 12px; }
  .topbar .right { display: none; }
  .slogan .line1 { font-size: 48px; }
  .slogan .line2 { font-size: 20px; letter-spacing: 2px; }
  .stamps { flex-wrap: wrap; }
  .stamps .quote { max-width: 100%; }
  .stats { max-width: 100%; }
  .auth-card { padding: 28px 24px 24px; }
  .auth-head h2 { font-size: 26px; }
  .helper { display: none; }
}
</style>
