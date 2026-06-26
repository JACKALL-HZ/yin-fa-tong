"""科室模型 —— tb_department"""

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class DepartmentModel(Base, TimestampMixin):
    __tablename__ = "tb_department"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_hospital.id"), comment="所属医院ID")
    dept_name: Mapped[str] = mapped_column(String(50), comment="科室名称")
