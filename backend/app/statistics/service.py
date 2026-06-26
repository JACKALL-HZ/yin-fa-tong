"""数据统计业务逻辑"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.reserve.models import ReserveModel
from app.schedule.models import ScheduleModel
from app.accompany.order.models import AccompanyOrderModel


async def dashboard(session: AsyncSession) -> dict:
    """运营数据看板"""
    # 挂号总量
    total_reserves = await session.scalar(
        select(func.count(ReserveModel.id)).where(ReserveModel.is_deleted == 0)
    ) or 0

    # 今日挂号
    from datetime import date
    today = date.today()
    today_reserves = await session.scalar(
        select(func.count(ReserveModel.id)).where(
            ReserveModel.is_deleted == 0,
            func.date(ReserveModel.create_time) == today,
        )
    ) or 0

    # 号源占比：老年号 vs 普通号
    total_schedules = await session.scalar(
        select(func.sum(ScheduleModel.normal_num + ScheduleModel.elder_priority_num))
        .where(ScheduleModel.is_deleted == 0)
    ) or 0
    elder_sources = await session.scalar(
        select(func.sum(ScheduleModel.elder_priority_num))
        .where(ScheduleModel.is_deleted == 0)
    ) or 0

    # 陪诊订单统计
    accompany_total = await session.scalar(
        select(func.count(AccompanyOrderModel.id)).where(AccompanyOrderModel.is_deleted == 0)
    ) or 0
    accompany_pending = await session.scalar(
        select(func.count(AccompanyOrderModel.id)).where(
            AccompanyOrderModel.is_deleted == 0,
            AccompanyOrderModel.order_status == 1,
        )
    ) or 0

    # 科室热度 TOP10（按挂号数）
    from app.doctor.models import DoctorModel
    from app.department.models import DepartmentModel
    dept_result = await session.execute(
        select(DepartmentModel.dept_name, func.count(ReserveModel.id))
        .select_from(ReserveModel)
        .join(ScheduleModel, ReserveModel.schedule_id == ScheduleModel.id)
        .join(DoctorModel, ScheduleModel.doctor_id == DoctorModel.id)
        .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
        .where(ReserveModel.is_deleted == 0)
        .group_by(DepartmentModel.id)
        .order_by(func.count(ReserveModel.id).desc())
        .limit(10)
    )
    dept_hot = [{"dept_name": dn, "count": c} for dn, c in dept_result.all()]

    return {
        "total_reserves": total_reserves,
        "today_reserves": today_reserves,
        "total_schedules": total_schedules,
        "elder_ratio": round(elder_sources / total_schedules * 100, 1) if total_schedules else 0,
        "accompany_total": accompany_total,
        "accompany_pending": accompany_pending,
        "dept_top10": dept_hot,
    }
