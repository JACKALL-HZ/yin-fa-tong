"""SQLAlchemy 模型基类 Mixin —— 统一审计字段"""

from datetime import datetime
from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """全表通用审计字段"""
    create_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", comment="0未删除 1已删除"
    )
