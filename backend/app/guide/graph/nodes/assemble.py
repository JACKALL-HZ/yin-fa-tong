"""节点[6] 组装：收集全部节点输出 → GuideResponse

- red：只给紧急处置建议，不给推荐/用药（合规红线）
- yellow：正常输出 + 前置警示
- green：正常输出
"""
from __future__ import annotations

import logging

from app.guide.graph.state import GuideState
from app.guide.schemas import GuideResponse, MatchResult, MedicationSuggestion

logger = logging.getLogger(__name__)


async def assemble(state: GuideState) -> dict:
    symptom_text = state.get("symptom_text", "")
    level = state.get("emergency_level", "green")
    em_msg = state.get("emergency_message", "")

    # ── 红色急症：紧急优先，不推荐科室不给用药 ──
    if level == "red":
        resp = GuideResponse(
            symptom_text=symptom_text,
            results=[],
            suggestion=f"⚠️ {em_msg}",
            emergency_flag=True,
            engine="langgraph",
            emergency_level="red",
            emergency_message=em_msg,
        )
        logger.info("组装完成(red) 紧急响应")
        return {"response": resp.model_dump(), "engine": "langgraph"}

    # ── 正常流程 ──
    departments = state.get("departments", [])
    results = [
        MatchResult(
            dept_name=d.get("dept_name", ""),
            confidence=float(d.get("confidence", 0) or 0),
            reasoning=d.get("reasoning", ""),
        )
        for d in departments[:3] if d.get("dept_name")
    ]
    if not results:
        results = [MatchResult(dept_name="内科", total_score=1, matched_symptoms=["通用"])]

    medications = [
        MedicationSuggestion(
            drug_name=m.get("drug_name", ""),
            indication=m.get("indication", ""),
            dosage_note=m.get("dosage_note", ""),
            elderly_precaution=m.get("elderly_precaution", ""),
            contraindication=m.get("contraindication", ""),
        )
        for m in state.get("medications", [])[:3]
    ]

    # 综合建议文本
    top = results[0]
    parts = []
    if level == "yellow":
        parts.append(f"⚠️ {em_msg}")
    if top.confidence > 0:
        parts.append(f"根据您的描述，建议优先挂【{top.dept_name}】（置信度 {top.confidence:.0%}）。{top.reasoning}")
    else:
        parts.append(f"根据您的描述，建议优先挂【{top.dept_name}】。")
    advice = state.get("general_advice", "")
    if advice:
        parts.append(advice)
    if medications:
        parts.append("以上用药建议仅供参考，具体用药请遵医嘱或咨询药师。")

    resp = GuideResponse(
        symptom_text=symptom_text,
        results=results,
        suggestion=" ".join(parts),
        medications=medications,
        elderly_precautions=state.get("elderly_precautions", ""),
        emergency_flag=(level == "yellow"),
        general_advice=advice,
        engine="langgraph",
        emergency_level=level,
        emergency_message=em_msg if level == "yellow" else "",
    )
    logger.info("组装完成(%s) top_dept=%s meds=%d", level, top.dept_name, len(medications))
    return {"response": resp.model_dump(), "engine": "langgraph"}
