"""排班号源 Pydantic 模型"""

from datetime import date
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    doctor_id: int = Field(description="医生ID")
    work_date: date = Field(description="出诊日期")
    time_period: str = Field(default="AM", description="AM上午 PM下午 ALL全天")
    normal_num: int = Field(default=0, ge=0, description="普通号数量")
    elder_priority_num: int = Field(default=0, ge=0, description="老年优先号数量")


class ScheduleUpdate(BaseModel):
    normal_num: int | None = Field(default=None, ge=0)
    elder_priority_num: int | None = Field(default=None, ge=0)


class ScheduleResponse(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str | None = None
    register_fee: float | None = None    # 医生挂号费
    dept_name: str | None = None
    hospital_name: str | None = None
    work_date: date
    time_period: str
    normal_num: int
    elder_priority_num: int
    normal_remain: int | None = None     # Redis 实时剩余普通号
    elder_remain: int | None = None      # Redis 实时剩余老年号
