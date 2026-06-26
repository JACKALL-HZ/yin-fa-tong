"""MySQL 异步数据库连接管理"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类 —— 所有 Model 继承此类"""
    pass


def register_es_hook(session: AsyncSession, coro_factory):
    """注册 ES 同步钩子，在 DB commit 成功后执行。

    Args:
        session: 当前数据库会话
        coro_factory: 无参协程工厂函数，如 lambda: sync_hospital_create(h)
    """
    hooks: list = session.info.setdefault("es_hooks", [])
    hooks.append(coro_factory)


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话

    支持 post-commit hooks：service 层可通过 session.info["es_hooks"] 注册
    在 DB commit 成功后才执行的回调（如 ES 同步），避免双写不一致。
    """
    async with AsyncSessionLocal() as session:
        pending_hooks: list = []
        session.info["es_hooks"] = pending_hooks
        try:
            yield session
            await session.commit()
            # commit 成功后执行所有注册的 ES 同步钩子
            for hook in pending_hooks:
                try:
                    await hook()
                except Exception:
                    import logging
                    logging.getLogger(__name__).warning(
                        "Post-commit hook 失败: %s", hook, exc_info=True
                    )
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
