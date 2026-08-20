"""智能导诊模型 —— tb_guide_runs（可观测：每次导诊运行记录）"""

from sqlalchemy import BigInteger, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base
from app.shared.base import TimestampMixin


class GuideRunModel(Base, TimestampMixin):
    __tablename__ = "tb_guide_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(64), index=True, comment="追踪ID（=thread_id 首轮）")
    thread_id: Mapped[str] = mapped_column(String(64), index=True, comment="LangGraph 续推线程ID")
    symptom_text: Mapped[str] = mapped_column(String(500), comment="症状描述")
    engine: Mapped[str] = mapped_column(String(20), default="langgraph", comment="langgraph/rule")
    emergency_level: Mapped[str] = mapped_column(String(10), default="", comment="red/yellow/green")
    extract_engine: Mapped[str] = mapped_column(String(20), default="", comment="llm/lexicon/rule")
    nodes_path: Mapped[str] = mapped_column(String(255), default="", comment="节点执行路径")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, comment="总耗时毫秒")
    status: Mapped[str] = mapped_column(String(20), default="ok", comment="ok/degraded/error")
    error: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="错误信息")
    nodes_detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="节点级明细JSON")
