"""用户中心数据访问层"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.user.models import ElderBindModel


async def list_by_child(session: AsyncSession, child_uid: int) -> list[ElderBindModel]:
    result = await session.execute(
        select(ElderBindModel).where(
            ElderBindModel.child_uid == child_uid,
            ElderBindModel.is_deleted == 0,
        )
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, bind_id: int, child_uid: int) -> ElderBindModel | None:
    result = await session.execute(
        select(ElderBindModel).where(
            ElderBindModel.id == bind_id,
            ElderBindModel.child_uid == child_uid,
            ElderBindModel.is_deleted == 0,
        )
    )
    return result.scalar_one_or_none()


async def count_by_child(session: AsyncSession, child_uid: int) -> int:
    result = await session.execute(
        select(func.count(ElderBindModel.id)).where(
            ElderBindModel.child_uid == child_uid,
            ElderBindModel.is_deleted == 0,
        )
    )
    return result.scalar() or 0


async def create(session: AsyncSession, child_uid: int, **kwargs) -> ElderBindModel:
    elder = ElderBindModel(child_uid=child_uid, **kwargs)
    session.add(elder)
    await session.flush()
    await session.refresh(elder)
    return elder


async def update(session: AsyncSession, elder: ElderBindModel, **kwargs) -> ElderBindModel:
    for key, value in kwargs.items():
        setattr(elder, key, value)
    await session.flush()
    await session.refresh(elder)
    return elder


async def get_elder_ids_by_user(session: AsyncSession, child_uid: int) -> list[int]:
    """获取用户绑定的所有长辈 ID 列表"""
    result = await session.execute(
        select(ElderBindModel.id).where(
            ElderBindModel.child_uid == child_uid,
            ElderBindModel.is_deleted == 0,
        )
    )
    return list(result.scalars().all())


async def soft_delete(session: AsyncSession, elder: ElderBindModel):
    elder.is_deleted = 1
    await session.flush()
