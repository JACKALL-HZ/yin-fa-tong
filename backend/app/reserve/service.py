"""挂号预约业务逻辑层"""

import logging
from datetime import date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.reserve.schemas import ReserveCreateRequest, ReserveResponse
from app.reserve import repository as repo
from app.reserve.mq import producer as mq_producer
from app.reserve.models import ReserveModel
from app.schedule.repository import get_by_id as get_schedule
from app.doctor.models import DoctorModel
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel
from app.user.models import ElderBindModel
from app.shared.redis import decrease_source_redis, rollback_source_redis, get_redis
from app.queue.service import enqueue as queue_enqueue
from app.exception.base import BadRequestException, NotFoundException, ConflictException

logger = logging.getLogger(__name__)


def _generate_queue_code(reserve_id: int) -> str:
    """生成候诊编号: NK + 日期 + 4位流水"""
    today = date.today().strftime("%Y%m%d")
    return f"NK{today}{reserve_id:04d}"


async def _build_response(session: AsyncSession, reserve: ReserveModel) -> ReserveResponse:
    """组装 ReservationResponse 并拉取关联信息"""
    sched = await get_schedule(session, reserve.schedule_id)
    work_date = sched.work_date if sched else None

    # 自动过期：排班日期已过且仍为"已预约"→ 更新为"已就诊"
    if reserve.order_status == 2 and work_date and work_date < date.today():
        reserve = await repo.update_status(session, reserve, order_status=3, queue_status=3)
    time_period = sched.time_period if sched else None
    _tp_map = {"AM": "上午", "PM": "下午", "ALL": "全天"}
    time_period_text = _tp_map.get(time_period, time_period) if time_period else None

    doctor = None
    dept = None
    hospital = None
    if sched:
        doctor_result = await session.execute(select(DoctorModel).where(DoctorModel.id == sched.doctor_id))
        doctor = doctor_result.scalar_one_or_none()
    if doctor:
        dept_result = await session.execute(select(DepartmentModel).where(DepartmentModel.id == doctor.dept_id))
        dept = dept_result.scalar_one_or_none()
    if dept:
        hosp_result = await session.execute(select(HospitalModel).where(HospitalModel.id == dept.hospital_id))
        hospital = hosp_result.scalar_one_or_none()

    elder_name = None
    if reserve.elder_bind_id:
        elder_result = await session.execute(select(ElderBindModel).where(ElderBindModel.id == reserve.elder_bind_id))
        elder = elder_result.scalar_one_or_none()
        if elder:
            elder_name = elder.elder_name

    # 支付截止时间：预约创建后 15 分钟（待支付状态下才有意义）
    # create_time 是 UTC naive，转为 UTC+8 再加 15 分钟，确保前端解析正确
    pay_deadline = None
    if reserve.pay_status == 1 and reserve.create_time:
        utc8 = timezone(timedelta(hours=8))
        create_local = reserve.create_time.replace(tzinfo=timezone.utc).astimezone(utc8)
        pay_deadline = create_local + timedelta(minutes=15)

    return ReserveResponse(
        id=reserve.id,
        user_id=reserve.user_id,
        schedule_id=reserve.schedule_id,
        elder_bind_id=reserve.elder_bind_id,
        queue_code=reserve.queue_code,
        queue_status=reserve.queue_status,
        pay_status=reserve.pay_status,
        order_status=reserve.order_status,
        hospital_name=hospital.hospital_name if hospital else None,
        dept_name=dept.dept_name if dept else None,
        doctor_name=doctor.doctor_name if doctor else None,
        work_date=work_date,
        time_period=time_period,
        time_period_text=time_period_text,
        register_fee=doctor.register_fee if doctor else None,
        elder_name=elder_name,
        pay_deadline=pay_deadline,
    )


