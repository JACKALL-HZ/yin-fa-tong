"""志愿者数据访问层"""

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.accompany.volunteer.models import VolunteerModel


async def list_available(session: AsyncSession) -> list[VolunteerModel]:
    result = await session.execute(
        select(VolunteerModel).where(
            VolunteerModel.status == 1,
            VolunteerModel.is_deleted == 0,
        ).order_by(VolunteerModel.service_score.desc())
    )
    return list(result.scalars().all())


async def list_all(session: AsyncSession) -> list[VolunteerModel]:
    result = await session.execute(
        select(VolunteerModel).where(VolunteerModel.is_deleted == 0)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, vol_id: int) -> VolunteerModel | None:
    result = await session.execute(
        select(VolunteerModel).where(VolunteerModel.id == vol_id, VolunteerModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, **kwargs) -> VolunteerModel:
    vol = VolunteerModel(**kwargs)
    session.add(vol)
    await session.flush()
    await session.refresh(vol)
    return vol


async def update(session: AsyncSession, vol: VolunteerModel, **kwargs) -> VolunteerModel:
    for k, v in kwargs.items():
        if v is not None:
            setattr(vol, k, v)
    await session.flush()
    await session.refresh(vol)
    return vol


async def update_score(session: AsyncSession, vol: VolunteerModel, new_score: int):
    """更新志愿者评分（加权平均，保留 Decimal 精度）"""
    old_total = vol.service_score * vol.service_count
    vol.service_count += 1
    vol.service_score = (old_total + new_score) / Decimal(vol.service_count)
    await session.flush()
