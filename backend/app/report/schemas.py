"""体检报告 Pydantic 模型"""

from datetime import datetime
from pydantic import BaseModel, Field


class ReportUploadResponse(BaseModel):
    id: int
    elder_bind_id: int
    report_url: str
    ocr_result: dict | None = None
    interpretation: str | None = None
    create_time: datetime


class ReportListItem(BaseModel):
    id: int
    elder_bind_id: int
    elder_name: str | None = None
    report_url: str
    interpretation: str | None = None
    create_time: datetime


class ReportDetailResponse(BaseModel):
    id: int
    elder_bind_id: int
    report_url: str
    ocr_result: dict | None = None
    interpretation: str | None = None
    create_time: datetime | None = None
