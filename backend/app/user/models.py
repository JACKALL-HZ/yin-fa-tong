"""用户中心模型 —— tb_elder_bind"""

from datetime import date
from sqlalchemy import BigInteger, String, Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class ElderBindModel(Base, TimestampMixin):
    __tablename__ = "tb_elder_bind"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    child_uid: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"), comment="子女用户ID")
    elder_name: Mapped[str] = mapped_column(String(32), comment="长辈姓名")
    elder_id_card: Mapped[str | None] = mapped_column(String(20), comment="长辈身份证号")
    elder_phone: Mapped[str | None] = mapped_column(String(20), comment="长辈联系电话")
    gender: Mapped[int] = mapped_column(Integer, default=1, comment="1男 2女")
    birthday: Mapped[date | None] = mapped_column(Date, comment="长辈出生日期，用于自动核算年龄")
    medical_card: Mapped[str | None] = mapped_column(String(50), comment="医保卡编号")
