"""排班号源数据访问层"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schedule.models import ScheduleModel
from app.doctor.models import DoctorModel
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel


async def list_by_doctor(session: AsyncSession, doctor_id: int, from_date: date | None = None) -> list[ScheduleModel]:
    stmt = select(ScheduleModel).where(
        ScheduleModel.doctor_id == doctor_id,
        ScheduleModel.is_deleted == 0,
    )
    # 默认只查询今天及以后的排班
    if from_date is None:
        from_date = date.today()
    stmt = stmt.where(ScheduleModel.work_date >= from_date)
    result = await session.execute(stmt.order_by(ScheduleModel.work_date))
    return list(result.scalars().all())


async def list_with_relations(session: AsyncSession, doctor_id: int | None = None, from_date: date | None = None) -> list[dict]:
    """排班 + 医生 + 科室 + 医院 四级联表"""
    stmt = (
        select(ScheduleModel, DoctorModel.doctor_name, DoctorModel.register_fee,
               DepartmentModel.dept_name, HospitalModel.hospital_name)
        .join(DoctorModel, ScheduleModel.doctor_id == DoctorModel.id)
        .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(ScheduleModel.is_deleted == 0)
    )
    if doctor_id:
        stmt = stmt.where(ScheduleModel.doctor_id == doctor_id)
    # 默认只查询今天及以后的排班
    if from_date is None:
        from_date = date.today()
    stmt = stmt.where(ScheduleModel.work_date >= from_date)

    result = await session.execute(stmt.order_by(ScheduleModel.work_date))
    rows = result.all()
    return [
        {
            "id": s.id, "doctor_id": s.doctor_id,
            "doctor_name": dn, "register_fee": rf, "dept_name": dpn, "hospital_name": hn,
            "work_date": s.work_date, "time_period": s.time_period,
            "normal_num": s.normal_num, "elder_priority_num": s.elder_priority_num,
        }
        for s, dn, rf, dpn, hn in rows
    ]


async def get_by_id_with_relations(session: AsyncSession, schedule_id: int) -> dict | None:
    """单个排班 + 医生 + 科室 + 医院 四级联表"""
    stmt = (
        select(ScheduleModel, DoctorModel.doctor_name, DoctorModel.register_fee,
               DepartmentModel.dept_name, HospitalModel.hospital_name)
        .join(DoctorModel, ScheduleModel.doctor_id == DoctorModel.id)
        .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(ScheduleModel.id == schedule_id, ScheduleModel.is_deleted == 0)
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        return None
    s, dn, rf, dpn, hn = row
    return {
        "id": s.id, "doctor_id": s.doctor_id,
        "doctor_name": dn, "register_fee": rf, "dept_name": dpn, "hospital_name": hn,
        "work_date": s.work_date, "time_period": s.time_period,
        "normal_num": s.normal_num, "elder_priority_num": s.elder_priority_num,
    }


async def get_by_id(session: AsyncSession, schedule_id: int) -> ScheduleModel | None:
    result = await session.execute(
        select(ScheduleModel).where(ScheduleModel.id == schedule_id, ScheduleModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, **kwargs) -> ScheduleModel:
    sched = ScheduleModel(**kwargs)
    session.add(sched)
    await session.flush()
    await session.refresh(sched)
    return sched


async def update(session: AsyncSession, sched: ScheduleModel, **kwargs) -> ScheduleModel:
    for k, v in kwargs.items():
        if v is not None:
            setattr(sched, k, v)
    await session.flush()
    await session.refresh(sched)
    return sched


async def soft_delete(session: AsyncSession, sched: ScheduleModel):
    sched.is_deleted = 1
    await session.flush()
