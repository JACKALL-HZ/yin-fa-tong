"""认证模块业务逻辑层"""

import logging

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import UserModel
from app.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    WxLoginRequest,
    AlipayLoginRequest,
    TokenResponse,
)
from app.auth import repository as repo
from app.auth.utils import hash_password, verify_password, create_access_token, decode_access_token
from app.shared.database import get_db
from app.exception.base import (
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# 支付宝客户端单例（避免每次请求重新初始化）
_alipay_client = None


def _get_alipay_client():
    """获取支付宝客户端单例"""
    global _alipay_client
    if _alipay_client is not None:
        return _alipay_client

    from app.config import settings
    from alipay.aop.api.AlipayClientFactory import AlipayClientFactory

    factory = AlipayClientFactory(
        alipay_public_key=settings.ALIPAY_PUBLIC_KEY,
        app_private_key=settings.ALIPAY_PRIVATE_KEY,
        app_id=settings.ALIPAY_APP_ID,
        sign_type="RSA2",
    )
    _alipay_client = factory.get_client()
    _alipay_client.server_url = settings.ALIPAY_GATEWAY
    return _alipay_client


async def register(session: AsyncSession, req: RegisterRequest) -> TokenResponse:
    # 检查账号是否已存在
    existing = await repo.get_user_by_username(session, req.username)
    if existing:
        raise ConflictException("该账号已被注册")

    # 管理员注册需注册码校验
    if req.user_type == 3:
        from app.config import settings
        if not req.admin_code or req.admin_code != settings.ADMIN_REGISTER_CODE:
            raise ForbiddenException("管理员注册码错误")

    user = await repo.create_user(
        session,
        username=req.username,
        password=hash_password(req.password),
        nickname=req.nickname,
        user_type=req.user_type,
    )
    token = create_access_token(user.id, user.user_type)
    return TokenResponse(access_token=token, user_id=user.id, nickname=user.nickname, user_type=user.user_type)


async def login(session: AsyncSession, req: LoginRequest) -> TokenResponse:
    user = await repo.get_user_by_username(session, req.username)
    if not user or not verify_password(req.password, user.password):
        raise BadRequestException("账号或密码错误")

    token = create_access_token(user.id, user.user_type)
    return TokenResponse(access_token=token, user_id=user.id, nickname=user.nickname, user_type=user.user_type)


async def wx_login(session: AsyncSession, req: WxLoginRequest) -> TokenResponse:
    """模拟微信授权登录：首次自动注册，后续直接登录"""
    user = await repo.get_user_by_wx_openid(session, req.wx_openid)
    if not user:
        # 首次授权，自动创建账号
        user = await repo.create_user(
            session,
            wx_openid=req.wx_openid,
            password=hash_password(req.wx_openid),  # 模拟：微信用户默认密码为 openid
            nickname=req.nickname,
            user_type=1,  # 默认老年用户
        )
    token = create_access_token(user.id, user.user_type)
    return TokenResponse(access_token=token, user_id=user.id, nickname=user.nickname, user_type=user.user_type)


async def alipay_login(session: AsyncSession, req: AlipayLoginRequest) -> TokenResponse:
    """支付宝 OAuth 扫码登录：用 auth_code 换用户信息，首次自动注册"""
    from app.config import settings

    # 动态导入支付宝 SDK（兼容未安装情况）
    try:
        from alipay.aop.api.domain.AlipaySystemOauthTokenRequest import AlipaySystemOauthTokenRequest
        from alipay.aop.api.domain.AlipayUserInfoShareRequest import AlipayUserInfoShareRequest
    except ImportError:
        raise BadRequestException("支付宝 SDK 未安装，请执行 pip install alipay-sdk-python")

    if not settings.ALIPAY_APP_ID or not settings.ALIPAY_PRIVATE_KEY:
        raise BadRequestException("支付宝配置缺失，请检查 ALIPAY_APP_ID 和密钥配置")

    client = _get_alipay_client()

    # Step 1: auth_code 换 access_token + user_id
    token_req = AlipaySystemOauthTokenRequest()
    token_req.grant_type = "authorization_code"
    token_req.code = req.auth_code
    token_resp = client.execute(token_req)

    if not token_resp or token_resp.get("code") != "10000":
        msg = token_resp.get("sub_msg", token_resp.get("msg", "未知错误")) if token_resp else "支付宝服务无响应"
        raise BadRequestException(f"支付宝授权失败: {msg}")

    # 验证响应签名（防伪造）
    if not client.verify_sign(token_resp):
        raise BadRequestException("支付宝响应签名校验失败")

    alipay_user_id = token_resp.get("user_id")
    access_token = token_resp.get("access_token")

    if not alipay_user_id:
        raise BadRequestException("支付宝未返回用户标识")

    # Step 2: 用 access_token 获取用户昵称
    nickname = "支付宝用户"
    try:
        info_req = AlipayUserInfoShareRequest()
        info_req.auth_token = access_token
        info_resp = client.execute(info_req)
        if info_resp and info_resp.get("code") == "10000":
            user_name = info_resp.get("user_name")
            if user_name:
                nickname = user_name
    except Exception as exc:
        logger.warning("获取支付宝用户昵称失败: %s", exc)

    # Step 3: 按 alipay_user_id 查库，找到则登录，未找到则自动注册
    user = await repo.get_user_by_alipay_user_id(session, alipay_user_id)
    if not user:
        user = await repo.create_user(
            session,
            alipay_user_id=alipay_user_id,
            nickname=nickname,
            password=hash_password(alipay_user_id),  # 随机密码，OAuth 用户不使用密码登录
            user_type=1,  # 默认老年用户
        )

    token = create_access_token(user.id, user.user_type)
    return TokenResponse(access_token=token, user_id=user.id, nickname=user.nickname, user_type=user.user_type)


async def get_current_user(
    session: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserModel:
    """JWT 鉴权依赖：从 Authorization Header 解析用户"""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
    except Exception:
        raise UnauthorizedException("Token 无效或已过期")

    user = await repo.get_user_by_id(session, user_id)
    if not user:
        raise UnauthorizedException("用户不存在")
    return user


def require_admin(user: UserModel = Depends(get_current_user)):
    """管理员权限校验依赖"""
    if user.user_type != 3:
        raise ForbiddenException("仅管理员可操作")
    return user
