"""节点[2] 紧急分级：纯规则词库判定（红线：不依赖 LLM，急症判定必须确定性）

red    → 条件边直接跳 assemble（跳过推荐/用药），只给"立即就医/120"处置建议
yellow → 正常流程但响应前置警示
green  → 常规门诊
"""
from __future__ import annotations

import logging

from app.guide.graph.state import GuideState
from app.guide.symptom_dict.emergency_dict import triage_by_rule

logger = logging.getLogger(__name__)


async def triage(state: GuideState) -> dict:
    text = state.get("symptom_text", "")
    # 症状抽取结果拼接（LLM 规范化后的表述也参与匹配，提高召回）
    symptom_parts = []
    for s in state.get("symptoms", []):
        part = s.get("entity", "")
        if s.get("modifier"):
            part += s.get("modifier", "")
        if part:
            symptom_parts.append(part)
    full_text = f"{text} {' '.join(symptom_parts)}"

    level, message = triage_by_rule(full_text)
    logger.info("紧急分级 level=%s", level)
    return {"emergency_level": level, "emergency_message": message}
