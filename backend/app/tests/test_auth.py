"""认证模块单元测试 — 注册 / 登录 / JWT / 微信授权"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.auth.utils import hash_password, verify_password, create_access_token, decode_access_token
from app.auth import service


# ═══════════════════════════════════════════
# 1. bcrypt 密码工具测试
# ═══════════════════════════════════════════

class TestPasswordUtils:
    def test_hash_and_verify(self):
        plain = "testpass123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_hash_is_stable_per_input(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1) and verify_password("same", h2)


# ═══════════════════════════════════════════
# 2. JWT 令牌测试
# ═══════════════════════════════════════════

class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token(user_id=42, user_type=1)
        assert isinstance(token, str)
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == 1

    def test_decode_invalid_token(self):
        with pytest.raises(Exception):
            decode_access_token("not.a.valid.token")

    def test_expired_token(self):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.config import settings

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "1", "type": 1, "exp": past}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(Exception):
            decode_access_token(token)


# ═══════════════════════════════════════════
# 3. register() 业务逻辑测试
# ═══════════════════════════════════════════

class TestRegister:
    async def test_register_success(self, mock_session):
        from app.auth.schemas import RegisterRequest

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "13800138000"
        mock_user.nickname = "测试用户"
        mock_user.user_type = 1

        with patch("app.auth.repository.create_user", AsyncMock(return_value=mock_user)):
            req = RegisterRequest(username="13800138000", password="test1234",
                                  nickname="测试用户", user_type=1)
            result = await service.register(mock_session, req)

            assert result.user_id == 1
            assert result.nickname == "测试用户"
            assert result.user_type == 1
            assert result.access_token is not None

    async def test_register_duplicate_username(self, mock_session):
        from app.auth.schemas import RegisterRequest
        from app.exception.base import ConflictException

        existing_user = MagicMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=existing_user)))

        req = RegisterRequest(username="13800138000", password="test1234")
        with pytest.raises(ConflictException, match="已被注册"):
            await service.register(mock_session, req)

    async def test_register_admin_without_prefix(self, mock_session):
        from app.auth.schemas import RegisterRequest
        from app.exception.base import ForbiddenException

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))
        req = RegisterRequest(username="justauser", password="test1234", user_type=3)
        with pytest.raises(ForbiddenException, match="admin_"):
            await service.register(mock_session, req)

    async def test_register_admin_with_prefix(self, mock_session):
        from app.auth.schemas import RegisterRequest

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "admin_test"
        mock_user.nickname = "管理员"
        mock_user.user_type = 3

        with patch("app.auth.repository.create_user", AsyncMock(return_value=mock_user)):
            req = RegisterRequest(username="admin_test", password="test1234",
                                  nickname="管理员", user_type=3)
            result = await service.register(mock_session, req)
            assert result.user_type == 3


# ═══════════════════════════════════════════
# 4. login() 业务逻辑测试
# ═══════════════════════════════════════════

class TestLogin:
    async def test_login_success(self, mock_session):
        from app.auth.schemas import LoginRequest

        hashed = hash_password("mypassword")
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.username = "13800138001"
        mock_user.nickname = "老用户"
        mock_user.user_type = 2
        mock_user.password = hashed

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)))

        req = LoginRequest(username="13800138001", password="mypassword")
        result = await service.login(mock_session, req)
        assert result.user_id == 2
        assert result.nickname == "老用户"

    async def test_login_wrong_password(self, mock_session):
        from app.auth.schemas import LoginRequest
        from app.exception.base import BadRequestException

        hashed = hash_password("correct_password")
        mock_user = MagicMock()
        mock_user.password = hashed

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)))

        req = LoginRequest(username="13800138001", password="wrong_password")
        with pytest.raises(BadRequestException, match="账号或密码错误"):
            await service.login(mock_session, req)

    async def test_login_user_not_found(self, mock_session):
        from app.auth.schemas import LoginRequest
        from app.exception.base import BadRequestException

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        req = LoginRequest(username="nobody", password="any")
        with pytest.raises(BadRequestException):
            await service.login(mock_session, req)


# ═══════════════════════════════════════════
# 5. wx_login() 微信授权测试
# ═══════════════════════════════════════════

class TestWxLogin:
    async def test_wx_login_new_user(self, mock_session):
        from app.auth.schemas import WxLoginRequest

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.nickname = "微信用户"
        mock_user.user_type = 1

        with patch("app.auth.repository.create_user", AsyncMock(return_value=mock_user)):
            req = WxLoginRequest(wx_openid="wx_openid_new_001")
            result = await service.wx_login(mock_session, req)
            assert result.user_id == 10
            assert result.user_type == 1

    async def test_wx_login_existing_user(self, mock_session):
        from app.auth.schemas import WxLoginRequest

        mock_user = MagicMock()
        mock_user.id = 11
        mock_user.username = "13800138002"
        mock_user.nickname = "回头客"
        mock_user.user_type = 2

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)))

        req = WxLoginRequest(wx_openid="wx_openid_returning_001")
        result = await service.wx_login(mock_session, req)
        assert result.user_id == 11
        assert result.nickname == "回头客"


# ═══════════════════════════════════════════
# 6. API 端点集成测试
# ═══════════════════════════════════════════

@pytest.mark.integration
class TestAuthAPI:
    async def test_register_endpoint(self, client, _mock_db_session):
        mock_session = _mock_db_session
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)))

        mock_user = MagicMock()
        mock_user.id = 99
        mock_user.username = "13900001111"
        mock_user.nickname = "API用户"
        mock_user.user_type = 1

        with patch("app.auth.repository.create_user", AsyncMock(return_value=mock_user)):
            resp = await client.post("/api/auth/register", json={
                "username": "13900001111",
                "password": "api_test_123",
                "nickname": "API用户",
                "user_type": 1,
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["message"] == "注册成功"
        assert "access_token" in body["data"]

    async def test_login_endpoint(self, client, _mock_db_session):
        mock_session = _mock_db_session
        hashed = hash_password("api_login_pass")
        mock_user = MagicMock()
        mock_user.id = 55
        mock_user.username = "13900002222"
        mock_user.nickname = "登录测试"
        mock_user.user_type = 2
        mock_user.password = hashed

        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)))

        resp = await client.post("/api/auth/login", json={
            "username": "13900002222",
            "password": "api_login_pass",
        })

        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["user_id"] == 55

    async def test_login_wrong_password_api(self, client, _mock_db_session):
        mock_session = _mock_db_session
        hashed = hash_password("correct")
        mock_user = MagicMock()
        mock_user.password = hashed
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)))

        resp = await client.post("/api/auth/login", json={
            "username": "user", "password": "wrong",
        })

        assert resp.status_code == 400

    async def test_health_check(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
