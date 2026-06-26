"""陪诊订单模型 —— tb_accompany_order"""

from datetime import date
from sqlalchemy import BigInteger, String, Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class AccompanyOrderModel(Base, TimestampMixin):
    __tablename__ = "tb_accompany_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="陪诊订单主键")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"), comment="下单子女用户ID")
    elder_bind_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tb_elder_bind.id"), nullable=True, default=None, comment="陪同长辈ID，老人本人下单时可为空")
    volunteer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_volunteer.id"), comment="用户自主选定志愿者ID")
    accompany_date: Mapped[date] = mapped_column(Date, comment="陪诊日期")
    order_status: Mapped[int] = mapped_column(Integer, default=1, comment="1待审核 2待服务 3服务中 4已完成 5已取消")
    service_score: Mapped[int | None] = mapped_column(Integer, comment="用户评价打分1-5分")
    service_comment: Mapped[str | None] = mapped_column(String(200), comment="陪诊文字评价")
