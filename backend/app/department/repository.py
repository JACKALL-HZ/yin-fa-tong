"""科室模块数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.department.models import DepartmentModel
from app.hospital.models import HospitalModel


async def list_by_hospital(session: AsyncSession, hospital_id: int) -> list[DepartmentModel]:
    result = await session.execute(
        select(DepartmentModel).where(
            DepartmentModel.hospital_id == hospital_id,
            DepartmentModel.is_deleted == 0,
        )
    )
    return list(result.scalars().all())


async def list_all_with_hospital(session: AsyncSession) -> list[dict]:
    """科室 + 医院名称联表"""
    result = await session.execute(
        select(DepartmentModel, HospitalModel.hospital_name)
        .join(HospitalModel, DepartmentModel.hospital_id == HospitalModel.id)
        .where(DepartmentModel.is_deleted == 0)
    )
    rows = result.all()
    return [{"id": d.id, "hospital_id": d.hospital_id, "hospital_name": hn, "dept_name": d.dept_name} for d, hn in rows]


async def get_by_id(session: AsyncSession, dept_id: int) -> DepartmentModel | None:
    result = await session.execute(
        select(DepartmentModel).where(DepartmentModel.id == dept_id, DepartmentModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, **kwargs) -> DepartmentModel:
    dept = DepartmentModel(**kwargs)
    session.add(dept)
    await session.flush()
    await session.refresh(dept)
    return dept


async def update(session: AsyncSession, dept: DepartmentModel, **kwargs) -> DepartmentModel:
    for k, v in kwargs.items():
        if v is not None:
            setattr(dept, k, v)
    await session.flush()
    await session.refresh(dept)
    return dept


async def soft_delete(session: AsyncSession, dept: DepartmentModel):
    dept.is_deleted = 1
    await session.flush()
