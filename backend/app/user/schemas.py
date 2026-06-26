"""用户中心 Pydantic 模型"""

from datetime import date
from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    """用户个人信息完善"""
    real_name: str = Field(min_length=1, max_length=32, description="真实姓名")
    gender: int = Field(ge=1, le=2, description="1男 2女")
    id_card: str = Field(min_length=18, max_length=18, description="身份证号")
    birthday: date | None = Field(default=None, description="出生日期")
    phone: str | None = Field(default=None, max_length=20, description="联系电话")


class ProfileResponse(BaseModel):
    id: int
    username: str | None
    nickname: str
    user_type: int
    real_name: str | None
    gender: int | None
    id_card: str | None
    birthday: date | None
    phone: str | None
    profile_complete: bool


class ElderBindCreate(BaseModel):
    elder_name: str = Field(min_length=1, max_length=32, description="长辈姓名")
    elder_id_card: str | None = Field(default=None, max_length=20, description="长辈身份证号")
    elder_phone: str | None = Field(default=None, max_length=20, description="长辈联系电话")
    gender: int = Field(default=1, ge=1, le=2, description="1男 2女")
    birthday: date | None = Field(default=None, description="长辈出生日期")
    medical_card: str | None = Field(default=None, max_length=50, description="医保卡编号")


class ElderBindUpdate(BaseModel):
    elder_name: str | None = Field(default=None, max_length=32)
    elder_id_card: str | None = Field(default=None, max_length=20)
    elder_phone: str | None = Field(default=None, max_length=20)
    gender: int | None = Field(default=None, ge=1, le=2)
    birthday: date | None = None
    medical_card: str | None = Field(default=None, max_length=50)


class ElderBindResponse(BaseModel):
    id: int
    child_uid: int
    elder_name: str
    elder_id_card: str | None
    elder_phone: str | None
    gender: int
    birthday: date | None
    age: int | None  # 自动计算的年龄
    medical_card: str | None
    is_elder: bool  # 是否 ≥60 岁（可优先挂老年号）


class TodoItem(BaseModel):
    icon: str = Field(description="图标 emoji")
    text: str = Field(description="任务描述")
    time: str = Field(description="时间描述")
    urgent: bool = Field(default=False, description="是否紧急")


class AlertItem(BaseModel):
    icon: str = Field(description="图标 emoji")
    title: str = Field(description="提醒标题")
    desc: str = Field(description="提醒描述")
    time: str = Field(description="时间描述")


class HealthReminderItem(BaseModel):
    icon: str = Field(description="图标 emoji")
    title: str = Field(description="提醒标题")
    desc: str = Field(description="提醒内容")
    action: str = Field(description="操作按钮文字", default="查看")


class ElderReminderResponse(BaseModel):
    todos: list[TodoItem] = Field(default_factory=list, description="代办任务列表")
    alerts: list[AlertItem] = Field(default_factory=list, description="智能提醒列表")
    health_reminders: list[HealthReminderItem] = Field(default_factory=list, description="健康提醒列表（用药/复诊/体检）")
