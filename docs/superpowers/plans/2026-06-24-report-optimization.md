# 体检报告功能优化完善

> 生成时间: 2026-06-24

## TL;DR

> **快速摘要**: 体检报告模块存在详情页缺失、授权绕过、OCR 为模拟实现、解释覆盖不全等问题。本次优化聚焦修复可用性缺陷和安全问题，不涉及真实 OCR 引擎接入。
>
> **交付物**:
> - 可正常访问的报告详情页（`/reports/:id`）
> - 修复后的上传授权校验
> - 新增删除报告功能（后端 + 前端）
> - 扩展指标解释覆盖范围
> - 修复前端类型安全和错误处理
>
> **预估工作量**: 中型
> **并行执行**: YES - 4 个 waves
> **关键路径**: Task 1 → Task 3 → Task 6

---

## Context

### 原始需求
体检报告功能优化完善

### 探索发现的核心问题

| 优先级 | 问题 | 影响 |
|--------|------|------|
| **P0** | 前端详情页不存在（`/reports/:id` 路由未注册，无 `ReportDetail.vue`） | 用户点击"查看详情"跳转空白/404 |
| **P0** | OCR 引擎是纯模拟实现（仅支持 `simulated_text`） | 上传真实体检单无法解析 |
| **P1** | `upload_report` 未校验 `elder_bind_id` 是否属于当前用户 | 任意用户可往任意老人名下上传报告 |
| **P2** | 无删除功能、无重新解释、interpreter 缺少肌酐/血常规指标 | 功能不完整 |
| **P2** | 详情接口返回 `dict` 非 Pydantic schema | 类型不安全，文档无法生成 |
| **P2** | 前端 catch 块未检查 `isSuccess`、类型标注为 `any` | 错误处理不可靠 |
| **P3** | `_to_item` 存在 N+1 查询、`dead code` 未清理 | 性能隐患 |

### 现有实现状态
- **后端基础结构完整**: 5 个文件（router / service / schemas / interpreter / repository）已实现基本 CRUD
- **前端基础结构完整**: 3 个文件（api / views / types）已实现列表和上传
- **Alembic 迁移已就绪**: `report_type` 字段迁移已创建（`b2c3d4e5f6a7`）
- **interpreter 已覆盖**: 血糖、血压、血脂、尿酸、总胆固醇 5 类指标
- **详情 API 已存在**: `get_report_detail()` 返回原始值 + 解释，但返回类型是 `dict`

---

## Work Objectives

### 核心目标
修复体检报告模块的可用性缺陷，使详情查看、删除、指标解释等核心功能正常运作。

### 具体目标
- 用户点击"查看详情"能正常跳转并展示报告详情
- 上传报告时验证 `elder_bind_id` 归属关系，防止越权
- 支持删除已上传的报告
- interpreter 扩展覆盖肌酐和血常规指标
- 前端类型安全和错误处理规范化

### Must Have
- [ ] 报告详情页可正常访问
- [ ] 上传接口授权校验
- [ ] 删除报告功能
- [ ] interpreter 扩展肌酐 + 血常规

### Must NOT Have（边界）
- 不接入真实 OCR 引擎（工程量大，需独立方案）
- 不新增 PDF 解析支持
- 不新增"重新解释"按钮（interpreter 逻辑未变，重新解释无意义）
- 不修改 `report_type` 字段的现有逻辑

---

## Verification Strategy（零人工验收）

> **核心原则**: 每个任务必须包含可自动化执行的验证命令。不接受"目视检查"。

- **后端验证**: `docker compose exec backend python -m pytest backend/app/tests/ -x`
- **前端验证**: `cd frontend && npx vue-tsc --noEmit && npx vite build`
- **编译验证**: 每个任务完成后必须运行对应层级的编译/类型检查

---

## Execution Strategy

### 并行执行 Waves

```
Wave 1（安全 + 基础）: Task 1, Task 2, Task 5（后端 schema + 授权 + interpreter 扩展）
    ↓
Wave 2（前端详情页）: Task 3（依赖 Task 1 的后端 schema）
    ↓
Wave 3（前端修复）: Task 4, Task 6（删除功能 + 错误处理修复）
    ↓
Wave 4（验证）: Task 7（全量编译验证）
```

### Dependency Matrix

| Task | 依赖 | 被依赖 |
|------|------|--------|
| 1 | — | 3 |
| 2 | — | — |
| 3 | 1 | — |
| 4 | — | — |
| 5 | — | — |
| 6 | — | 7 |
| 7 | 全部 | — |

### Agent Dispatch Summary

- **Wave 1**: 3 agents → T1（interpreter 扩展）, T2（授权修复）, T5（schema 规范化）
- **Wave 2**: 1 agent → T3（前端详情页）
- **Wave 3**: 2 agents → T4（删除功能）, T6（前端错误处理）
- **Wave 4**: 1 agent → T7（编译验证）

---

## TODOs

---

## Final Verification Wave（独立验证）

- [ ] F1. **后端 pytest** — `docker compose exec backend python -m pytest backend/app/tests/ -x` — 全部通过
- [ ] F2. **前端编译** — `cd frontend && npx vue-tsc --noEmit && npx vite build` — 零错误
- [ ] F3. **Docker 构建** — `docker compose build` — 成功

---

## Commit Strategy

- Task 1-2: `fix(backend): report authorization and schema规范化`
- Task 3-6: `feat(frontend): report detail page and error handling`
- Task 5: `feat(backend): expand report interpreter indicators`

---

## Success Criteria

### 验证命令

```bash
# 后端测试
docker compose exec backend python -m pytest backend/app/tests/ -x

# 前端类型检查 + 构建
cd frontend && npx vue-tsc --noEmit && npx vite build

# Docker 构建
docker compose build
```

### 最终检查清单

- [ ] 点击"查看详情"正常跳转到 `/reports/:id` 并展示数据
- [ ] 上传报告时 `elder_bind_id` 不属于当前用户返回 403
- [ ] 点击"删除"后报告从列表消失，数据库记录已删除
- [ ] 血肌酐、白细胞、血红蛋白、血小板能返回解释
- [ ] 前端 `vue-tsc --noEmit` 零错误
