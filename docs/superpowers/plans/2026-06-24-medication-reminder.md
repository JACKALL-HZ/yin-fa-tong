# 用药提醒功能精简实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现「每日固定时间吃药提醒」闭环——用户创建提醒 → 延迟消息触发 → 消费者写入消息中心 + 自动续发下一天

**架构：** 100% 复用已有 `ex_delay` 延迟交换机 + `q_delay_tasks` 队列，消费者通过 `body["type"]="health_reminder"` 分支处理。不新增任何队列或交换机。提醒状态管理仅靠数据库 `is_active` / `is_deleted` 字段，不做消息撤回。

**技术栈：** FastAPI + SQLAlchemy + aio_pika + Vue3 + Element Plus

---

## 文件结构

### 后端（修改 4 个文件，新增 1 个文件）

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/reminder/service.py` | 修改 | 新增 `toggle_active`、`delete_reminder`、`schedule_next` 函数 |
| `backend/app/reminder/router.py` | 修改 | 新增 PATCH（启停）、DELETE（删除）端点 |
| `backend/app/reminder/schemas.py` | 修改 | 新增 `ReminderToggle` schema |
| `backend/app/reminder/mq/consumer.py` | **新增** | 用药提醒消费者：写入 tb_message + 续发下一天 |
| `backend/app/main.py` | 修改 | 注册 reminder 消费者协程 |

### 前端（修改 3 个文件）

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/src/views/reminder/ReminderList.vue` | 修改 | 精简表单（仅用药+HH:MM），增加启停开关+删除按钮 |
| `frontend/src/api/reminder.ts` | 修改 | 新增 `toggle`、`remove` 接口 |
| `frontend/src/types/index.ts` | 修改 | 新增 `Reminder` 类型 |

### 不需要修改的文件

- `backend/app/reminder/models.py` — 模型已完整，字段足够
- `backend/app/shared/rabbitmq.py` — `publish_delay` 已就绪
- `backend/app/message/models.py` — `tb_message` 的 `msg_type=4` 已预留
- `backend/app/message/router.py` — 消息列表/已读/未读数接口已就绪
- `backend/app/alembic/versions/` — `tb_health_reminder` 已在初始迁移中建表，无需新迁移
- `backend/app/reserve/mq/consumer.py` — 不修改挂号消费者，提醒消费者独立文件

---

## 任务 1：后端 — 新增 toggle/delete 端点

**文件：**
- 修改：`backend/app/reminder/schemas.py`
- 修改：`backend/app/reminder/service.py`
- 修改：`backend/app/reminder/router.py`

- [ ] **步骤 1：扩展 schemas.py**

在 `ReminderResponse` 之后新增 `ReminderToggle`：

```python
# backend/app/reminder/schemas.py 末尾追加

class ReminderToggle(BaseModel):
    is_active: int = Field(description="1启用 0停用")
```

- [ ] **步骤 2：扩展 service.py — 新增 toggle_active**

在 `list_reminders` 函数之后追加：

```python
async def toggle_active(session: AsyncSession, user_id: int, reminder_id: int, is_active: int) -> None:
    """启用/停用提醒（消费者根据 is_active 决定是否处理）"""
    result = await session.execute(
        select(ReminderModel).where(
            ReminderModel.id == reminder_id,
            ReminderModel.user_id == user_id,
            ReminderModel.is_deleted == 0,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        from app.exception.base import NotFoundException
        raise NotFoundException("提醒不存在")
    r.is_active = is_active
    await session.flush()
```

- [ ] **步骤 3：扩展 service.py — 新增 delete_reminder**

在 `toggle_active` 函数之后追加：

```python
async def delete_reminder(session: AsyncSession, user_id: int, reminder_id: int) -> None:
    """软删除提醒（消费者遇到 is_deleted=1 直接丢弃）"""
    result = await session.execute(
        select(ReminderModel).where(
            ReminderModel.id == reminder_id,
            ReminderModel.user_id == user_id,
            ReminderModel.is_deleted == 0,
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        from app.exception.base import NotFoundException
        raise NotFoundException("提醒不存在")
    r.is_deleted = 1
    await session.flush()
```

- [ ] **步骤 4：扩展 router.py — 新增 PATCH 和 DELETE 端点**

在 `list_reminders` 端点之后追加：

```python
@router.patch("/{reminder_id}/toggle", response_model=ApiResponse)
async def toggle_reminder(
    reminder_id: int,
    req: ReminderToggle,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """启用/停用提醒"""
    await service.toggle_active(session, current_user.id, reminder_id, req.is_active)
    return ApiResponse.ok(message="已更新" if req.is_active else "已停用")


@router.delete("/{reminder_id}", response_model=ApiResponse)
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除提醒（软删除）"""
    await service.delete_reminder(session, current_user.id, reminder_id)
    return ApiResponse.ok(message="提醒已删除")
```

