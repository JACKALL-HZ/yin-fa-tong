"""健康提醒 Pydantic 模型"""

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    remind_type: str = Field(description="提醒类型：medicine用药 / revisit复诊 / checkup体检")
    remind_time: str = Field(description="提醒时间（HH:MM 格式）")
    remind_content: str = Field(min_length=1, max_length=255, description="提醒内容")
    elder_bind_id: int | None = Field(default=None, description="长辈ID（为空则提醒本人）")
    repeat_days: int = Field(default=0, ge=0, description="重复间隔天数（0=不重复）")


class ReminderResponse(BaseModel):
    id: int
    user_id: int
    remind_type: str
    remind_time: str
    remind_content: str
    elder_bind_id: int | None
    repeat_days: int
    is_active: int


class ReminderToggle(BaseModel):
    is_active: int = Field(ge=0, le=1, description="1启用 0停用")
