"""用户认证模型 —— tb_user"""

from datetime import date
from sqlalchemy import BigInteger, String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class UserModel(Base, TimestampMixin):
    __tablename__ = "tb_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    wx_openid: Mapped[str | None] = mapped_column(String(128), unique=True, comment="模拟微信唯一标识")
    alipay_user_id: Mapped[str | None] = mapped_column(String(128), unique=True, comment="支付宝用户唯一标识")
    username: Mapped[str | None] = mapped_column(String(32), unique=True, comment="登录账号")
    password: Mapped[str] = mapped_column(String(64), comment="bcrypt加密登录密码")
    nickname: Mapped[str] = mapped_column(String(64), comment="用户昵称")
    user_type: Mapped[int] = mapped_column(Integer, default=1, comment="1老年用户 2子女用户 3管理员")
    # ── 个人信息 ──
    real_name: Mapped[str | None] = mapped_column(String(32), comment="真实姓名")
    gender: Mapped[int | None] = mapped_column(Integer, comment="1男 2女")
    id_card: Mapped[str | None] = mapped_column(String(20), comment="身份证号")
    birthday: Mapped[date | None] = mapped_column(Date, comment="出生日期")
    phone: Mapped[str | None] = mapped_column(String(20), comment="联系电话")
