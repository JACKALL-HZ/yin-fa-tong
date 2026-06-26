---
name: yinfa-tong-redesign
description: 银发通前端视觉重设计实施记录
metadata:
  type: project
---

## 完成范围

将 30 个前端 .vue 文件从基础暖色方案重设计为"现代中式温暖医疗"美学，对齐 `docs/yinfa-tong-all.html` 设计稿（3097 行，6 套页面模板）。

**变更统计：** 新增 2 文件 + 修改 32 文件，所有 `.vue` 文件全部更新。

## 文件清单

### 新增文件
- `frontend/index.html` — Google Fonts 6 字体（Noto Sans/Serif SC + Ma Shan Zheng + Bebas Neue + DM Serif Display + Fraunces）
- `frontend/src/styles/shared.css` — 可复用 class（.card/.card-xl/.card-hover/.sec-head/.sec-head-zh/.sec-head-en/.sec-head-more/.btn-primary/.btn-accent/.btn-gold/.btn-outline/.pill/.pill-primary/.pill-accent/.pill-gold/.pill-rose/.pill-outline/.divider-dash/.divider-line/.page-wrap/.dark-card/.dark-card-accent/.watermark/.seal/.grid-hero/动画）

### 修改文件（32 文件）
- `App.vue` — CSS 变量：16→27 token，删除 `--c-warn`/`--c-warn-l` 合并入 `--c-gold` 系列；body 三层径向渐变；6 字体 utility class；增强 elder-mode
- `AppLayout.vue` — 底部 Tab→顶部导航（stick topbar + green main-nav + 6 菜单）
- `AdminLayout.vue` — header 蓝→墨绿渐变 + Element Plus CSS 变量全覆盖
- **Phase 3/4/5** — 27 个 view 页面全部适配新设计 token + `--c-warn`→`--c-gold` + sec-head/page-wrap/卡片/按钮样式
- 8 个 admin CRUD 页面 — 标题 serif + scoped admin-title class；el-table/dialog 主题由 AdminLayout 变量覆盖

## 设计 Token
- 色板：--c-bg(#F5EBD8) | --c-paper(#FFFCF5) | --c-primary(#B8451F) | --c-accent(#1F4D3A) | --c-gold(#C28840) | --c-cream(#EDD9A8) | --c-rose(#D87056) | --c-sky(#6E8A99) | --c-berry(#7B2D3A)
- 圆角：--r-sm(8px) | --r-md(14px) | --r-lg(22px) | --r-xl(32px) | --r-pill(999px)
- 阴影：三层 --shadow-1/--shadow-2/--shadow-3
- 字体：.serif(Noto Serif SC) | .brush(Ma Shan Zheng) | .display(DM Serif Display italic) | .num(Bebas Neue) | .fraunces(Fraunces italic)

## 关键规则
- `--c-warn`/`--c-warn-l` 已全局删除，替换为 `--c-gold`/`--c-gold-l`/`--c-gold-bg`
- 所有 API/路由/Pinia store/业务逻辑零变更
- 编译：vue-tsc + vite build，`✓ built in 6.37s`

**Why:** 用户提供 yinfa-tong-all.html 设计稿，要求完全重设计前端视觉效果。
**How to apply:** 后续新增页面沿用 shared.css 的 class 体系和新 CSS token，禁止再引入 `--c-warn`。
