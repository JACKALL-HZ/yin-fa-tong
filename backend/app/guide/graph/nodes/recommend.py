"""节点[4] 科室推荐：LLM 结合知识库上下文推荐 Top3 科室

- LLM 可用：症状 + 知识库 chunk → 推荐（含置信度+理由）
- LLM 不可用/失败：降级词库打分（SYMPTOM_MAP 加权）
"""
from __future__ import annotations

import logging
from collections import defaultdict

from app.guide.graph.state import GuideState
from app.guide.symptom_dict.mapping import SYMPTOM_MAP
from app.shared.llm import llm_client

logger = logging.getLogger(__name__)

RECOMMEND_SYSTEM = """你是老年医学科室导诊助手。根据患者症状信息和知识库参考资料，推荐最合适的 2-3 个就诊科室。

要求：
1. 优先依据知识库参考资料判断，资料不足时结合症状推理
2. confidence 取 0.0-1.0，主推科室 ≥0.7
3. reasoning 用通俗易懂的语言（老年患者能听懂），一句话说明为什么推荐
4. general_advice 给一段综合就医建议（含就诊前准备提示）

输出严格 JSON，格式如下：
{
  "departments": [
    {"dept_name": "科室名", "confidence": 0.85, "reasoning": "推荐理由"}
  ],
  "general_advice": "综合就医建议"
}

科室名从以下列表中选：
心血管内科、神经内科、呼吸内科、消化内科、骨科、内分泌科、眼科、耳鼻喉科、皮肤科、泌尿外科、普外科、口腔科、老年病科、康复医学科、中医科、妇科、急诊科

只输出 JSON，不要任何其他文字。"""


def _lexicon_recommend(text: str) -> list[dict]:
    """词库降级：SYMPTOM_MAP 加权打分取 Top3"""
    scores: dict[str, tuple[int, set]] = defaultdict(lambda: (0, set()))
    for entry in SYMPTOM_MAP:
        dept, weight = entry["dept_name"], entry["weight"]
        for kw in entry["keywords"]:
            if kw.lower() in text.lower():
                score, matched = scores[dept]
                scores[dept] = (score + weight, matched | {kw})
                break
    ranked = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)[:3]
    total = sum(s for _, (s, _) in ranked) or 1
    return [
        {
            "dept_name": dept,
            "confidence": round(score / total, 2),
            "reasoning": f"根据症状关键词（{'、'.join(list(matched)[:3])}）匹配",
        }
        for dept, (score, matched) in ranked
    ]


async def recommend(state: GuideState) -> dict:
    text = state.get("symptom_text", "")

    if llm_client.enabled:
        try:
            # 拼装 user 消息：症状 + 抽取结果 + 知识库上下文
            lines = [f"患者症状描述：{text}"]
            symptoms = state.get("symptoms", [])
            if symptoms:
                s_desc = "；".join(
                    f"{s.get('entity', '')}（{s.get('modifier', '')} {s.get('duration', '')}）".strip("（） ")
                    for s in symptoms if s.get("entity")
                )
                if s_desc:
                    lines.append(f"结构化症状：{s_desc}")
            depts = state.get("candidate_depts", [])
            if depts:
                lines.append(f"预筛候选科室：{'、'.join(depts)}")
            kb = state.get("kb_context", [])
            if kb:
                ctx = "\n---\n".join(
                    f"[{h.get('source', '')}] {h.get('document', '')[:400]}" for h in kb[:6]
                )
                lines.append(f"知识库参考资料：\n{ctx}")

            parsed = await llm_client.chat_json(RECOMMEND_SYSTEM, "\n".join(lines), temperature=0.2)
            departments = parsed.get("departments", [])
            if departments:
                advice = parsed.get("general_advice", "")
                logger.info("科室推荐(LLM) top=%s", departments[0].get("dept_name"))
                return {"departments": departments[:3], "general_advice": advice}
        except Exception as exc:
            logger.warning("LLM 科室推荐失败，降级词库: %s", exc)

    # 词库降级
    departments = _lexicon_recommend(text)
    logger.info("科室推荐(词库) count=%d", len(departments))
    return {"departments": departments, "general_advice": ""}
