"""支付记录数据库操作"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.payment.models import PayRecordModel


async def create_record(
    session: AsyncSession,
    reserve_id: int,
    pay_money: float,
    out_trade_no: str,
    pay_channel: str = "mock",
) -> PayRecordModel:
    """创建支付记录"""
    record = PayRecordModel(
        reserve_id=reserve_id,
        pay_money=pay_money,
        out_trade_no=out_trade_no,
        pay_channel=pay_channel,
        pay_status=1,
    )
    session.add(record)
    await session.flush()
    return record


async def get_by_out_trade_no(session: AsyncSession, out_trade_no: str) -> PayRecordModel | None:
    """根据商户订单号查询支付记录"""
    stmt = select(PayRecordModel).where(
        PayRecordModel.out_trade_no == out_trade_no,
        PayRecordModel.is_deleted == 0,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_paid(session: AsyncSession, out_trade_no: str, trade_no: str) -> int:
    """标记支付记录为已支付（仅待支付状态可更新，返回影响行数）"""
    stmt = (
        update(PayRecordModel)
        .where(PayRecordModel.out_trade_no == out_trade_no, PayRecordModel.pay_status == 1)
        .values(pay_status=2, trade_no=trade_no)
    )
    result = await session.execute(stmt)
    return result.rowcount


async def mark_closed(session: AsyncSession, out_trade_no: str) -> int:
    """标记支付记录为已关闭（仅待支付状态可更新，返回影响行数）"""
    stmt = (
        update(PayRecordModel)
        .where(PayRecordModel.out_trade_no == out_trade_no, PayRecordModel.pay_status == 1)
        .values(pay_status=3)
    )
    result = await session.execute(stmt)
    return result.rowcount


async def get_by_reserve_id(session: AsyncSession, reserve_id: int) -> PayRecordModel | None:
    """根据预约订单 ID 查询支付记录"""
    stmt = select(PayRecordModel).where(
        PayRecordModel.reserve_id == reserve_id,
        PayRecordModel.is_deleted == 0,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
