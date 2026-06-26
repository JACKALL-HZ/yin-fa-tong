"""排班号源模型 —— tb_schedule"""

from datetime import date
from sqlalchemy import BigInteger, String, Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class ScheduleModel(Base, TimestampMixin):
    __tablename__ = "tb_schedule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_doctor.id"), comment="医生ID")
    work_date: Mapped[date] = mapped_column(Date, comment="出诊日期")
    time_period: Mapped[str] = mapped_column(String(10), default="AM", comment="AM上午 PM下午 ALL全天")
    normal_num: Mapped[int] = mapped_column(Integer, default=0, comment="普通号数量")
    elder_priority_num: Mapped[int] = mapped_column(Integer, default=0, comment="老年优先号")
