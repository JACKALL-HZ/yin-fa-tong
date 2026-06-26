"""陪诊订单数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.accompany.order.models import AccompanyOrderModel


async def get_by_id(session: AsyncSession, order_id: int) -> AccompanyOrderModel | None:
    result = await session.execute(
        select(AccompanyOrderModel).where(AccompanyOrderModel.id == order_id, AccompanyOrderModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def list_by_user(session: AsyncSession, user_id: int, order_status: int | None = None) -> list[AccompanyOrderModel]:
    stmt = select(AccompanyOrderModel).where(
        AccompanyOrderModel.user_id == user_id,
        AccompanyOrderModel.is_deleted == 0,
    )
    if order_status is not None:
        stmt = stmt.where(AccompanyOrderModel.order_status == order_status)
    result = await session.execute(stmt.order_by(AccompanyOrderModel.create_time.desc()))
    return list(result.scalars().all())


async def list_all(session: AsyncSession, order_status: int | None = None) -> list[AccompanyOrderModel]:
    stmt = select(AccompanyOrderModel).where(AccompanyOrderModel.is_deleted == 0)
    if order_status is not None:
        stmt = stmt.where(AccompanyOrderModel.order_status == order_status)
    result = await session.execute(stmt.order_by(AccompanyOrderModel.create_time.desc()))
    return list(result.scalars().all())


async def create(session: AsyncSession, **kwargs) -> AccompanyOrderModel:
    order = AccompanyOrderModel(**kwargs)
    session.add(order)
    await session.flush()
    await session.refresh(order)
    return order


async def update_status(session: AsyncSession, order: AccompanyOrderModel, order_status: int) -> AccompanyOrderModel:
    order.order_status = order_status
    await session.flush()
    await session.refresh(order)
    return order


async def submit_review(session: AsyncSession, order: AccompanyOrderModel, score: int, comment: str | None) -> AccompanyOrderModel:
    order.service_score = score
    order.service_comment = comment
    order.order_status = 4  # 已完成
    await session.flush()
    await session.refresh(order)
    return order
