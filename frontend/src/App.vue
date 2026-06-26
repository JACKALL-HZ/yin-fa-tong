<script setup lang="ts">
import { useAppStore } from '@/stores/app'
const app = useAppStore()
</script>

<template>
  <router-view />
</template>

<style>
/* ========== Design Tokens (适老化) ========== */
/* 对齐设计稿: docs/yinfa-tong-all.html — 现代中式温暖医疗 */
:root {
  /* 底色 */
  --c-bg:       #F5EBD8;
  --c-paper:    #FFFCF5;
  --c-paper-2:  #F9F0DC;
  --c-line:     #D8C8A8;
  --c-line-2:   #C4B190;

  /* 主色 — 深赭红（朱砂印泥） */
  --c-primary:   #B8451F;
  --c-primary-d: #8C2F12;
  --c-primary-l: #F4D9C7;
  --c-primary-bg:#FBEEE5;

  /* 强调色 — 墨绿 */
  --c-accent:    #1F4D3A;
  --c-accent-d:  #0F2E22;
  --c-accent-l:  #D1DDD3;
  --c-accent-bg: #E5EDE6;

  /* 金色 — 焦糖金（装饰/星级/高亮） */
  --c-gold:     #C28840;
  --c-gold-l:   #F2DDB0;
  --c-gold-bg:  #FAEED3;

  /* 次要点缀 */
  --c-cream:    #EDD9A8;
  --c-rose:     #D87056;
  --c-sky:      #6E8A99;
  --c-berry:    #7B2D3A;

  /* 墨色文字 */
  --c-ink-900:  #1A1814;
  --c-ink-700:  #3D3830;
  --c-ink-500:  #6B6358;
  --c-ink-300:  #A89F8E;
  --c-danger:   #C0392B;

  /* 圆角 */
  --r-sm: 8px;
  --r-md: 14px;
  --r-lg: 22px;
  --r-xl: 32px;
  --r-pill: 999px;
  --tap-min: 80px;

  /* 阴影 — 暖色调 */
  --shadow-1: 0 1px 2px rgba(28,24,20,.04), 0 6px 18px rgba(28,24,20,.06);
  --shadow-2: 0 4px 12px rgba(28,24,20,.08), 0 12px 32px rgba(28,24,20,.12);
  --shadow-3: 0 8px 24px rgba(28,24,20,.12);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app {
  height: 100%;
  margin: 0; padding: 0;
  background:
    radial-gradient(1100px 700px at 0% 0%, rgba(194,136,64,.10), transparent 60%),
    radial-gradient(900px 600px at 100% 0%, rgba(184,69,31,.07), transparent 60%),
    radial-gradient(800px 600px at 50% 100%, rgba(31,77,58,.06), transparent 60%),
    var(--c-bg);
  color: var(--c-ink-900);
  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-weight: 500;
  font-size: 17px;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

/* 字体工具类 */
.serif   { font-family: "Noto Serif SC", "Songti SC", serif; }
.brush   { font-family: "Ma Shan Zheng", "Noto Serif SC", serif; }
.display { font-family: "DM Serif Display", "Noto Serif SC", serif; font-style: italic; }
.num     { font-family: "Bebas Neue", "Noto Sans SC", sans-serif; letter-spacing: 1px; }
.fraunces { font-family: "Fraunces", serif; font-style: italic; }

/* 长者模式：全局放大 */
.elder-mode {
  font-size: 24px;
}
.elder-mode h1, .elder-mode h2, .elder-mode h3 { font-size: 120%; }
.elder-mode .el-button { font-size: 22px !important; min-height: var(--tap-min); }
.elder-mode .el-input__inner { font-size: 22px !important; height: 56px; }
.elder-mode .el-card { font-size: 22px; }
.elder-mode input { font-size: 20px; }

/* shared 组件放大 */
.elder-mode .btn-primary,
.elder-mode .btn-accent,
.elder-mode .btn-gold,
.elder-mode .btn-outline { font-size: 20px; padding: 18px 32px; min-height: var(--tap-min); }
.elder-mode .pill { font-size: 16px; padding: 8px 18px; }
.elder-mode .sec-head-zh { font-size: 32px; }
.elder-mode .sec-head-en { font-size: 17px; }
.elder-mode .card { padding: 24px; }
.elder-mode .card-xl { padding: 32px; }

/* 页面组件放大 */
.elder-mode .tab { font-size: 20px; padding: 14px 26px; }
.elder-mode .el-tag { font-size: 14px; }
.elder-mode .el-table { font-size: 18px; }
.elder-mode .el-dialog { font-size: 20px; }
.elder-mode .page-wrap { padding: 40px 40px 100px; }
</style>
