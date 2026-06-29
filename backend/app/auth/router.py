"""认证模块路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.schemas import (
    RegisterRequest,
    RegisterWithCodeRequest,
    LoginRequest,
    WxLoginRequest,
    AlipayLoginRequest,
    SendSmsCodeRequest,
    SmsLoginRequest,
    AdminLoginRequest,
    TokenResponse,
    UserInfoResponse,
)
from app.auth import service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[TokenResponse])
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_db)):
    """账号密码注册"""
    data = await service.register(session, req)
    return ApiResponse.ok(data, message="注册成功")


@router.post("/register/code", response_model=ApiResponse[TokenResponse])
async def register_with_code(req: RegisterWithCodeRequest, session: AsyncSession = Depends(get_db)):
    """手机号+验证码注册"""
    data = await service.register_with_code(session, req)
    return ApiResponse.ok(data, message="注册成功")


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(req: LoginRequest, session: AsyncSession = Depends(get_db)):
    """账号密码登录"""
    data = await service.login(session, req)
    return ApiResponse.ok(data, message="登录成功")


@router.post("/wx-login", response_model=ApiResponse[TokenResponse])
async def wx_login(req: WxLoginRequest, session: AsyncSession = Depends(get_db)):
    """模拟微信授权登录"""
    data = await service.wx_login(session, req)
    return ApiResponse.ok(data, message="登录成功")


@router.post("/alipay-login", response_model=ApiResponse[TokenResponse])
async def alipay_login(req: AlipayLoginRequest, session: AsyncSession = Depends(get_db)):
    """支付宝 OAuth 扫码登录"""
    data = await service.alipay_login(session, req)
    return ApiResponse.ok(data, message="登录成功")


@router.post("/sms/send", response_model=ApiResponse)
async def send_sms_code(req: SendSmsCodeRequest, session: AsyncSession = Depends(get_db)):
    """发送短信验证码"""
    await service.send_sms_code(session, req)
    return ApiResponse.ok(message="验证码发送成功")


@router.post("/sms/login", response_model=ApiResponse[TokenResponse])
async def sms_login(req: SmsLoginRequest, session: AsyncSession = Depends(get_db)):
    """手机号验证码登录/注册"""
    data = await service.sms_login(session, req)
    return ApiResponse.ok(data, message="登录成功")


@router.post("/admin/login", response_model=ApiResponse[TokenResponse])
async def admin_login(req: AdminLoginRequest, session: AsyncSession = Depends(get_db)):
    """管理员登录"""
    data = await service.admin_login(session, req)
    return ApiResponse.ok(data, message="登录成功")


@router.get("/me", response_model=ApiResponse[UserInfoResponse])
async def get_me(session: AsyncSession = Depends(get_db),
                 current_user=Depends(service.get_current_user)):
    """获取当前登录用户信息"""
    profile_complete = all([
        current_user.real_name,
        current_user.gender,
        current_user.id_card,
        current_user.birthday,
    ])
    info = UserInfoResponse(
        id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        user_type=current_user.user_type,
        wx_openid=current_user.wx_openid,
        real_name=current_user.real_name,
        gender=current_user.gender,
        id_card=current_user.id_card,
        birthday=current_user.birthday,
        phone=current_user.phone,
        profile_complete=profile_complete,
    )
    return ApiResponse.ok(info)
