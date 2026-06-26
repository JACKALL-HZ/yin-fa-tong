"""医院模块路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user, require_admin
from app.hospital.schemas import HospitalCreate, HospitalUpdate, HospitalResponse
from app.hospital import service

router = APIRouter(prefix="/api/hospitals", tags=["医院管理"])


@router.get("", response_model=ApiResponse[list[HospitalResponse]])
async def list_hospitals(session: AsyncSession = Depends(get_db)):
    """查询医院列表（公开）"""
    data = await service.list_hospitals(session)
    return ApiResponse.ok(data)


@router.post("", response_model=ApiResponse[HospitalResponse])
async def create_hospital(req: HospitalCreate, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """新增医院（管理员）"""
    data = await service.create_hospital(session, req)
    return ApiResponse.ok(data, message="创建成功")


@router.put("/{hospital_id}", response_model=ApiResponse[HospitalResponse])
async def update_hospital(hospital_id: int, req: HospitalUpdate, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """更新医院（管理员）"""
    data = await service.update_hospital(session, hospital_id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/{hospital_id}", response_model=ApiResponse)
async def delete_hospital(hospital_id: int, session: AsyncSession = Depends(get_db),
                          _admin=Depends(require_admin)):
    """删除医院（管理员）"""
    await service.delete_hospital(session, hospital_id)
    return ApiResponse.ok(message="已删除")
