"""医院模型 —— tb_hospital"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class HospitalModel(Base, TimestampMixin):
    __tablename__ = "tb_hospital"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="医院主键")
    hospital_name: Mapped[str] = mapped_column(String(50), comment="医院名称")
    hospital_level: Mapped[str | None] = mapped_column(String(20), comment="医院等级")
    address: Mapped[str | None] = mapped_column(String(200), comment="医院地址")
