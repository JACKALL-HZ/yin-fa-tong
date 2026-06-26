"""定时任务调度器 —— 基于 APScheduler

任务列表：
1. 每天凌晨 2:00 — 批量更新过期订单为"已就诊"
2. 每小时整点 — Redis-MySQL 号源对账
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def expire_reservations():
    """每天凌晨 2:00：批量更新过期订单为已就诊

    扫描 order_status=2（已预约）且排班日期已过的订单，
    批量更新为 order_status=3（已就诊）、queue_status=3（已完成）。
    """
    from sqlalchemy import and_
    from app.shared.database import AsyncSessionLocal
    from app.reserve.models import ReserveModel
    from app.schedule.models import ScheduleModel
    from datetime import date

    async with AsyncSessionLocal() as session:
        # 使用子查询关联排班表检查 work_date
        from sqlalchemy import select, update as sa_update

        # 先查出过期的 reserve IDs
        subq = (
            select(ScheduleModel.id)
            .where(ScheduleModel.work_date < date.today())
        )
        result = await session.execute(
            sa_update(ReserveModel)
            .where(and_(
                ReserveModel.order_status == 2,
                ReserveModel.schedule_id.in_(subq),
                ReserveModel.is_deleted == 0,
            ))
            .values(order_status=3, queue_status=3)
        )
        await session.commit()
        if result.rowcount > 0:
            logger.info("定时过期：已更新 %d 条过期订单为已就诊", result.rowcount)
        else:
            logger.debug("定时过期：无过期订单需要更新")


async def reconcile_sources():
    """每小时：Redis-MySQL 号源对账

    对比 MySQL 中每个排班的有效预约数与 Redis 剩余量，
    不一致时以 MySQL 为准修复 Redis。
    """
    from sqlalchemy import select, func
    from app.shared.database import AsyncSessionLocal
    from app.schedule.models import ScheduleModel
    from app.reserve.models import ReserveModel
    from app.shared.redis import get_redis
    from datetime import date

    async with AsyncSessionLocal() as session:
        # 查询今天及未来的排班
        schedules_result = await session.execute(
            select(ScheduleModel).where(
                ScheduleModel.work_date >= date.today(),
                ScheduleModel.is_deleted == 0,
            )
        )
        schedules = schedules_result.scalars().all()
        if not schedules:
            return

        r = await get_redis()
        fixed_count = 0

        for s in schedules:
            # 按 source_type 分组统计有效预约数（未取消：order_status in (1, 2)）
            from sqlalchemy import case
            cnt_result = await session.execute(
                select(
                    func.count(case((ReserveModel.source_type == "normal", 1))),
                    func.count(case((ReserveModel.source_type == "elder", 1))),
                ).where(
                    ReserveModel.schedule_id == s.id,
                    ReserveModel.order_status.in_([1, 2]),
                    ReserveModel.is_deleted == 0,
                )
            )
            normal_reserved, elder_reserved = cnt_result.one()

            # 以 MySQL 总量 - 对应类型预约数 = 正确剩余量
            expected_normal = max(0, s.normal_num - normal_reserved)
            expected_elder = max(0, s.elder_priority_num - elder_reserved)

            # 对比 Redis 实际值
            redis_normal = int(await r.get(f"source:{s.id}:normal") or 0)
            redis_elder = int(await r.get(f"source:{s.id}:elder") or 0)

            if redis_normal != expected_normal or redis_elder != expected_elder:
                await r.set(f"source:{s.id}:normal", expected_normal)
                await r.set(f"source:{s.id}:elder", expected_elder)
                fixed_count += 1
                logger.warning(
                    "对账修复 schedule_id=%s normal:%d->%d elder:%d->%d (reserved=%d)",
                    s.id, redis_normal, expected_normal, redis_elder, expected_elder, reserved,
                )

        if fixed_count > 0:
            logger.warning("号源对账完成，修复了 %d 个排班", fixed_count)
        else:
            logger.debug("号源对账完成，数据一致")


def start_scheduler():
    """启动定时任务调度器"""
    scheduler.add_job(expire_reservations, CronTrigger(hour=2, minute=0), id="expire_reservations")
    scheduler.add_job(reconcile_sources, CronTrigger(minute=0), id="reconcile_sources")
    scheduler.start()
    logger.info("定时任务调度器已启动（过期订单 02:00 / 号源对账 每小时）")
