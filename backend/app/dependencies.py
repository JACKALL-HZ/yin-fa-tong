"""全局依赖注入

集中管理 FastAPI Depends() 依赖，供路由层统一引用。
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db

# 数据库会话依赖（类型别名，路由层可直接用 DbSession）
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ---- 分页参数 ----
async def pagination_params(
    page: int = 1,
    page_size: int = 10,
):
    """通用分页参数依赖"""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100
    return {"page": page, "page_size": page_size}


Pagination = Annotated[dict, Depends(pagination_params)]
