"""支付路由层

端点：
  POST /api/payment/create   - 创建支付订单（沙箱/模拟）
  POST /api/payment/notify   - 支付宝异步回调（验签）
  GET  /api/payment/result    - 查询支付结果
  POST /api/payment/pay       - 兼容旧接口（模拟支付）
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user
from app.auth.models import UserModel
from app.payment.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResultResponse,
)
from app.payment import service as pay_service

router = APIRouter(prefix="/api/payment", tags=["在线缴费"])


@router.post("/create", response_model=ApiResponse[CreatePaymentResponse])
async def create_payment(
    req: CreatePaymentRequest,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建支付订单

    sandbox 模式：返回支付宝支付页面 URL，前端跳转
    mock 模式：直接完成支付，返回空 URL
    """
    try:
        data = await pay_service.create_payment(session, req, current_user.id)
        return ApiResponse.ok(data, message="支付订单已创建")
    except ValueError as e:
        return ApiResponse.fail(400, str(e))


@router.post("/notify")
async def alipay_notify(request: Request, session: AsyncSession = Depends(get_db)):
    """支付宝异步回调通知

    支付宝会 POST form-data 到此端点。
    返回 "success" 表示确认收到，支付宝不再重发。
    """
    form = await request.form()
    params = {k: v for k, v in form.items()}

    success = await pay_service.handle_alipay_notify(session, params)
    return "success" if success else "fail"


@router.get("/result", response_model=ApiResponse[PaymentResultResponse])
async def payment_result(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """查询支付结果（前端轮询用）"""
    try:
        data = await pay_service.query_payment_result(session, reserve_id, current_user.id)
        return ApiResponse.ok(data)
    except PermissionError as e:
        return ApiResponse.fail(403, str(e))
    except ValueError as e:
        return ApiResponse.fail(400, str(e))


@router.get("/query", response_model=ApiResponse[PaymentResultResponse])
async def payment_query_by_trade_no(
    out_trade_no: str,
    session: AsyncSession = Depends(get_db),
):
    """按商户订单号查询支付结果（支付宝回调跳转用，无需登录）"""
    try:
        data = await pay_service.query_payment_by_trade_no(session, out_trade_no)
        return ApiResponse.ok(data)
    except ValueError as e:
        return ApiResponse.fail(400, str(e))


@router.post("/sync", response_model=ApiResponse[PaymentResultResponse])
async def payment_sync_status(
    out_trade_no: str,
    session: AsyncSession = Depends(get_db),
):
    """主动同步支付宝支付状态（notify 回调未到达时的兜底方案）"""
    try:
        data = await pay_service.sync_payment_status(session, out_trade_no)
        return ApiResponse.ok(data, message="同步完成")
    except ValueError as e:
        return ApiResponse.fail(400, str(e))


@router.post("/pay")
async def legacy_pay(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """兼容旧接口：直接模拟支付

    保留此端点以兼容 OrderList.vue 中的 reserveApi.pay(id) 调用。
    """
    try:
        req = CreatePaymentRequest(reserve_id=reserve_id)
        data = await pay_service.create_payment(session, req, current_user.id)
        return ApiResponse.ok({"amount": data.amount}, message="支付成功")
    except ValueError as e:
        return ApiResponse.fail(400, str(e))
