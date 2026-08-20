"""LLM-as-Reranker：用 LLM 对混合检索召回的候选片段做相关性重排

延续"embedding 走 provider"路线，零本地模型依赖。
- 输入：query + 候选片段列表（带编号）
- LLM 按与 query 的相关性从高到低输出编号序列
- 降级：LLM 未配置/调用失败/解析失败 → 原序返回（即 RRF 序），不阻塞检索
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings
from app.shared.llm import llm_client

logger = logging.getLogger(__name__)

RERANK_SYSTEM = """你是医学文献相关性重排器。根据用户症状描述，对给定的候选医学知识片段按相关性从高到低排序。

候选片段已编号。只输出 JSON，格式：
{"ranked": [编号1, 编号2, ...]}
- 编号是片段前的 [n] 标记
- 全部编号都要出现，不遗漏不重复
- 最相关的排在最前
只输出 JSON，不要任何解释。"""


async def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """对 candidates 重排，返回 top_k 条（降级时按原序）"""
    if not candidates:
        return []
    top_k = top_k or settings.RERANK_TOP_K

    # 仅 1 条无需重排
    if len(candidates) == 1:
        return candidates[:top_k]

    # LLM 未配置 → 直接原序截断
    if not (settings.RERANK_ENABLED and llm_client.enabled):
        return candidates[:top_k]

    try:
        # 构造候选摘要（编号 + 截断文本）
        lines: list[str] = []
        for i, c in enumerate(candidates, 1):
            doc = (c.get("document") or "")[:200].replace("\n", " ")
            dept = c.get("dept", "")
            lines.append(f"[{i}] 科室:{dept} 内容:{doc}")
        user_msg = f"症状描述：{query}\n\n候选片段：\n" + "\n".join(lines)

        parsed = await llm_client.chat_json(RERANK_SYSTEM, user_msg, temperature=0.0)
        ranked_ids: list[int] = []
        raw = parsed.get("ranked", [])
        if isinstance(raw, list):
            for x in raw:
                try:
                    n = int(x)
                    if 1 <= n <= len(candidates):
                        ranked_ids.append(n)
                except (TypeError, ValueError):
                    continue

        if len(ranked_ids) != len(candidates):
            logger.warning("重排编号数(%d)!=候选数(%d)，降级原序", len(ranked_ids), len(candidates))
            return candidates[:top_k]

        reordered = [candidates[n - 1] for n in ranked_ids]
        logger.info("LLM 重排完成 in=%d out=%d", len(candidates), min(len(reordered), top_k))
        return reordered[:top_k]
    except Exception as exc:
        logger.warning("LLM 重排失败，降级原序: %s", exc)
        return candidates[:top_k]
