"""医生模块数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.doctor.models import DoctorModel
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel


async def list_by_dept(session: AsyncSession, dept_id: int) -> list[DoctorModel]:
    result = await session.execute(
        select(DoctorModel).where(DoctorModel.dept_id == dept_id, DoctorModel.is_deleted == 0)
    )
    return list(result.scalars().all())


async def list_all_with_relations(session: AsyncSession) -> list[dict]:
    """医生 + 科室 + 医院 三级联表"""
    result = await session.execute(
        select(DoctorModel, DepartmentModel.dept_name, HospitalModel.id, HospitalModel.hospital_name)
        .join(DepartmentModel, DoctorModel.dept_id == DepartmentModel.id)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(DoctorModel.is_deleted == 0)
    )
    rows = result.all()
    return [
        {
            "id": d.id, "dept_id": d.dept_id, "dept_name": dn,
            "hospital_id": hid, "hospital_name": hn,
            "doctor_name": d.doctor_name, "doctor_title": d.doctor_title,
            "specialty": d.specialty, "register_fee": d.register_fee,
            "doctor_avatar": d.doctor_avatar,
        }
        for d, dn, hid, hn in rows
    ]


async def get_by_id(session: AsyncSession, doctor_id: int) -> DoctorModel | None:
    result = await session.execute(
        select(DoctorModel).where(DoctorModel.id == doctor_id, DoctorModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, **kwargs) -> DoctorModel:
    doc = DoctorModel(**kwargs)
    session.add(doc)
    await session.flush()
    await session.refresh(doc)
    return doc


async def update(session: AsyncSession, doc: DoctorModel, **kwargs) -> DoctorModel:
    for k, v in kwargs.items():
        if v is not None:
            setattr(doc, k, v)
    await session.flush()
    await session.refresh(doc)
    return doc


async def soft_delete(session: AsyncSession, doc: DoctorModel):
    doc.is_deleted = 1
    await session.flush()
