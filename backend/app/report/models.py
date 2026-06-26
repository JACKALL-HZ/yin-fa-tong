"""体检报告模型 —— tb_physical_report"""

from sqlalchemy import BigInteger, String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class PhysicalReportModel(Base, TimestampMixin):
    __tablename__ = "tb_physical_report"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    elder_bind_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_elder_bind.id"), comment="绑定长辈ID")
    report_url: Mapped[str] = mapped_column(String(255), comment="报告图片地址")
    ocr_result: Mapped[str | None] = mapped_column(Text, comment="OCR识别原始结果JSON")
    interpretation: Mapped[str | None] = mapped_column(Text, comment="通俗化解读文本")