需要在 router.py 顶部 import 中新增 `ReminderToggle`：

```python
from app.reminder.schemas import ReminderCreate, ReminderResponse, ReminderToggle
```

- [ ] **步骤 5：验证启动无报错**

```bash
docker compose up -d --build backend
docker compose logs backend --tail 10
```

预期：`Application startup complete.`，无 ImportError 或 NameError。

- [ ] **步骤 6：Commit**

```bash
git add backend/app/reminder/schemas.py backend/app/reminder/service.py backend/app/reminder/router.py
git commit -m "feat(reminder): add toggle and delete endpoints"
```

---

## 任务 2：后端 — 用药提醒消费者

**文件：**
- 新增：`backend/app/reminder/mq/consumer.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1：编写消费者 consumer.py**

```python
"""用药提醒消费者 —— 处理延迟队列中的健康提醒消息

监听 q_delay_tasks 队列中 type="health_reminder" 的消息。
校验提醒状态 → 写入 tb_message → 续发下一天延迟消息。
复用 app.shared.rabbitmq 共享连接，不独立建连。
"""

import json
import logging
from datetime import datetime, timedelta, timezone

import aio_pika
from sqlalchemy import select

from app.shared.rabbitmq import get_channel, publish_delay
from app.shared.database import AsyncSessionLocal
from app.reminder.models import ReminderModel
from app.message.models import MessageModel

logger = logging.getLogger(__name__)


async def on_health_reminder(body: dict):
    """处理一条用药提醒消息"""
    reminder_id = body.get("reminder_id")
    if not reminder_id:
        logger.warning("health_reminder 消息缺少 reminder_id: %s", body)
        return

    async with AsyncSessionLocal() as session:
        # 1. 查询提醒记录
        result = await session.execute(
            select(ReminderModel).where(ReminderModel.id == reminder_id)
        )
        r = result.scalar_one_or_none()

        # 2. 状态校验：不存在/已删除/已停用 → 丢弃，不续发
        if not r or r.is_deleted == 1:
            logger.info("提醒已删除，丢弃 reminder_id=%s", reminder_id)
            return
        if r.is_active == 0:
            logger.info("提醒已停用，丢弃 reminder_id=%s", reminder_id)
            return

        # 3. 写入 tb_message（msg_type=4 健康提醒）
        msg = MessageModel(
            user_id=r.user_id,
            msg_type=4,
            msg_content=f"💊 用药提醒：{r.remind_content}",
            read_status=0,
        )
        session.add(msg)
        await session.flush()
        logger.info("已写入消息 reminder_id=%s user_id=%s", reminder_id, r.user_id)

        # 4. 续发下一天延迟消息（每日循环）
        remind_time = r.remind_time  # "HH:MM"
        hour, minute = map(int, remind_time.split(":"))
        now = datetime.now(timezone.utc)
        next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_trigger <= now:
            next_trigger += timedelta(days=1)
        delay_ms = int((next_trigger - now).total_seconds() * 1000)

        await session.commit()

    # 在 session 外发送延迟消息（不依赖事务）
    await publish_delay("delay.task", {
        "type": "health_reminder",
        "reminder_id": reminder_id,
        "user_id": r.user_id,
        "content": r.remind_content,
    }, delay_ms)
    logger.info("已续发下一天提醒 reminder_id=%s delay_ms=%s", reminder_id, delay_ms)
```

- [ ] **步骤 2：将消费者逻辑接入 on_delay_message 分发**

修改 `backend/app/reserve/mq/consumer.py`，在 `on_delay_message` 函数中新增 `health_reminder` 分支：

在 `elif msg_type == "reserve_success":` 块之后追加：

```python
        elif msg_type == "health_reminder":
            from app.reminder.mq.consumer import on_health_reminder
            await on_health_reminder(body)
```

- [ ] **步骤 3：验证启动无报错**

```bash
docker compose up -d --build backend
docker compose logs backend --tail 10
```

预期：`延时消息消费者已启动`，`Application startup complete.`

- [ ] **步骤 4：Commit**

```bash
git add backend/app/reminder/mq/consumer.py backend/app/reserve/mq/consumer.py
git commit -m "feat(reminder): add health_reminder consumer with daily loop"
```

---

## 任务 3：前端 — 精简提醒页面

**文件：**
- 修改：`frontend/src/types/index.ts`
- 修改：`frontend/src/api/reminder.ts`
- 修改：`frontend/src/views/reminder/ReminderList.vue`

- [ ] **步骤 1：新增 Reminder 类型**

在 `frontend/src/types/index.ts` 的 `// ---- 报告 ----` 之前追加：

