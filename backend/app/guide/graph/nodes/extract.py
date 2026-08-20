"""节点[1] 症状抽取：口语/方言 → 结构化症状 + 候选科室

- LLM 可用：结构化抽取（规范化医学表述）
- LLM 不可用/失败：降级词库关键词匹配（SYMPTOM_MAP）
"""
from __future__ import annotations

import logging

from app.guide.graph.state import GuideState
from app.guide.symptom_dict.mapping import SYMPTOM_MAP
from app.shared.llm import llm_client

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM = """你是老年患者症状信息抽取助手。从用户的症状描述中抽取结构化信息。
用户是老年患者，描述常为方言或口语（如"脑壳疼""上不来气""心口堵得慌"），需先理解再规范化为医学表述。

输出严格 JSON，格式如下：
{
  "symptoms": [
    {"entity": "症状主体(规范医学词)", "modifier": "程度或性质修饰", "duration": "持续时间"}
  ],
  "candidate_depts": ["候选科室1", "候选科室2"]
}

候选科室只能从以下列表中选（最多4个）：
心血管内科、神经内科、呼吸内科、消化内科、骨科、内分泌科、眼科、耳鼻喉科、皮肤科、泌尿外科、普外科、口腔科、老年病科、康复医学科、中医科、妇科

只输出 JSON，不要任何其他文字。"""


def _lexicon_extract(text: str) -> dict:
    """词库降级：SYMPTOM_MAP 关键词命中 → 症状列表 + 候选科室"""
    symptoms: list[dict] = []
    depts: list[str] = []
    for entry in SYMPTOM_MAP:
        dept = entry["dept_name"]
        for kw in entry["keywords"]:
            if kw.lower() in text.lower():
                if not any(s["entity"] == kw for s in symptoms):
                    symptoms.append({"entity": kw, "modifier": "", "duration": ""})
                if dept not in depts:
                    depts.append(dept)
                break
    return {"symptoms": symptoms, "candidate_depts": depts[:4]}


async def symptom_extract(state: GuideState) -> dict:
    text = state.get("symptom_text", "")
    if not text:
        return {"symptoms": [], "candidate_depts": [], "extract_engine": "rule"}

    # LLM 路径
    if llm_client.enabled:
        try:
            parsed = await llm_client.chat_json(EXTRACT_SYSTEM, text, temperature=0.1)
            if parsed.get("symptoms") or parsed.get("candidate_depts"):
                logger.info("症状抽取(LLM) symptoms=%d depts=%s",
                            len(parsed.get("symptoms", [])), parsed.get("candidate_depts"))
                return {
                    "symptoms": parsed.get("symptoms", []),
                    "candidate_depts": parsed.get("candidate_depts", []),
                    "extract_engine": "llm",
                }
        except Exception as exc:
            logger.warning("LLM 症状抽取失败，降级词库: %s", exc)

    # 词库降级
    result = _lexicon_extract(text)
    logger.info("症状抽取(词库) symptoms=%d depts=%s",
                len(result["symptoms"]), result["candidate_depts"])
    return {**result, "extract_engine": "lexicon"}
