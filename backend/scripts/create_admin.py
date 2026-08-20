"""一键创建管理员账号"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.shared.database import async_session
from app.auth.repository import create_user, get_user_by_username
from app.auth.utils import hash_password


async def main():
    username = input("请输入管理员账号（手机号）: ").strip()
    password = input("请输入密码: ").strip()
    nickname = input("请输入昵称（默认：系统管理员）: ").strip() or "系统管理员"

    async with async_session() as session:
        # 检查是否已存在
        existing = await get_user_by_username(session, username)
        if existing:
            print(f"❌ 账号 {username} 已存在")
            return

        # 创建管理员
        user = await create_user(
            session,
            username=username,
            password=hash_password(password),
            nickname=nickname,
            user_type=3,
        )
        await session.commit()
        print(f"✅ 管理员创建成功！")
        print(f"   账号: {username}")
        print(f"   昵称: {nickname}")
        print(f"   ID: {user.id}")


if __name__ == "__main__":
    asyncio.run(main())
