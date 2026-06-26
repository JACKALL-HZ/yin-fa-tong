"""候诊排队路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user, require_admin
from app.auth.models import UserModel
from app.queue import service

router = APIRouter(prefix="/api/queue", tags=["候诊排队"])


@router.get("/status/{schedule_id}", response_model=ApiResponse)
async def queue_status(schedule_id: int):
    """查询排班的实时候诊进度（公开）"""
    data = await service.get_queue_status(schedule_id)
    return ApiResponse.ok(data)


@router.get("/my-position/{queue_code}", response_model=ApiResponse)
async def my_position(queue_code: str, _user=Depends(get_current_user)):
    """查询我的排队位置"""
    data = await service.get_my_queue_position(queue_code)
    if data is None:
        return ApiResponse.fail(404, "候诊编号不存在")
    return ApiResponse.ok(data)


@router.post("/call-next/{schedule_id}", response_model=ApiResponse)
async def call_next(schedule_id: int, _admin=Depends(require_admin)):
    """叫下一个号（管理员/医生）"""
    next_num = await service.call_next(schedule_id)
    return ApiResponse.ok({"next_number": next_num}, message=f"请{next_num}号就诊")
