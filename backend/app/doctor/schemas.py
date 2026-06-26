"""医生模块 Pydantic 模型"""

from decimal import Decimal
from pydantic import BaseModel, Field


class DoctorCreate(BaseModel):
    dept_id: int = Field(description="所属科室ID")
    doctor_name: str = Field(min_length=1, max_length=32, description="医生姓名")
    doctor_title: str | None = Field(default=None, max_length=20, description="职称")
    specialty: str | None = Field(default=None, max_length=200, description="擅长")
    register_fee: Decimal = Field(default=Decimal("0"), description="挂号费")


class DoctorUpdate(BaseModel):
    doctor_name: str | None = Field(default=None, max_length=32)
    doctor_title: str | None = Field(default=None, max_length=20)
    specialty: str | None = Field(default=None, max_length=200)
    register_fee: Decimal | None = None


class DoctorResponse(BaseModel):
    id: int
    dept_id: int
    dept_name: str | None = None  # 联表查询时填充
    hospital_id: int | None = None
    hospital_name: str | None = None
    doctor_name: str
    doctor_title: str | None
    specialty: str | None
    register_fee: Decimal
    doctor_avatar: str | None
