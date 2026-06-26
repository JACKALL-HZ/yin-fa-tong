"""志愿者路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user, require_admin
from app.accompany.volunteer.schemas import VolunteerCreate, VolunteerUpdate, VolunteerResponse
from app.accompany.volunteer import service

router = APIRouter(prefix="/api/volunteers", tags=["志愿者"])


@router.get("", response_model=ApiResponse[list[VolunteerResponse]])
async def list_volunteers(session: AsyncSession = Depends(get_db)):
    """可预约志愿者列表（公开，按评分降序）"""
    data = await service.list_available(session)
    return ApiResponse.ok(data)


@router.get("/{vol_id}", response_model=ApiResponse[VolunteerResponse])
async def volunteer_detail(vol_id: int, session: AsyncSession = Depends(get_db)):
    """志愿者详情"""
    data = await service.get_detail(session, vol_id)
    return ApiResponse.ok(data)


@router.post("", response_model=ApiResponse[VolunteerResponse])
async def create_volunteer(req: VolunteerCreate, session: AsyncSession = Depends(get_db),
                           _admin=Depends(require_admin)):
    """新增志愿者（管理员）"""
    data = await service.create_volunteer(session, req)
    return ApiResponse.ok(data, message="创建成功")


@router.put("/{vol_id}", response_model=ApiResponse[VolunteerResponse])
async def update_volunteer(vol_id: int, req: VolunteerUpdate, session: AsyncSession = Depends(get_db),
                           _admin=Depends(require_admin)):
    """更新志愿者（管理员）"""
    data = await service.update_volunteer(session, vol_id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/{vol_id}", response_model=ApiResponse)
async def delete_volunteer(vol_id: int, session: AsyncSession = Depends(get_db),
                           _admin=Depends(require_admin)):
    """删除志愿者（管理员）"""
    await service.delete_volunteer(session, vol_id)
    return ApiResponse.ok(message="已删除")
