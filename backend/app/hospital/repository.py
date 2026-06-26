"""医院模块数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.hospital.models import HospitalModel


async def list_all(session: AsyncSession) -> list[HospitalModel]:
    result = await session.execute(
        select(HospitalModel).where(HospitalModel.is_deleted == 0)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, hospital_id: int) -> HospitalModel | None:
    result = await session.execute(
        select(HospitalModel).where(
            HospitalModel.id == hospital_id,
            HospitalModel.is_deleted == 0,
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, **kwargs) -> HospitalModel:
    hospital = HospitalModel(**kwargs)
    session.add(hospital)
    await session.flush()
    await session.refresh(hospital)
    return hospital


async def update(session: AsyncSession, hospital: HospitalModel, **kwargs) -> HospitalModel:
    for key, value in kwargs.items():
        if value is not None:
            setattr(hospital, key, value)
    await session.flush()
    await session.refresh(hospital)
    return hospital


async def soft_delete(session: AsyncSession, hospital: HospitalModel):
    hospital.is_deleted = 1
    await session.flush()
