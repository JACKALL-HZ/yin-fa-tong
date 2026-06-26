"""科室模块 Pydantic 模型"""

from pydantic import BaseModel, Field


class DeptCreate(BaseModel):
    hospital_id: int = Field(description="所属医院ID")
    dept_name: str = Field(min_length=1, max_length=50, description="科室名称")


class DeptUpdate(BaseModel):
    dept_name: str | None = Field(default=None, max_length=50)


class DeptResponse(BaseModel):
    id: int
    hospital_id: int
    dept_name: str


class DeptListResponse(BaseModel):
    """科室列表（含医院名称）"""
    id: int
    hospital_id: int
    hospital_name: str
    dept_name: str
