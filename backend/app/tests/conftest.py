"""测试公共 Fixtures

Mock 全部外部依赖（DB / Redis / RabbitMQ），不依赖任何真实服务。
"""

import sys
import os as _os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# ── 跳过生产环境配置校验 ──
_os.environ["YFT_SKIP_CONFIG_CHECK"] = "1"

# ── 必须在 import app 之前 mock SQLAlchemy engine ──
# app/shared/database.py 在模块级别调用了 create_async_engine()
# 如果不 mock 会导致 import 时尝试连接 MySQL 而失败

def _setup_pre_import_mocks():
    """在导入 app 之前 mock engine 创建"""
    import sqlalchemy.ext.asyncio as sa_asyncio
    _orig = sa_asyncio.create_async_engine

    def _mock_create_async_engine(*args, **kwargs):
        return MagicMock()

    sa_asyncio.create_async_engine = _mock_create_async_engine


_setup_pre_import_mocks()


# ── 现在可以安全导入 app ──
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture(autouse=True)
def _mock_db_session():
    """Mock SQLAlchemy AsyncSession"""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    from unittest.mock import patch
    with patch("app.shared.database.AsyncSessionLocal", autospec=True) as mock_factory:
        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_factory.return_value.__aexit__.return_value = None
        yield mock_session


@pytest.fixture(autouse=True)
def _mock_redis():
    """Mock Redis 客户端"""
    from unittest.mock import patch

    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value="10")
    mock_redis.set = AsyncMock()
    mock_redis.eval = AsyncMock(return_value=1)
    mock_redis.incrby = AsyncMock()
    mock_redis.decrby = AsyncMock()

    with patch("app.shared.redis.init_redis", AsyncMock(return_value=mock_redis)):
        with patch("app.shared.redis.get_redis", AsyncMock(return_value=mock_redis)):
            yield mock_redis


@pytest.fixture(autouse=True)
def _mock_rabbitmq():
    """Mock RabbitMQ"""
    from unittest.mock import patch
    with patch("app.reserve.mq.producer.send_payment_timeout", AsyncMock()):
        with patch("app.reserve.mq.producer.send_reserve_success", AsyncMock()):
            with patch("app.shared.rabbitmq.publish_direct", AsyncMock()):
                yield


@pytest.fixture
async def client():
    """FastAPI 异步测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_session():
    """独立 mock session"""
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    mock.execute = AsyncMock()
    mock.add = MagicMock()
    mock.flush = AsyncMock()
    mock.refresh = AsyncMock()
    return mock


@pytest.fixture(scope="session")
def event_loop_policy():
    """Windows 事件循环策略"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.get_event_loop_policy()
