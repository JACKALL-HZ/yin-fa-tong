"""消息通知模型 —— tb_message"""

from sqlalchemy import BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class MessageModel(Base, TimestampMixin):
    __tablename__ = "tb_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="消息主键")
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tb_user.id"), comment="接收用户ID")
    msg_type: Mapped[int] = mapped_column(Integer, default=1, comment="1系统通知 2挂号通知 3候诊通知 4健康提醒 5陪诊通知")
    msg_content: Mapped[str] = mapped_column(String(255), comment="消息内容")
    read_status: Mapped[int] = mapped_column(Integer, default=0, comment="0未读 1已读")
