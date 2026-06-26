"""科室模块路由层"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import require_admin
from app.department.schemas import DeptCreate, DeptUpdate, DeptResponse, DeptListResponse
from app.department import service

router = APIRouter(prefix="/api/departments", tags=["科室管理"])


@router.get("", response_model=ApiResponse[list[DeptListResponse]])
async def list_departments(session: AsyncSession = Depends(get_db)):
    """查询全部科室列表（公开，含医院名称）"""
    data = await service.list_all(session)
    return ApiResponse.ok(data)


@router.get("/by-hospital/{hospital_id}", response_model=ApiResponse[list[DeptResponse]])
async def list_by_hospital(hospital_id: int, session: AsyncSession = Depends(get_db)):
    """按医院查询科室（公开）"""
    data = await service.list_by_hospital(session, hospital_id)
    return ApiResponse.ok(data)


@router.post("", response_model=ApiResponse[DeptResponse])
async def create_dept(req: DeptCreate, session: AsyncSession = Depends(get_db),
                      _admin=Depends(require_admin)):
    """新增科室（管理员）"""
    data = await service.create_dept(session, req)
    return ApiResponse.ok(data, message="创建成功")


@router.put("/{dept_id}", response_model=ApiResponse[DeptResponse])
async def update_dept(dept_id: int, req: DeptUpdate, session: AsyncSession = Depends(get_db),
                      _admin=Depends(require_admin)):
    """更新科室（管理员）"""
    data = await service.update_dept(session, dept_id, req)
    return ApiResponse.ok(data, message="更新成功")


@router.delete("/{dept_id}", response_model=ApiResponse)
async def delete_dept(dept_id: int, session: AsyncSession = Depends(get_db),
                      _admin=Depends(require_admin)):
    """删除科室（管理员）"""
    await service.delete_dept(session, dept_id)
    return ApiResponse.ok(message="已删除")
