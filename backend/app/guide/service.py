"""智能导诊业务逻辑

诊断策略（两档分派）:
  PRIMARY:  GUIDE_ENGINE=langgraph → 自建 LangGraph 图（症状抽取→紧急分级→知识库检索→科室推荐→用药建议）
  FALLBACK: GUIDE_ENGINE=rule 或 langgraph 失败 → 本地规则引擎关键词匹配
"""

import logging
from collections import defaultdict

from app.config import settings
from app.guide.symptom_dict.mapping import SYMPTOM_MAP
from app.guide.schemas import (
    GuideRequest, GuideResponse, MatchResult,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  FALLBACK: 本地规则引擎（保持不变，LangGraph 不可用时的兜底方案）
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
#  PRIMARY: LangGraph 自建图导诊
# ═══════════════════════════════════════════════════════════════

async def _langgraph_diagnose(req: GuideRequest) -> GuideResponse:
    """LangGraph 自建图导诊（lazy import，避免模块加载期依赖 graph.build 尚未就绪）"""
    from app.guide.graph.build import run_guide_graph
    return await run_guide_graph(req)


# ═══════════════════════════════════════════════════════════════
#  主入口：按 GUIDE_ENGINE 分派，langgraph 失败自动降级 rule
# ═══════════════════════════════════════════════════════════════

async def guide_diagnose(req: GuideRequest) -> GuideResponse:
    """智能导诊主入口：GUIDE_ENGINE=langgraph 优先，失败降级规则引擎"""
    engine = settings.GUIDE_ENGINE
    if engine == "langgraph":
        try:
            return await _langgraph_diagnose(req)
        except Exception as exc:
            logger.warning("LangGraph 诊断失败，降级规则引擎。错误: %s", exc)
            return _rule_engine_diagnose(req)
    # rule（默认/兜底）
    return _rule_engine_diagnose(req)


# ═══════════════════════════════════════════════════════════════
#  流式入口：SSE 事件生成器（节点级进度 + 最终结果）
# ═══════════════════════════════════════════════════════════════

async def stream_guide_diagnose(req: GuideRequest):
    """流式导诊 SSE 生成器

    langgraph 模式 → start/node_end×N/final 事件流
    图不可用/失败 → 降级 rule，单次 final 事件
    """
    if settings.GUIDE_ENGINE == "langgraph":
        try:
            from app.guide.graph.build import stream_guide_graph  # noqa: E402
            async for evt in stream_guide_graph(req):
                yield evt
            return
        except Exception as exc:
            logger.warning("LangGraph 流式失败，降级规则引擎: %s", exc)
    # 降级：规则引擎单 final 事件
    from app.guide.graph.build import _sse  # noqa: E402
    resp = _rule_engine_diagnose(req)
    yield _sse("final", resp.model_dump())
