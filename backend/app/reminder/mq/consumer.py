"""用药提醒消费者 —— 处理延迟队列中的健康提醒消息

监听 q_delay_tasks 队列中 type="health_reminder" 的消息。
校验提醒状态 → 写入 tb_message → 续发下一天延迟消息。
复用 app.shared.rabbitmq 共享连接，不独立建连。
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.shared.rabbitmq import publish_delay
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

        # 提前取出属性（session 关闭后仍需使用）
        user_id = r.user_id
        remind_content = r.remind_content
        remind_time = r.remind_time

        # 3. 写入 tb_message（msg_type=4 健康提醒）
        msg = MessageModel(
            user_id=user_id,
            msg_type=4,
            msg_content=f"\U0001f48a 用药提醒：{remind_content}",
            read_status=0,
        )
        session.add(msg)
        await session.flush()
        logger.info("已写入消息 reminder_id=%s user_id=%s", reminder_id, user_id)

        # 4. 续发下一天延迟消息（每日循环）
        try:
            hour, minute = map(int, remind_time.split(":"))
        except ValueError:
            logger.error("remind_time 格式异常 reminder_id=%s time=%s", reminder_id, remind_time)
            await session.commit()
            return

        now = datetime.now(timezone.utc)
        next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_trigger <= now:
            next_trigger += timedelta(days=1)
        delay_ms = int((next_trigger - now).total_seconds() * 1000)

        await session.commit()

    # 在 session 外发送延迟消息（不依赖事务）
    try:
        await publish_delay("delay.task", {
            "type": "health_reminder",
            "reminder_id": reminder_id,
            "user_id": user_id,
            "content": remind_content,
        }, delay_ms)
        logger.info("已续发下一天提醒 reminder_id=%s delay_ms=%s", reminder_id, delay_ms)
    except Exception:
        logger.exception("续发延迟消息失败，提醒链可能中断 reminder_id=%s", reminder_id)
