"""健康提醒模型 —— tb_health_reminder（辅助表）"""

from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class ReminderModel(Base, TimestampMixin):
    __tablename__ = "tb_health_reminder"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"), comment="用户ID")
    remind_type: Mapped[str] = mapped_column(String(20), comment="medicine/revisit/checkup")
    remind_time: Mapped[str] = mapped_column(String(5), comment="HH:MM")
    remind_content: Mapped[str] = mapped_column(String(255), comment="提醒内容")
    elder_bind_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tb_elder_bind.id"), nullable=True, comment="长辈ID")
    repeat_days: Mapped[int] = mapped_column(Integer, default=0, comment="重复间隔天数 0=不重复")
    is_active: Mapped[int] = mapped_column(Integer, default=1, comment="1启用 0停用")
