"""节点[3] 知识库检索：混合检索（稀疏 BM25 + 稠密向量 → RRF 融合 → LLM 重排）

- 向量库可用且已入库：symptom_text → hybrid_search → Top-K
- 不可用/未入库/检索失败：kb_context=[]，recommend 节点自动降级词库推荐
"""
from __future__ import annotations

import logging

from app.config import settings
from app.guide.graph.state import GuideState
from app.shared.vector_store import vector_store

logger = logging.getLogger(__name__)


async def retrieve(state: GuideState) -> dict:
    query = state.get("symptom_text", "")
    if not query:
        return {"kb_context": []}

    if not (vector_store.enabled and vector_store.is_ingested):
        logger.warning("向量库不可用或未入库，知识库检索跳过（recommend 将降级）")
        return {"kb_context": []}

    try:
        hits = await vector_store.hybrid_search(query, top_k=settings.KB_TOP_K)
        logger.info("知识库检索命中=%d", len(hits))
        return {"kb_context": hits}
    except Exception as exc:
        logger.warning("知识库检索失败（recommend 将降级）: %s", exc)
        return {"kb_context": []}
