"""志愿者 Pydantic 模型"""

from decimal import Decimal
from pydantic import BaseModel, Field


class VolunteerCreate(BaseModel):
    vol_name: str = Field(min_length=1, max_length=32)
    vol_phone: str = Field(min_length=1, max_length=20)
    service_dept: str | None = Field(default=None, max_length=100, description="可服务科室")
    service_desc: str | None = Field(default=None, max_length=255, description="陪诊服务简介")
    avatar: str | None = Field(default=None, max_length=255)


class VolunteerUpdate(BaseModel):
    vol_name: str | None = Field(default=None, max_length=32)
    vol_phone: str | None = Field(default=None, max_length=20)
    service_dept: str | None = Field(default=None, max_length=100)
    service_desc: str | None = Field(default=None, max_length=255)
    status: int | None = Field(default=None, ge=0, le=1, description="1可预约 0不可预约")


class VolunteerResponse(BaseModel):
    id: int
    vol_name: str
    vol_phone: str
    service_dept: str | None
    avatar: str | None
    service_desc: str | None
    service_score: Decimal
    service_count: int
    status: int
