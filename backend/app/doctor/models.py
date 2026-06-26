"""医生模型 —— tb_doctor"""

from decimal import Decimal
from sqlalchemy import BigInteger, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class DoctorModel(Base, TimestampMixin):
    __tablename__ = "tb_doctor"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dept_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_department.id"), comment="所属科室ID")
    doctor_name: Mapped[str] = mapped_column(String(32), comment="医生姓名")
    doctor_title: Mapped[str | None] = mapped_column(String(20), comment="医生职称")
    specialty: Mapped[str | None] = mapped_column(String(200), comment="擅长诊疗病症")
    register_fee: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0, comment="单次挂号资费")
    doctor_avatar: Mapped[str | None] = mapped_column(String(255), comment="医生头像存储地址")
