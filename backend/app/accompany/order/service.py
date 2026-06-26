"""陪诊订单业务逻辑层"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.accompany.order.schemas import (
    AccompanyOrderCreate, ReviewCreate, AccompanyOrderResponse, STATUS_MAP,
)
from app.accompany.order.models import AccompanyOrderModel
from app.accompany.order import repository as repo
from app.accompany.volunteer.repository import get_by_id as get_volunteer, update_score
from app.user.models import ElderBindModel
from app.shared.rabbitmq import publish_direct
from app.exception.base import NotFoundException, BadRequestException

logger = logging.getLogger(__name__)


async def _to_response(session: AsyncSession, order: AccompanyOrderModel) -> AccompanyOrderResponse:
    # 自动过期：服务日期已过 → 待审核/待服务自动取消，服务中自动完成
    if order.accompany_date:
        from datetime import date
        if order.order_status in (1, 2) and order.accompany_date < date.today():
            order = await repo.update_status(session, order, 5)
        elif order.order_status == 3 and order.accompany_date < date.today():
            order = await repo.update_status(session, order, 4)

    elder_name = None
    vol_name = None
    if order.elder_bind_id:
        elder_result = await session.execute(select(ElderBindModel).where(ElderBindModel.id == order.elder_bind_id))
        elder = elder_result.scalar_one_or_none()
        if elder:
            elder_name = elder.elder_name
    if order.volunteer_id:
        vol = await get_volunteer(session, order.volunteer_id)
        if vol:
            vol_name = vol.vol_name

    return AccompanyOrderResponse(
        id=order.id, user_id=order.user_id, elder_bind_id=order.elder_bind_id,
        elder_name=elder_name, volunteer_id=order.volunteer_id, vol_name=vol_name,
        accompany_date=order.accompany_date, order_status=order.order_status,
        status_text=STATUS_MAP.get(order.order_status, "未知"),
        service_score=order.service_score, service_comment=order.service_comment,
    )


async def create_order(session: AsyncSession, user_id: int, req: AccompanyOrderCreate) -> AccompanyOrderResponse:
    # 校验志愿者存在且可预约
    vol = await get_volunteer(session, req.volunteer_id)
    if not vol or vol.status != 1:
        raise BadRequestException("该志愿者暂不可预约")

    order = await repo.create(
        session,
        user_id=user_id,
        elder_bind_id=req.elder_bind_id,
        volunteer_id=req.volunteer_id,
        accompany_date=req.accompany_date,
        order_status=1,  # 待审核
    )

    # 推送管理员审核通知
    try:
        await publish_direct("ex_accompany", "accompany.submit", {
            "type": "accompany_submit",
            "order_id": order.id,
        })
    except Exception:
        logger.warning("MQ 推送陪诊申请通知失败，订单已创建，不影响核心流程", exc_info=True)

    return await _to_response(session, order)


async def approve_order(session: AsyncSession, order_id: int) -> AccompanyOrderResponse:
    """管理员审核通过：待审核 → 待服务"""
    order = await repo.get_by_id(session, order_id)
    if not order:
        raise NotFoundException("订单不存在")
    if order.order_status != 1:
        raise BadRequestException("当前状态不允许审核")
    order = await repo.update_status(session, order, 2)
    return await _to_response(session, order)


async def reject_order(session: AsyncSession, order_id: int):
    order = await repo.get_by_id(session, order_id)
    if not order:
        raise NotFoundException("订单不存在")
    await repo.update_status(session, order, 5)


async def start_service(session: AsyncSession, order_id: int) -> AccompanyOrderResponse:
    order = await repo.get_by_id(session, order_id)
    if not order:
        raise NotFoundException("订单不存在")
    if order.order_status != 2:
        raise BadRequestException("当前状态不允许开始服务")
    order = await repo.update_status(session, order, 3)
    return await _to_response(session, order)


async def complete_service(session: AsyncSession, order_id: int) -> AccompanyOrderResponse:
    """管理员完成服务：服务中 → 已完成"""
    order = await repo.get_by_id(session, order_id)
    if not order:
        raise NotFoundException("订单不存在")
    if order.order_status != 3:
        raise BadRequestException("仅服务中的订单可完成")
    order = await repo.update_status(session, order, 4)
    return await _to_response(session, order)


async def submit_review(session: AsyncSession, order_id: int, user_id: int, req: ReviewCreate) -> AccompanyOrderResponse:
    order = await repo.get_by_id(session, order_id)
    if not order or order.user_id != user_id:
        raise NotFoundException("订单不存在")
    if order.order_status != 3:
        raise BadRequestException("仅服务中的订单可评价")
    if order.service_score is not None:
        raise BadRequestException("已评价过，不可重复评价")

    # 保存评价
    order = await repo.submit_review(session, order, req.service_score, req.service_comment)

    # 更新志愿者评分
    vol = await get_volunteer(session, order.volunteer_id)
    if vol:
        await update_score(session, vol, req.service_score)

    return await _to_response(session, order)


async def list_my_orders(session: AsyncSession, user_id: int, order_status: int | None = None) -> list[AccompanyOrderResponse]:
    orders = await repo.list_by_user(session, user_id, order_status)
    return [await _to_response(session, o) for o in orders]
