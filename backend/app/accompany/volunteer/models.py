"""志愿者模型 —— tb_volunteer"""

from decimal import Decimal
from sqlalchemy import BigInteger, String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class VolunteerModel(Base, TimestampMixin):
    __tablename__ = "tb_volunteer"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="志愿者主键")
    vol_name: Mapped[str] = mapped_column(String(32), comment="志愿者姓名")
    vol_phone: Mapped[str] = mapped_column(String(20), comment="联系电话")
    service_dept: Mapped[str | None] = mapped_column(String(100), comment="可服务科室")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="志愿者头像地址")
    service_desc: Mapped[str | None] = mapped_column(String(255), comment="陪诊服务简介、从业经验")
    service_score: Mapped[Decimal] = mapped_column(Numeric(2, 1), default=5.0, comment="综合服务评分1-5分")
    service_count: Mapped[int] = mapped_column(Integer, default=0, comment="累计完成陪诊次数")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="1可预约 0不可预约")
