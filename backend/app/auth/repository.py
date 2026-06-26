"""认证模块数据访问层"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import UserModel


async def get_user_by_username(session: AsyncSession, username: str) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.username == username, UserModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def get_user_by_wx_openid(session: AsyncSession, wx_openid: str) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.wx_openid == wx_openid, UserModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def get_user_by_alipay_user_id(session: AsyncSession, alipay_user_id: str) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.alipay_user_id == alipay_user_id, UserModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_deleted == 0)
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, **kwargs) -> UserModel:
    user = UserModel(**kwargs)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user
