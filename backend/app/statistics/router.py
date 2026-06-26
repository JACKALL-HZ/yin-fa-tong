"""数据统计路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import require_admin
from app.statistics.service import dashboard

router = APIRouter(prefix="/api/statistics", tags=["数据统计"])


@router.get("/dashboard", response_model=ApiResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """运营数据看板（管理员）"""
    data = await dashboard(session)
    return ApiResponse.ok(data)
