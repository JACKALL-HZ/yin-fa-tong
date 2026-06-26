"""用户中心路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user
from app.auth.models import UserModel
from app.user.schemas import ElderBindCreate, ElderBindUpdate, ElderBindResponse, ElderReminderResponse, ProfileUpdate, ProfileResponse
from app.user import service

router = APIRouter(prefix="/api/user", tags=["用户中心"])


@router.put("/profile", response_model=ApiResponse[ProfileResponse])
async def update_profile(
    req: ProfileUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """完善/更新用户个人信息"""
    data = await service.update_profile(session, current_user, req)
    return ApiResponse.ok(data, message="信息已更新")


@router.get("/elders", response_model=ApiResponse[list[ElderBindResponse]])
async def list_elders(
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取我绑定的长辈列表"""
    data = await service.list_elders(session, current_user.id)
    return ApiResponse.ok(data)


@router.get("/elders/reminders", response_model=ApiResponse[ElderReminderResponse])
async def elder_reminders(
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取长辈代办任务和智能提醒（基于真实挂号数据）"""
    data = await service.get_elder_reminders(session, current_user.id)
    return ApiResponse.ok(data)


@router.post("/elders", response_model=ApiResponse[ElderBindResponse])
async def create_elder(
    req: ElderBindCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """绑定新长辈"""
    data = await service.create_elder(session, current_user.id, req)
    return ApiResponse.ok(data, message="绑定成功")


@router.put("/elders/{bind_id}", response_model=ApiResponse[ElderBindResponse])
async def update_elder(
    bind_id: int,
    req: ElderBindUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """更新长辈信息"""
    data = await service.update_elder(session, bind_id, current_user.id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/elders/{bind_id}", response_model=ApiResponse)
async def delete_elder(
    bind_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """解绑长辈（逻辑删除）"""
    await service.delete_elder(session, bind_id, current_user.id)
    return ApiResponse.ok(message="已解绑")
