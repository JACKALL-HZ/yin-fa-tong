"""健康提醒业务逻辑"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.reminder.schemas import ReminderCreate, ReminderResponse
from app.reminder.models import ReminderModel
from app.shared.rabbitmq import publish_delay

logger = logging.getLogger(__name__)


async def create_reminder(session: AsyncSession, user_id: int, req: ReminderCreate) -> ReminderResponse:
    r = ReminderModel(
        user_id=user_id,
        remind_type=req.remind_type,
        remind_time=req.remind_time,
        remind_content=req.remind_content,
        elder_bind_id=req.elder_bind_id,
        repeat_days=req.repeat_days,
    )
    session.add(r)
    await session.flush()
    await session.refresh(r)

    # 计算延时毫秒（到下一次提醒时间）
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    hour, minute = map(int, req.remind_time.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        from datetime import timedelta
        target += timedelta(days=1)
    delay_ms = int((target - now).total_seconds() * 1000)

    await publish_delay("delay.task", {
        "type": "health_reminder",
        "reminder_id": r.id,
        "user_id": user_id,
        "content": req.remind_content,
    }, delay_ms)

    return ReminderResponse(
        id=r.id, user_id=r.user_id, remind_type=r.remind_type,
        remind_time=r.remind_time, remind_content=r.remind_content,
        elder_bind_id=r.elder_bind_id, repeat_days=r.repeat_days, is_active=r.is_active,
    )


async def list_reminders(session: AsyncSession, user_id: int) -> list[ReminderResponse]:
    result = await session.execute(
        select(ReminderModel).where(
            ReminderModel.user_id == user_id,
            ReminderModel.is_deleted == 0,
        )
    )
    reminders = result.scalars().all()
    return [
        ReminderResponse(
            id=r.id, user_id=r.user_id, remind_type=r.remind_type,
            remind_time=r.remind_time, remind_content=r.remind_content,
            elder_bind_id=r.elder_bind_id, repeat_days=r.repeat_days, is_active=r.is_active,
        )
        for r in reminders
    ]


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
