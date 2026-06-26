"""陪诊订单路由层"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user, require_admin
from app.auth.models import UserModel
from app.accompany.order.schemas import AccompanyOrderCreate, ReviewCreate, AccompanyOrderResponse
from app.accompany.order import service
from app.accompany.order.repository import list_all

router = APIRouter(prefix="/api/accompany-orders", tags=["陪诊订单"])


@router.post("", response_model=ApiResponse[AccompanyOrderResponse])
async def create_order(
    req: AccompanyOrderCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """提交陪诊申请（自选志愿者，生成待审核订单）"""
    data = await service.create_order(session, current_user.id, req)
    return ApiResponse.ok(data, message="申请已提交，等待审核")


@router.get("", response_model=ApiResponse[list[AccompanyOrderResponse]])
async def my_orders(
    order_status: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """我的陪诊订单"""
    data = await service.list_my_orders(session, current_user.id, order_status)
    return ApiResponse.ok(data)


@router.post("/{order_id}/review", response_model=ApiResponse[AccompanyOrderResponse])
async def review_order(
    order_id: int,
    req: ReviewCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """服务评价（1-5分 + 文字，更新志愿者评分）"""
    data = await service.submit_review(session, order_id, current_user.id, req)
    return ApiResponse.ok(data, message="评价成功")


# ---- 管理员操作 ----
@router.get("/admin/all", response_model=ApiResponse[list[AccompanyOrderResponse]])
async def admin_orders(
    order_status: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """管理员查看全部陪诊订单"""
    orders = await list_all(session, order_status)
    responses = [await service._to_response(session, o) for o in orders]
    return ApiResponse.ok(responses)


@router.post("/{order_id}/approve", response_model=ApiResponse[AccompanyOrderResponse])
async def approve_order(order_id: int, session: AsyncSession = Depends(get_db),
                        _admin=Depends(require_admin)):
    """审核通过：待审核→待服务"""
    data = await service.approve_order(session, order_id)
    return ApiResponse.ok(data, message="已审核通过")


@router.post("/{order_id}/reject", response_model=ApiResponse)
async def reject_order(order_id: int, session: AsyncSession = Depends(get_db),
                       _admin=Depends(require_admin)):
    """审核拒绝"""
    await service.reject_order(session, order_id)
    return ApiResponse.ok(message="已拒绝")


@router.post("/{order_id}/start", response_model=ApiResponse[AccompanyOrderResponse])
async def start_service(order_id: int, session: AsyncSession = Depends(get_db),
                        _admin=Depends(require_admin)):
    """开始服务：待服务→服务中"""
    data = await service.start_service(session, order_id)
    return ApiResponse.ok(data, message="服务已开始")


@router.post("/{order_id}/complete", response_model=ApiResponse[AccompanyOrderResponse])
async def complete_service(order_id: int, session: AsyncSession = Depends(get_db),
                           _admin=Depends(require_admin)):
    """完成服务：服务中→已完成"""
    data = await service.complete_service(session, order_id)
    return ApiResponse.ok(data, message="服务已完成")
