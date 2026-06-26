"""排班号源路由层"""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import require_admin
from app.schedule.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.schedule import service

router = APIRouter(prefix="/api/schedules", tags=["排班号源"])


@router.get("", response_model=ApiResponse[list[ScheduleResponse]])
async def list_schedules(
    doctor_id: int | None = Query(default=None, description="按医生筛选"),
    from_date: date | None = Query(default=None, description="起始日期"),
    session: AsyncSession = Depends(get_db),
):
    """查询排班号源（公开，含 Redis 实时剩余号源）"""
    data = await service.list_schedules(session, doctor_id, from_date)
    return ApiResponse.ok(data)


@router.get("/by-doctor/{doctor_id}", response_model=ApiResponse[list[ScheduleResponse]])
async def list_by_doctor(
    doctor_id: int,
    from_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    """按医生查询排班（公开）"""
    data = await service.list_schedules(session, doctor_id, from_date)
    return ApiResponse.ok(data)


@router.get("/{schedule_id}", response_model=ApiResponse[ScheduleResponse])
async def get_schedule(
    schedule_id: int,
    session: AsyncSession = Depends(get_db),
):
    """查询单个排班详情（公开，含 Redis 实时剩余号源 + 四级联表）"""
    data = await service.get_schedule_by_id(session, schedule_id)
    return ApiResponse.ok(data)


@router.post("", response_model=ApiResponse[ScheduleResponse])
async def create_schedule(req: ScheduleCreate, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """创建排班（管理员，同时同步号源到 Redis）"""
    data = await service.create_schedule(session, req)
    return ApiResponse.ok(data, message="排班创建成功")


@router.put("/{schedule_id}", response_model=ApiResponse[ScheduleResponse])
async def update_schedule(schedule_id: int, req: ScheduleUpdate, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """更新号源数量（管理员，同步 Redis）"""
    data = await service.update_schedule(session, schedule_id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/{schedule_id}", response_model=ApiResponse)
async def delete_schedule(schedule_id: int, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """删除排班（管理员）"""
    await service.delete_schedule(session, schedule_id)
    return ApiResponse.ok(message="已删除")