```typescript
// ---- 提醒 ----
export interface Reminder {
  id: number; user_id: number; remind_type: string; remind_time: string
  remind_content: string; elder_bind_id: number | null; repeat_days: number; is_active: number
}
```

- [ ] **步骤 2：扩展 reminder API**

替换 `frontend/src/api/reminder.ts` 全部内容：

```typescript
import http from './index'
import type { ApiResponse, Reminder } from '@/types'

export const reminderApi = {
  list: () => http.get<ApiResponse<Reminder[]>>('/reminders'),
  create: (data: { remind_type: string; remind_time: string; remind_content: string }) =>
    http.post<ApiResponse<Reminder>>('/reminders', data),
  toggle: (id: number, is_active: number) =>
    http.patch<ApiResponse>(`/reminders/${id}/toggle`, { is_active }),
  remove: (id: number) =>
    http.delete<ApiResponse>(`/reminders/${id}`),
}
```

- [ ] **步骤 3：重写 ReminderList.vue**

替换 `frontend/src/views/reminder/ReminderList.vue` 全部内容：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { reminderApi } from '@/api/reminder'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Reminder } from '@/types'

const list = ref<Reminder[]>([])
const loading = ref(false)
const showAdd = ref(false)
const form = ref({ remind_type: 'medicine', remind_time: '', remind_content: '' })

async function load() {
  loading.value = true
  try {
    const r = await reminderApi.list()
    list.value = r.data.data || []
  } finally {
    loading.value = false
  }
}

async function add() {
  if (!form.value.remind_time || !form.value.remind_content) return ElMessage.warning('请填写药品名和提醒时间')
  await reminderApi.create(form.value)
  ElMessage.success('提醒已创建')
  showAdd.value = false
  form.value = { remind_type: 'medicine', remind_time: '', remind_content: '' }
  load()
}

async function toggleItem(r: Reminder) {
  const newActive = r.is_active === 1 ? 0 : 1
  await reminderApi.toggle(r.id, newActive)
  r.is_active = newActive
  ElMessage.success(newActive ? '已启用' : '已停用')
}

async function deleteItem(r: Reminder) {
  await ElMessageBox.confirm('确定删除该提醒？', '提示', { type: 'warning' })
  await reminderApi.remove(r.id)
  ElMessage.success('已删除')
  load()
}

load()
</script>

<template>
  <div class="page-wrap">
    <div class="sec-head">
      <span class="sec-head-zh">用药提醒</span>
      <span class="sec-head-en">Medication Reminders</span>
      <span class="sec-head-more">
        <el-button type="primary" size="large" @click="showAdd = true">+ 新建提醒</el-button>
      </span>
    </div>

    <div v-loading="loading">
      <div v-if="list.length === 0 && !loading" class="empty">暂无提醒，点击上方按钮创建</div>
      <div v-for="r in list" :key="r.id" class="reminder-card card-hover" :class="{ stopped: r.is_active === 0 }">
        <div class="r-top">
          <span class="pill" :class="r.is_active === 1 ? 'pill-green' : 'pill-grey'">
            {{ r.is_active === 1 ? '✅ 启用中' : '⏸ 已停用' }}
          </span>
          <span class="r-time">⏰ 每日 {{ r.remind_time }}</span>
        </div>
        <div class="r-content">💊 {{ r.remind_content }}</div>
        <div class="r-actions">
          <el-switch :model-value="r.is_active === 1" @change="toggleItem(r)" active-text="启用" inactive-text="停用" />
          <el-button type="danger" text size="small" @click="deleteItem(r)">删除</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showAdd" title="新建用药提醒" width="90%">
      <el-form label-position="top" size="large">
        <el-form-item label="药品名称">
          <el-input v-model="form.remind_content" placeholder="如：阿托伐他汀 1片" />
        </el-form-item>
        <el-form-item label="每日提醒时间">
          <el-time-picker v-model="form.remind_time" format="HH:mm" value-format="HH:mm" placeholder="选择时间" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="large" @click="showAdd = false">取消</el-button>
        <el-button size="large" type="primary" @click="add">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-wrap { max-width: 960px; margin: 0 auto; padding: 32px 32px 80px; }
