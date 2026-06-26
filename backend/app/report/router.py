"""体检报告路由层"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.service import get_current_user
from app.auth.models import UserModel
from app.report.schemas import ReportUploadResponse, ReportListItem, ReportDetailResponse
from app.report import service

router = APIRouter(prefix="/api/reports", tags=["体检报告"])


@router.post("/upload", response_model=ApiResponse[ReportUploadResponse])
async def upload_report(
    elder_bind_id: int = Form(description="绑定长辈ID"),
    file: UploadFile = File(description="体检报告图片"),
    simulated_text: str | None = Form(default=None, description="模拟OCR文本（开发专用）"),
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """上传体检报告图片，OCR 识别 + 通俗解读"""
    data = await service.upload_report(session, current_user, elder_bind_id, file, simulated_text)
    return ApiResponse.ok(data, message="报告上传成功")


@router.get("", response_model=ApiResponse[list[ReportListItem]])
async def my_reports(
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """我的长辈关联的体检报告列表"""
    data = await service.list_reports_for_user(session, current_user.id)
    return ApiResponse.ok(data)


@router.get("/{report_id}", response_model=ApiResponse[ReportDetailResponse])
async def report_detail(
    report_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """体检报告详情（含 OCR 结果 + 解读）"""
    data = await service.get_report_detail(session, report_id, current_user)
    return ApiResponse.ok(data)


@router.delete("/{report_id}", response_model=ApiResponse)
async def delete_report(
    report_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除体检报告（软删除）"""
    await service.delete_report(session, current_user, report_id)
    return ApiResponse.ok(None, message="报告已删除")
