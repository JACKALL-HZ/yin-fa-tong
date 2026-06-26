"""健康提醒路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user
from app.auth.models import UserModel
from app.reminder.schemas import ReminderCreate, ReminderResponse, ReminderToggle
from app.reminder import service

router = APIRouter(prefix="/api/reminders", tags=["健康提醒"])


@router.post("", response_model=ApiResponse[ReminderResponse])
async def create_reminder(
    req: ReminderCreate,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建健康提醒（自动延时推送到 Delay 队列）"""
    data = await service.create_reminder(session, current_user.id, req)
    return ApiResponse.ok(data, message="提醒已创建")


@router.get("", response_model=ApiResponse[list[ReminderResponse]])
async def list_reminders(
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """我的提醒列表"""
    data = await service.list_reminders(session, current_user.id)
    return ApiResponse.ok(data)


@router.patch("/{reminder_id}/toggle", response_model=ApiResponse)
async def toggle_reminder(
    reminder_id: int,
    req: ReminderToggle,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """启用/停用提醒"""
    await service.toggle_active(session, current_user.id, reminder_id, req.is_active)
    return ApiResponse.ok(message="已启用" if req.is_active else "已停用")


@router.delete("/{reminder_id}", response_model=ApiResponse)
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除提醒（软删除）"""
    await service.delete_reminder(session, current_user.id, reminder_id)
    return ApiResponse.ok(message="提醒已删除")