.empty { text-align: center; padding: 60px 0; color: var(--c-ink-300); font-size: 17px; }
.reminder-card {
  background: var(--c-paper); border-radius: var(--r-md); padding: 18px 20px;
  box-shadow: var(--shadow-1); margin-bottom: 10px;
  border-left: 4px solid var(--c-gold);
}
.reminder-card.stopped { opacity: 0.6; border-left-color: var(--c-ink-300); }
.r-top { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.r-content { font-size: 20px; font-weight: 700; color: var(--c-ink-900); }
.r-time { font-size: 14px; color: var(--c-ink-500); }
.r-actions { display: flex; align-items: center; gap: 12px; margin-top: 10px; }
.pill-green { background: #e8f5e9; color: #2e7d32; padding: 2px 10px; border-radius: 12px; font-size: 13px; }
.pill-grey { background: #eeeeee; color: #757575; padding: 2px 10px; border-radius: 12px; font-size: 13px; }
</style>
```

- [ ] **步骤 4：验证前端编译无报错**

```bash
npm run build --prefix frontend
```

预期：无 TypeScript 编译错误，`Build complete`。

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/types/index.ts frontend/src/api/reminder.ts frontend/src/views/reminder/ReminderList.vue
git commit -m "feat(reminder): simplify medication reminder UI with toggle/delete"
```

---

## 任务 4：端到端验证

- [ ] **步骤 1：重建后端**

```bash
cd "e:\银发通二阶段项目"
docker compose up -d --build backend
docker compose logs backend --tail 15
```

预期：`Application startup complete.`，无错误。

- [ ] **步骤 2：创建用药提醒**

```bash
# 先登录获取 token
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}' | python -m json.tool

# 用返回的 token 创建提醒（替换 <TOKEN>）
curl -s -X POST http://localhost:8000/api/reminders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"remind_type":"medicine","remind_time":"08:00","remind_content":"阿托伐他汀 1片"}' | python -m json.tool
```

预期：返回 `code: 200`，data 中包含 `id`、`remind_time: "08:00"`、`is_active: 1`。

- [ ] **步骤 3：查看提醒列表**

```bash
curl -s http://localhost:8000/api/reminders \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool
```

预期：列表中包含刚创建的提醒。

- [ ] **步骤 4：停用提醒**

```bash
curl -s -X PATCH http://localhost:8000/api/reminders/1/toggle \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"is_active":0}' | python -m json.tool
```

预期：`code: 200`，`message: "已停用"`。

- [ ] **步骤 5：重新启用提醒**

```bash
curl -s -X PATCH http://localhost:8000/api/reminders/1/toggle \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"is_active":1}' | python -m json.tool
```

预期：`code: 200`，`message: "已启用"`。

- [ ] **步骤 6：删除提醒**

```bash
curl -s -X DELETE http://localhost:8000/api/reminders/1 \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool
```

预期：`code: 200`，`message: "提醒已删除"`。

- [ ] **步骤 7：验证消费者日志**

```bash
docker compose logs backend --tail 30 | grep -i "health_reminder\|提醒"
```

预期：如果创建的提醒时间已过（或设一个很近的时间），应看到 `已写入消息` 和 `已续发下一天提醒` 日志。

- [ ] **步骤 8：验证消息中心**

```bash
curl -s "http://localhost:8000/api/messages?msg_type=4" \
  -H "Authorization: Bearer <TOKEN>" | python -m json.tool
```

预期：如果提醒已触发，列表中应有 `msg_type: 4`、`msg_content: "💊 用药提醒：阿托伐他汀 1片"`。

- [ ] **步骤 9：前端页面验证**

打开浏览器访问 `http://localhost:5173`，进入「用药提醒」页面：
- 点击「+ 新建提醒」→ 填写药品名 + 选择时间 → 创建成功
- 列表中显示提醒卡片，有启用/停用开关和删除按钮
- 切换开关 → 卡片样式变化（启用绿色/停用灰色）
- 删除 → 确认弹窗 → 提醒消失

---

## 自检清单

1. **规格覆盖度：**
   - ✅ 用户新增提醒 → 任务 1（service.create_reminder 已有）+ 任务 3（前端表单）
   - ✅ 消费者到期执行 → 任务 2（consumer.py）
   - ✅ 写入 tb_message → 任务 2（on_health_reminder）
   - ✅ 自动续发下一天 → 任务 2（schedule_next 逻辑）
   - ✅ 停用则丢弃不续发 → 任务 2（is_active 检查）
   - ✅ 取消/修改靠数据库状态 → 任务 1（toggle/delete 端点）
   - ✅ 复用 delay_exchange → 任务 2（publish_delay + on_delay_message 分支）
   - ✅ 不新增基础设施 → 全文无新队列/交换机声明

2. **占位符扫描：** 无 TODO、待定、后续实现。

3. **类型一致性：** `Reminder` 类型在 types/index.ts 定义，api/reminder.ts 和 ReminderList.vue 均引用同一类型。