async def create_reserve(session: AsyncSession, user_id: int, req: ReserveCreateRequest) -> ReserveResponse:
    """挂号预约下单"""
    # 1. 校验排班是否存在
    sched = await get_schedule(session, req.schedule_id)
    if not sched:
        raise NotFoundException("该排班不存在")

    # 1.5 预约去重：同一用户同一排班不可重复预约
    r = await get_redis()
    dedup_key = f"reserve_dedup:{req.schedule_id}:{user_id}"
    first_attempt = await r.set(dedup_key, 1, nx=True, ex=900)  # 15min = 支付超时
    if not first_attempt:
        raise ConflictException("您已预约该时段，请勿重复操作")

    # 2. Redis Lua 原子扣减号源
    success = await decrease_source_redis(req.schedule_id, req.source_type)
    if not success:
        raise ConflictException("号源不足，已被抢光")

    # 3. 创建待支付订单
    try:
        reserve = await repo.create(
            session,
            user_id=user_id,
            schedule_id=req.schedule_id,
            elder_bind_id=req.elder_bind_id,
            source_type=req.source_type,
            pay_status=1,       # 待支付
            order_status=1,     # 待支付
            queue_status=1,     # 等待中
        )
        # 生成候诊编号
        queue_code = _generate_queue_code(reserve.id)
        reserve = await repo.update_status(session, reserve, queue_code=queue_code)

        # 4. 注册到 Redis 排队队列
        await queue_enqueue(reserve.id, req.schedule_id, queue_code)

        # 5. 发送延时取消消息（15分钟）+ 挂号成功通知
        #    RabbitMQ 不可用时 graceful 降级，不阻断预约创建
        try:
            await mq_producer.send_payment_timeout(reserve.id, req.schedule_id, req.source_type)
            await mq_producer.send_reserve_success(user_id, reserve.id, queue_code)
        except Exception as mq_err:
            logger.warning("RabbitMQ 消息发送失败（预约已创建，超时由定时任务兜底）: %s", mq_err)

        return await _build_response(session, reserve)

    except Exception:
        # 业务异常时回滚 Redis 号源 + 清除去重标记
        await rollback_source_redis(req.schedule_id, req.source_type)
        await r.delete(dedup_key)
        raise


async def pay_reserve(session: AsyncSession, reserve_id: int, user_id: int) -> ReserveResponse:
    """支付订单：待支付 → 已预约"""
    reserve = await repo.get_by_id(session, reserve_id)
    if not reserve or reserve.user_id != user_id:
        raise NotFoundException("订单不存在")
    if reserve.pay_status != 1:
        raise BadRequestException("订单状态不允许支付")

    reserve = await repo.update_status(session, reserve, pay_status=2, order_status=2, queue_status=1)
    return await _build_response(session, reserve)


async def cancel_reserve(session: AsyncSession, reserve_id: int, user_id: int):
    """用户主动取消订单 + 回滚号源"""
    reserve = await repo.get_by_id(session, reserve_id)
    if not reserve or reserve.user_id != user_id:
        raise NotFoundException("订单不存在")
    if reserve.order_status == 4:
        raise BadRequestException("订单已取消")

    # 就诊当天不可在线取消
    schedule = await get_schedule(session, reserve.schedule_id)
    if schedule and schedule.work_date <= date.today():
        raise BadRequestException("就诊当天不可在线取消，请到窗口办理")

    # 回滚 Redis 号源
    await rollback_source_redis(reserve.schedule_id, reserve.source_type)

    # 清除预约去重标记
    r = await get_redis()
    await r.delete(f"reserve_dedup:{reserve.schedule_id}:{user_id}")

    await repo.update_status(session, reserve, pay_status=3, order_status=4)


async def list_my_reserves(session: AsyncSession, user_id: int, order_status: int | None = None) -> list[ReserveResponse]:
    """我的预约列表"""
    reserves = await repo.list_by_user(session, user_id, order_status)
    responses = []
    for r in reserves:
        responses.append(await _build_response(session, r))
    return responses


async def get_reserve_detail(session: AsyncSession, reserve_id: int, user_id: int) -> ReserveResponse:
    """预约详情"""
    reserve = await repo.get_by_id(session, reserve_id)
    if not reserve or reserve.user_id != user_id:
        raise NotFoundException("订单不存在")
    return await _build_response(session, reserve)
