"""挂号预约路由层"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user, require_admin
from app.auth.models import UserModel
from app.reserve.schemas import ReserveCreateRequest, ReserveResponse
from app.reserve import service

router = APIRouter(prefix="/api/reserves", tags=["挂号预约"])


@router.post("", response_model=ApiResponse[ReserveResponse])
async def create_reserve(
    req: ReserveCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """提交挂号预约（生成待支付订单 + Redis 扣减号源 + 15分钟延时取消）"""
    data = await service.create_reserve(session, current_user.id, req)
    return ApiResponse.ok(data, message="预约成功，请在15分钟内支付")


@router.get("", response_model=ApiResponse[list[ReserveResponse]])
async def my_reserves(
    order_status: int | None = Query(default=None, description="订单状态筛选"),
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """我的预约列表"""
    data = await service.list_my_reserves(session, current_user.id, order_status)
    return ApiResponse.ok(data)


@router.get("/{reserve_id}", response_model=ApiResponse[ReserveResponse])
async def reserve_detail(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """预约详情"""
    data = await service.get_reserve_detail(session, reserve_id, current_user.id)
    return ApiResponse.ok(data)


@router.post("/{reserve_id}/pay", response_model=ApiResponse[ReserveResponse])
async def pay_reserve(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """支付订单（逻辑：待支付→已预约）"""
    data = await service.pay_reserve(session, reserve_id, current_user.id)
    return ApiResponse.ok(data, message="支付成功")


@router.post("/{reserve_id}/cancel", response_model=ApiResponse)
async def cancel_reserve(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """取消订单 + Redis 回滚号源"""
    await service.cancel_reserve(session, reserve_id, current_user.id)
    return ApiResponse.ok(message="已取消")


# ---- 后台管理 ----
@router.get("/admin/all", response_model=ApiResponse[list[ReserveResponse]])
async def admin_list_reserves(
    order_status: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
):
    """管理员查看全部预约"""
    from app.reserve.repository import list_all
    reserves = await list_all(session, order_status)
    responses = [await service._build_response(session, r) for r in reserves]
    return ApiResponse.ok(responses)
