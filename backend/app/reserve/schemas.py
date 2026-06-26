"""挂号预约 Pydantic 模型"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ReserveCreateRequest(BaseModel):
    schedule_id: int = Field(description="排班ID")
    elder_bind_id: int | None = Field(default=None, description="代办长辈ID（子女代办时传入）")
    source_type: str = Field(default="normal", description="号源类型：normal普通 / elder老年优先")


class ReserveResponse(BaseModel):
    id: int
    user_id: int
    schedule_id: int
    elder_bind_id: int | None
    queue_code: str | None
    queue_status: int
    pay_status: int
    order_status: int
    # 关联信息
    hospital_name: str | None = None
    dept_name: str | None = None
    doctor_name: str | None = None
    work_date: date | None = None
    time_period: str | None = None
    time_period_text: str | None = None  # "上午"/"下午"/"全天"
    register_fee: Decimal | None = None
    elder_name: str | None = None
    pay_deadline: datetime | None = Field(default=None, description="支付截止时间（待支付状态才有）")


class PayRequest(BaseModel):
    reserve_id: int = Field(description="预约订单ID")
    pay_money: Decimal = Field(description="缴费金额")
