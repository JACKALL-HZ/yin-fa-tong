"""医院模块 Pydantic 模型"""

from pydantic import BaseModel, Field


class HospitalCreate(BaseModel):
    hospital_name: str = Field(min_length=1, max_length=50, description="医院名称")
    hospital_level: str | None = Field(default=None, max_length=20, description="医院等级")
    address: str | None = Field(default=None, max_length=200, description="医院地址")


class HospitalUpdate(BaseModel):
    hospital_name: str | None = Field(default=None, max_length=50)
    hospital_level: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=200)


class HospitalResponse(BaseModel):
    id: int
    hospital_name: str
    hospital_level: str | None
    address: str | None
