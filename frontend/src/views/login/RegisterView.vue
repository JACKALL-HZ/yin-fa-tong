<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const nickname = ref('')
const userType = ref<1 | 2>(1) // 1老年用户 2子女用户
const agreed = ref(false)
const loading = ref(false)

async function handleRegister() {
  if (!agreed.value) return ElMessage.warning('请阅读并同意用户协议')
  if (!phone.value) return ElMessage.warning('请输入手机号')
  if (phone.value.length !== 11) return ElMessage.warning('请输入11位手机号')
  if (!password.value) return ElMessage.warning('请输入密码')
  if (password.value.length < 6) return ElMessage.warning('密码长度不能少于6位')
  if (password.value !== confirmPassword.value) return ElMessage.warning('两次密码输入不一致')

  loading.value = true
  try {
    await userStore.register(
      phone.value,
      password.value,
      nickname.value || undefined,
      userType.value,
    )
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="scene">
    <!-- 装饰水印 -->
    <div class="watermark wm1 serif">仁</div>
    <div class="watermark wm2 serif">守</div>

    <!-- 飘落银杏叶 -->
    <div class="leaves">
      <div v-for="i in 6" :key="i" :class="['leaf', `l${i}`]">
        <svg viewBox="0 0 100 100">
          <path d="M50 8 C20 30, 18 60, 50 92 C82 60, 80 30, 50 8 Z"
                :fill="i % 3 === 0 ? '#C28840' : i % 3 === 1 ? '#1F4D3A' : '#B8451F'"
                :opacity="0.5 + (i % 5) * 0.1" />
        </svg>
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
          <div class="line2 serif">陪 你 把 次 就 医 ， 走 慢 一 点</div>
        </div>

        <div class="features">
          <div class="feat">
            <div class="icon">🏥</div>
            <div class="text">
              <div class="t">186家三甲医院直连</div>
              <div class="d">覆盖全国主要城市</div>
            </div>
          </div>
          <div class="feat">
            <div class="icon">👨‍👩‍👧</div>
            <div class="text">
              <div class="t">子女代办一键挂号</div>
              <div class="d">远程为长辈预约就医</div>
            </div>
          </div>
          <div class="feat">
            <div class="icon">🤝</div>
            <div class="text">
              <div class="t">专业陪诊全程陪伴</div>
              <div class="d">让就医不再孤单</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧注册表单 -->
      <div class="auth-side">
        <div class="auth-card">
          <div class="auth-head">
            <div class="hello">CREATE ACCOUNT</div>
            <h2>注册<span class="b">银发通</span>账号 🌟</h2>
            <div class="sub">注册后即可享受预约挂号、智能导诊、陪诊服务</div>
          </div>

          <!-- 用户类型选择 -->
          <div class="type-row">
            <div :class="['type-btn', { on: userType === 1 }]" @click="userType = 1">
              <span class="ic">👴</span>
              <span>我是长者</span>
            </div>
            <div :class="['type-btn', { on: userType === 2 }]" @click="userType = 2">
              <span class="ic">👨‍👩‍👧</span>
              <span>我是子女</span>
            </div>
          </div>

          <!-- 表单 -->
          <div class="panel">
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
                <input v-model="password" type="password" placeholder="请设置登录密码（至少6位）" />
              </div>
            </div>

            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-9a2 2 0 0 0-2-2h-2V6a5 5 0 0 0-5-5zM9 6a3 3 0 0 1 6 0v3H9V6z" />
                    <path d="M9 14l2 2 4-4" stroke-width="2" />
                  </svg>
                </span>
                <input v-model="confirmPassword" type="password" placeholder="请再次输入密码" />
              </div>
            </div>

            <div class="field">
              <div class="row">
                <span class="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 21v-1a8 8 0 0 1 16 0v1" />
                  </svg>
                </span>
                <input v-model="nickname" type="text" placeholder="请输入昵称（选填，默认：用户）" />
              </div>
            </div>

            <div class="form-row">
              <label class="check">
                <input v-model="agreed" type="checkbox" />
                <span class="box"></span>
                我已阅读并同意
                <a href="javascript:void(0)">《用户协议》</a>和
                <a href="javascript:void(0)">《隐私政策》</a>
              </label>
            </div>

            <button class="submit" :disabled="loading" @click="handleRegister">
              {{ loading ? '注册中...' : '注 册' }}
            </button>

            <div class="foot">
              已有账号？
              <a href="javascript:void(0)" @click="router.push('/login')">返回登录</a>
            </div>
          </div>
        </div>
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

/* 银杏叶 */
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
  width: 40px;
  height: 40px;
  opacity: 0;
  will-change: transform, opacity;
}

.leaf svg { width: 100%; height: 100%; display: block; }

@keyframes drift {
  0%   { transform: translate3d(0,-80px,0) rotate(0deg); opacity: 0; }
  8%   { opacity: .7; }
  50%  { transform: translate3d(100px,55vh,0) rotate(220deg); opacity: .8; }
  92%  { opacity: .6; }
  100% { transform: translate3d(-40px,110vh,0) rotate(540deg); opacity: 0; }
}

.leaf.l1 { left: 10%; animation: drift 24s linear infinite; animation-delay: 0s; }
.leaf.l2 { left: 30%; animation: drift 28s linear infinite; animation-delay: -6s; }
.leaf.l3 { left: 50%; animation: drift 22s linear infinite; animation-delay: -12s; }
.leaf.l4 { left: 70%; animation: drift 30s linear infinite; animation-delay: -3s; }
.leaf.l5 { left: 85%; animation: drift 26s linear infinite; animation-delay: -15s; }
.leaf.l6 { left: 20%; animation: drift 32s linear infinite; animation-delay: -9s; }

/* 水印 */
.watermark {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  color: rgba(31,77,58,.045);
  line-height: 1;
  user-select: none;
}

.wm1 { top: 8%; left: 5%; font-size: 220px; transform: rotate(-8deg); }
.wm2 { bottom: 6%; right: 5%; font-size: 280px; transform: rotate(6deg); color: rgba(184,69,31,.045); }

/* ============ 主舞台 ============ */
.stage {
  position: relative;
  z-index: 5;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
  padding: 40px 64px;
  min-height: 100vh;
}

@media (max-width: 1100px) {
  .stage {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 24px 24px 40px;
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
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: linear-gradient(160deg, var(--c-primary) 0%, var(--c-primary-d) 100%);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 28px -8px rgba(184,69,31,.5);
  position: relative;
  flex-shrink: 0;
}

.logo-row .badge .yin {
  font-weight: 900;
  font-size: 30px;
  line-height: 1;
}

.logo-row .badge .seal-dot {
  position: absolute;
  right: -4px;
  bottom: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--c-gold);
  color: #FFF7E8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  border: 2px solid var(--c-bg);
}

.logo-row .word {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-row .zh {
  font-weight: 900;
  font-size: 28px;
  letter-spacing: 4px;
  color: var(--c-ink-900);
}

.logo-row .en {
  font-size: 12px;
  color: var(--c-gold);
  letter-spacing: 2px;
}

/* 标语 */
.slogan .line1 {
  font-size: 52px;
  line-height: 1.1;
  color: var(--c-ink-900);
  letter-spacing: 2px;
}

.slogan .line1 .red { color: var(--c-primary); }
.slogan .line1 .green { color: var(--c-accent); }

.slogan .line2 {
  margin-top: 12px;
  font-weight: 500;
  font-size: 22px;
  color: var(--c-ink-700);
  letter-spacing: 4px;
}

/* 特性列表 */
.features {
  margin-top: 36px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.features .feat {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(255,252,245,.7);
  border-radius: 14px;
  border: 1px solid rgba(216,200,168,.4);
  backdrop-filter: blur(6px);
}

.features .feat .icon {
  font-size: 28px;
  flex-shrink: 0;
}

.features .feat .t {
  font-weight: 700;
  font-size: 16px;
  color: var(--c-ink-900);
}

.features .feat .d {
  font-size: 13px;
  color: var(--c-ink-500);
  margin-top: 2px;
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

.auth-head {
  margin-bottom: 24px;
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
  font-size: 30px;
  color: var(--c-ink-900);
  letter-spacing: 1px;
}

.auth-head h2 .b { color: var(--c-primary); }

.auth-head .sub {
  margin-top: 6px;
  font-size: 14px;
  color: var(--c-ink-500);
}

/* 用户类型选择 */
.type-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.type-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: 2px solid var(--c-line);
  border-radius: 14px;
  cursor: pointer;
  font-weight: 700;
  font-size: 15px;
  color: var(--c-ink-500);
  background: #FFFCF5;
  transition: all .2s;
}

.type-btn.on {
  border-color: var(--c-primary);
  color: var(--c-primary);
  background: var(--c-primary-bg);
}

.type-btn .ic { font-size: 20px; }

/* 表单 */
.panel {
  animation: fadeUp .4s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.field {
  margin-bottom: 14px;
}

.field .row {
  display: flex;
  align-items: center;
  gap: 0;
  height: 58px;
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

.field .row .ic svg { width: 100%; height: 100%; }

.field .row .prel {
  padding-right: 12px;
  margin-right: 12px;
  border-right: 1px solid var(--c-line);
  font-weight: 700;
  color: var(--c-ink-700);
  font-size: 16px;
}

.field .row input {
  flex: 1;
  border: 0;
  background: transparent;
  outline: 0;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 16px;
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

.form-row {
  display: flex;
  align-items: center;
  margin: 6px 4px 18px;
  font-size: 13px;
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
  flex-shrink: 0;
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

/* 主按钮 */
.submit {
  width: 100%;
  height: 60px;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-d) 100%);
  color: #FFF7E8;
  font-family: "Noto Sans SC", sans-serif;
  font-size: 18px;
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

.submit:active { transform: translateY(0); }

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

.submit:hover::after { left: 140%; }

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

.foot a:hover { text-decoration: underline; }

@media (max-width: 1100px) {
  .brand-side { display: none; }
  .auth-card { padding: 28px 24px 24px; }
  .auth-head h2 { font-size: 24px; }
  .slogan { display: none; }
}
</style>
