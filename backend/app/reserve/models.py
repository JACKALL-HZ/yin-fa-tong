"""挂号预约模型 —— tb_reserve"""

from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class ReserveModel(Base, TimestampMixin):
    __tablename__ = "tb_reserve"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"), comment="预约用户")
    schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_schedule.id"), comment="排班ID")
    elder_bind_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("tb_elder_bind.id"), comment="代办长辈ID")
    source_type: Mapped[str] = mapped_column(String(10), default="normal", comment="号源类型：normal普通 / elder老年优先")
    queue_code: Mapped[str | None] = mapped_column(String(20), comment="候诊排队编号")
    queue_status: Mapped[int] = mapped_column(Integer, default=1, comment="候诊状态：1等待中 2就诊中 3已完成")
    pay_status: Mapped[int] = mapped_column(Integer, default=1, comment="1待支付 2已支付 3超时取消")
    order_status: Mapped[int] = mapped_column(Integer, default=1, comment="订单状态：1待支付 2已预约 3已就诊 4已取消")
