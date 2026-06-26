"""挂号预约数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.reserve.models import ReserveModel


async def get_by_id(session: AsyncSession, reserve_id: int) -> ReserveModel | None:
    result = await session.execute(
        select(ReserveModel).where(ReserveModel.id == reserve_id, ReserveModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def list_by_user(session: AsyncSession, user_id: int, order_status: int | None = None) -> list[ReserveModel]:
    stmt = select(ReserveModel).where(
        ReserveModel.user_id == user_id,
        ReserveModel.is_deleted == 0,
    )
    if order_status is not None:
        stmt = stmt.where(ReserveModel.order_status == order_status)
    result = await session.execute(stmt.order_by(ReserveModel.create_time.desc()))
    return list(result.scalars().all())


async def list_all(session: AsyncSession, order_status: int | None = None) -> list[ReserveModel]:
    stmt = select(ReserveModel).where(ReserveModel.is_deleted == 0)
    if order_status is not None:
        stmt = stmt.where(ReserveModel.order_status == order_status)
    result = await session.execute(stmt.order_by(ReserveModel.create_time.desc()))
    return list(result.scalars().all())


async def create(session: AsyncSession, **kwargs) -> ReserveModel:
    reserve = ReserveModel(**kwargs)
    session.add(reserve)
    await session.flush()
    await session.refresh(reserve)
    return reserve


async def list_by_elder_binds(session: AsyncSession, elder_bind_ids: list[int]) -> list[ReserveModel]:
    """查询指定长辈绑定 ID 列表关联的所有挂号记录"""
    if not elder_bind_ids:
        return []
    stmt = (
        select(ReserveModel)
        .where(
            ReserveModel.elder_bind_id.in_(elder_bind_ids),
            ReserveModel.is_deleted == 0,
        )
        .order_by(ReserveModel.create_time.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_status(
    session: AsyncSession,
    reserve: ReserveModel,
    pay_status: int | None = None,
    order_status: int | None = None,
    queue_status: int | None = None,
    queue_code: str | None = None,
) -> ReserveModel:
    if pay_status is not None:
        reserve.pay_status = pay_status
    if order_status is not None:
        reserve.order_status = order_status
    if queue_status is not None:
        reserve.queue_status = queue_status
    if queue_code is not None:
        reserve.queue_code = queue_code
    await session.flush()
    await session.refresh(reserve)
    return reserve
