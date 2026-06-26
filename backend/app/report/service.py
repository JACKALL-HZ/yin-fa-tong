"""体检报告业务逻辑层"""

import json
import os
import uuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.report.schemas import ReportUploadResponse, ReportListItem, ReportDetailResponse
from app.report import repository as repo
from app.report.ocr.engine import recognize_and_extract
from app.report.template.interpreter import interpret
from app.user.models import ElderBindModel
from app.user.repository import get_elder_ids_by_user
from app.auth.models import UserModel
from app.exception.base import NotFoundException, BadRequestException, ForbiddenException

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def _validate_image(file: UploadFile):
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(f"不支持的图片格式：{ext}，支持 {', '.join(ALLOWED_EXTENSIONS)}")


async def _read_file_bytes(file: UploadFile) -> bytes:
    """读取上传文件内容并校验大小"""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise BadRequestException("图片大小不能超过 10MB")
    return content


def _save_bytes(content: bytes, filename: str) -> str:
    """保存字节到 uploads 目录，返回 URL 相对路径"""
    upload_dir = settings.upload_dir_absolute
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(filename or ".jpg")[-1].lower()
    saved_name = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, saved_name)

    with open(filepath, "wb") as f:
        f.write(content)

    return f"/uploads/{saved_name}"


async def upload_report(
    session: AsyncSession,
    current_user: UserModel,
    elder_bind_id: int,
    file: UploadFile,
    simulated_text: str | None = None,
) -> ReportUploadResponse:
    """
    上传体检报告：
    1. 校验长辈归属 + 图片格式
    2. 读取文件内容
    3. 保存图片磁盘
    4. OCR 识别指标（模拟文本模式用于开发演示）
    5. 规则引擎通俗解读
    6. 落库
    """
    # 校验 elder_bind_id 归属：必须属于当前用户
    from app.user.repository import get_by_id as get_bind_by_id
    bind = await get_bind_by_id(session, elder_bind_id, current_user.id)
    if not bind:
        raise ForbiddenException("无权操作该亲情账号")

    _validate_image(file)
    content = await _read_file_bytes(file)

    # 保存图片
    report_url = _save_bytes(content, file.filename or "report.jpg")

    # OCR 识别 + 指标提取
    ocr_data = recognize_and_extract(content, simulated_text)
    indicators = ocr_data.get("indicators", {})

    # 通俗解读
    interpretation_text = interpret(indicators)

    # 落库
    report = await repo.create(
        session,
        elder_bind_id=elder_bind_id,
        report_url=report_url,
        ocr_result=json.dumps(ocr_data, ensure_ascii=False),
        interpretation=interpretation_text,
    )

    return ReportUploadResponse(
        id=report.id,
        elder_bind_id=report.elder_bind_id,
        report_url=report.report_url,
        ocr_result=ocr_data,
        interpretation=report.interpretation,
        create_time=report.create_time,
    )


async def _to_item(session: AsyncSession, report) -> ReportListItem:
    elder_name = None
    elder_result = await session.execute(
        select(ElderBindModel).where(ElderBindModel.id == report.elder_bind_id)
    )
    elder = elder_result.scalar_one_or_none()
    if elder:
        elder_name = elder.elder_name

    return ReportListItem(
        id=report.id, elder_bind_id=report.elder_bind_id,
        elder_name=elder_name, report_url=report.report_url,
        interpretation=report.interpretation, create_time=report.create_time,
    )


async def get_report_detail(
    session: AsyncSession, report_id: int, current_user: UserModel
) -> ReportDetailResponse:
    """获取报告详情（含权限校验）"""
    report = await repo.get_by_id(session, report_id)
    if not report:
        raise NotFoundException("报告不存在")

    # 权限校验：只能查看绑定老人的报告
    elder_ids = await get_elder_ids_by_user(session, current_user.id)
    if report.elder_bind_id not in elder_ids:
        raise ForbiddenException("无权查看该报告")

    ocr_result = None
    if report.ocr_result:
        try:
            ocr_result = json.loads(report.ocr_result)
        except json.JSONDecodeError:
            ocr_result = {"raw": report.ocr_result}

    return ReportDetailResponse(
        id=report.id,
        elder_bind_id=report.elder_bind_id,
        report_url=report.report_url,
        ocr_result=ocr_result,
        interpretation=report.interpretation,
        create_time=report.create_time,
    )


async def list_my_reports(session: AsyncSession, elder_bind_ids: list[int]) -> list[ReportListItem]:
    reports = await repo.list_by_user_elders(session, elder_bind_ids)
    return [await _to_item(session, r) for r in reports]


async def list_reports_for_user(session: AsyncSession, user_id: int) -> list[ReportListItem]:
    """根据用户 ID 查询其名下所有长辈的体检报告"""
    elder_ids = await get_elder_ids_by_user(session, user_id)
    return await list_my_reports(session, elder_ids)


async def delete_report(session: AsyncSession, current_user: UserModel, report_id: int) -> None:
    """删除报告（软删除），需校验归属"""
    report = await repo.get_by_id(session, report_id)
    if not report:
        raise NotFoundException("报告不存在")

    # 校验报告所属长辈是否属于当前用户
    elder_ids = await get_elder_ids_by_user(session, current_user.id)
    if report.elder_bind_id not in elder_ids:
        raise ForbiddenException("无权删除该报告")

    await repo.soft_delete(session, report)
