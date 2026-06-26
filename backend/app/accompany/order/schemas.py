"""陪诊订单 Pydantic 模型"""

from datetime import date
from pydantic import BaseModel, Field


class AccompanyOrderCreate(BaseModel):
    volunteer_id: int = Field(description="志愿者ID")
    elder_bind_id: int | None = Field(default=None, description="陪同长辈ID，老人本人下单可不传")
    accompany_date: date = Field(description="陪诊日期")


class ReviewCreate(BaseModel):
    service_score: int = Field(ge=1, le=5, description="评分 1-5")
    service_comment: str | None = Field(default=None, max_length=200, description="陪诊文字评价")


class AccompanyOrderResponse(BaseModel):
    id: int
    user_id: int
    elder_bind_id: int | None = None
    elder_name: str | None = None
    volunteer_id: int
    vol_name: str | None = None
    accompany_date: date
    order_status: int
    status_text: str
    service_score: int | None
    service_comment: str | None


STATUS_MAP = {1: "待审核", 2: "待服务", 3: "服务中", 4: "已完成", 5: "已取消"}
