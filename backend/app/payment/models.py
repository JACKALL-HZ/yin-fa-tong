"""缴费记录模型 —— tb_pay_record"""

from decimal import Decimal
from sqlalchemy import BigInteger, Numeric, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class PayRecordModel(Base, TimestampMixin):
    __tablename__ = "tb_pay_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="缴费记录ID")
    reserve_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_reserve.id"), index=True, comment="预约订单ID")
    pay_money: Mapped[Decimal] = mapped_column(Numeric(10, 2), comment="缴费金额")
    # 支付宝沙箱相关字段
    trade_no: Mapped[str] = mapped_column(String(64), default="", comment="支付宝交易号")
    out_trade_no: Mapped[str] = mapped_column(String(64), default="", index=True, comment="商户订单号")
    pay_channel: Mapped[str] = mapped_column(String(20), default="mock", comment="支付渠道：alipay / mock")
    pay_status: Mapped[int] = mapped_column(Integer, default=1, comment="支付状态：1待支付 2已支付 3已关闭")
