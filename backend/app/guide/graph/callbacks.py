"""导诊运行记录落库（guide_runs 表，best-effort：失败不影响主链路）"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.shared.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def save_guide_run(
    trace_id: str,
    thread_id: str,
    symptom_text: str,
    engine: str,
    final_state: dict[str, Any],
    nodes: list[str],
    duration_ms: int,
    status: str = "ok",
    error: str = "",
) -> None:
    """把一次导诊运行写入 tb_guide_runs（可观测埋点，任何失败仅告警）"""
    try:
        from app.guide.models import GuideRunModel

        extract_engine = final_state.get("extract_engine", "")
        emergency_level = final_state.get("emergency_level", "")

        # 降级判定：LLM 抽取失败 / 知识库检索为空 / 图报错
        degraded = (
            extract_engine in ("lexicon", "rule")
            or final_state.get("kb_context") == []
            or status == "error"
        )
        run_status = "error" if status == "error" else ("degraded" if degraded else "ok")

        nodes_detail = json.dumps(
            {
                "nodes": nodes,
                "extract_engine": extract_engine,
                "kb_hits": len(final_state.get("kb_context") or []),
                "dept_count": len(final_state.get("departments") or []),
                "med_count": len(final_state.get("medications") or []),
            },
            ensure_ascii=False,
        )

        async with AsyncSessionLocal() as session:
            session.add(GuideRunModel(
                trace_id=trace_id[:64],
                thread_id=thread_id[:64],
                symptom_text=symptom_text[:500],
                engine=engine,
                emergency_level=emergency_level,
                extract_engine=extract_engine,
                nodes_path="→".join(nodes)[:255],
                duration_ms=duration_ms,
                status=run_status,
                error=(error or None),
                nodes_detail=nodes_detail,
            ))
            await session.commit()
    except Exception as exc:
        logger.warning("guide_runs 落库失败（不影响响应）: %s", exc)
