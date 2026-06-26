"""医生模块路由层"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import require_admin
from app.doctor.schemas import DoctorCreate, DoctorUpdate, DoctorResponse
from app.doctor import service

router = APIRouter(prefix="/api/doctors", tags=["医生管理"])


@router.get("", response_model=ApiResponse[list[DoctorResponse]])
async def list_doctors(dept_id: int | None = None, session: AsyncSession = Depends(get_db)):
    """查询医生列表（公开），可按科室筛选"""
    if dept_id:
        data = await service.list_by_dept(session, dept_id)
    else:
        data = await service.list_all(session)
    return ApiResponse.ok(data)


@router.post("", response_model=ApiResponse[DoctorResponse])
async def create_doctor(req: DoctorCreate, session: AsyncSession = Depends(get_db),
                        _admin=Depends(require_admin)):
    """新增医生（管理员）"""
    data = await service.create_doctor(session, req)
    return ApiResponse.ok(data, message="创建成功")


@router.put("/{doctor_id}", response_model=ApiResponse[DoctorResponse])
async def update_doctor(doctor_id: int, req: DoctorUpdate, session: AsyncSession = Depends(get_db),
                        _admin=Depends(require_admin)):
    """更新医生（管理员）"""
    data = await service.update_doctor(session, doctor_id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/{doctor_id}", response_model=ApiResponse)
async def delete_doctor(doctor_id: int, session: AsyncSession = Depends(get_db),
                        _admin=Depends(require_admin)):
    """删除医生（管理员）"""
    await service.delete_doctor(session, doctor_id)
    return ApiResponse.ok(message="已删除")
