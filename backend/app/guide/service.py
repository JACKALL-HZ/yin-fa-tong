"""智能导诊业务逻辑

诊断策略:
  PRIMARY:  调用 Dify Chatbot（通义千问 + 医学知识库）→ 解析 JSON → 返回科室+用药建议
  FALLBACK: 当 Dify 不可用/未配置/超时/出错时，退化到本地规则引擎关键词匹配
"""

import json
import re
import logging
from collections import defaultdict
from app.guide.symptom_dict.mapping import SYMPTOM_MAP
from app.guide.schemas import (
    GuideRequest, GuideResponse, MatchResult, MedicationSuggestion,
)
from app.shared.dify_client import dify_client

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  FALLBACK: 本地规则引擎（保持不变，Dify 不可用时的兜底方案）
# ═══════════════════════════════════════════════════════════════

def _tokenize(text: str) -> list[str]:
    """简易分词：滑动窗口提取 2~5 字片段"""
    cleaned = text.strip().lower()
    if not cleaned:
        return []
    tokens = []
    n = len(cleaned)
    for win in range(2, 6):
        for i in range(n - win + 1):
            tokens.append(cleaned[i:i + win])
    tokens.append(cleaned)
    return tokens


def _rule_engine_diagnose(req: GuideRequest) -> GuideResponse:
    """本地规则引擎：症状关键词匹配 + 科室推荐"""
    tokens = _tokenize(req.symptom_text)
    dept_scores: dict[str, tuple[int, set]] = defaultdict(lambda: (0, set()))

    for entry in SYMPTOM_MAP:
        dept = entry["dept_name"]
        weight = entry["weight"]
        for kw in entry["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in tokens or kw_lower in req.symptom_text:
                score, matched = dept_scores[dept]
                dept_scores[dept] = (score + weight, matched | {kw})

    # 排序取 Top 3
    ranked = sorted(dept_scores.items(), key=lambda x: x[1][0], reverse=True)
    results = []
    for dept_name, (score, matched) in ranked[:3]:
        results.append(MatchResult(
            dept_name=dept_name,
            total_score=score,
            matched_symptoms=list(matched),
        ))

    # 无匹配时返回默认推荐
    if not results:
        results = [
            MatchResult(dept_name="内科", total_score=1, matched_symptoms=["通用"]),
            MatchResult(dept_name="老年病科", total_score=1, matched_symptoms=["通用"]),
        ]

    # 生成建议
    if results[0].total_score >= 5:
        suggestion = f"根据您的描述，建议优先挂【{results[0].dept_name}】。"
    elif ranked:
        suggestion = "症状不太明确，建议先挂【内科】或【老年病科】做初步检查。"
    else:
        suggestion = "未能匹配到合适的科室，建议到导诊台咨询或挂【内科】就诊。"

    return GuideResponse(
        symptom_text=req.symptom_text,
        results=results,
        suggestion=suggestion,
        engine="rule",
    )


# ═══════════════════════════════════════════════════════════════
#  PRIMARY: Dify Chatbot 诊断
# ═══════════════════════════════════════════════════════════════

def _extract_json_from_text(text: str) -> dict:
    """从 LLM 文本回复中提取 JSON（处理 markdown 代码块包裹的情况）"""
    # 先尝试匹配 ```json ... ``` 代码块
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 再尝试匹配裸花括号
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


async def _dify_diagnose(req: GuideRequest) -> GuideResponse:
    """调用 Dify Chatbot API → 从文本回复中提取 JSON → 映射为响应"""
    answer_text = await dify_client.chat(query=req.symptom_text)
    parsed = _extract_json_from_text(answer_text)

    # ── 科室推荐 ──
    results = []
    for dep in parsed.get("departments", [])[:3]:
        results.append(MatchResult(
            dept_name=dep.get("dept_name", ""),
            confidence=float(dep.get("confidence", 0)),
            reasoning=dep.get("reasoning", ""),
        ))

    # ── 用药建议：note 字段兼容简化格式 ──
    medications = []
    for med in parsed.get("medications", [])[:3]:
        note = med.get("note", "")  # 简化 prompt 只用 note
        medications.append(MedicationSuggestion(
            drug_name=med.get("drug_name", ""),
            indication=med.get("indication", note),       # note → indication
            dosage_note=med.get("dosage_note", ""),
            elderly_precaution=med.get("elderly_precaution", ""),
            contraindication=med.get("contraindication", ""),
        ))

    # ── 建议文本：advice 字段兼容简化格式 ──
    advice = parsed.get("advice", parsed.get("general_advice", ""))
    if results:
        top = results[0]
        suggestion = f"根据AI分析，建议优先挂【{top.dept_name}】（置信度 {top.confidence:.0%}）。{top.reasoning}"
    else:
        suggestion = advice or "AI分析未匹配到明确科室，建议挂【内科】就诊。"

    return GuideResponse(
        symptom_text=req.symptom_text,
        results=results,
        suggestion=suggestion,
        medications=medications,
        general_advice=advice,
        engine="dify",
    )


# ═══════════════════════════════════════════════════════════════
#  主入口：Dify 优先，规则引擎兜底
# ═══════════════════════════════════════════════════════════════

async def guide_diagnose(req: GuideRequest) -> GuideResponse:
    """智能导诊主入口：Dify AI 优先，失败时自动降级为规则引擎"""
    if not dify_client.enabled:
        return _rule_engine_diagnose(req)

    try:
        return await _dify_diagnose(req)
    except Exception as exc:
        logger.warning("Dify 诊断失败，降级为规则引擎。错误: %s", exc)
        return _rule_engine_diagnose(req)
