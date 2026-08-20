"""BM25 稀疏检索封装（rank_bm25）

与 Chroma 稠密检索互补，供 vector_store.hybrid_search 调用做混合检索。

设计要点：
- 内存级 BM25Okapi，零外部依赖（无 ES）。
- 中文分词用字符 n-gram（2~5 字滑动窗口 + 整串），不依赖 jieba。
- build() 与 vector_store.ingest_kb() 同步：入库的同一批 chunk 同时建 BM25 索引，
  保证稀疏/稠密两路面对的是完全相同的文档集。
- 失败/未建索引时返回空列表，调用方降级到纯稠密。
"""
from __future__ import annotations

import logging
from typing import Any

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def _tokenize_zh(text: str) -> list[str]:
    """中文 n-gram 分词：2~5 字滑动窗口 + 整串去空白"""
    cleaned = (text or "").strip().lower()
    if not cleaned:
        return []
    tokens: list[str] = []
    n = len(cleaned)
    for win in range(2, 6):
        for i in range(n - win + 1):
            tokens.append(cleaned[i:i + win])
    tokens.append(cleaned)
    return tokens


class BM25Index:
    """内存级 BM25 索引（单例，与 VectorStore 生命周期同步）"""

    _instance: "BM25Index | None" = None

    def __new__(cls) -> "BM25Index":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self) -> None:
        self._bm: BM25Okapi | None = None
        self._docs: list[str] = []
        self._metas: list[dict[str, Any]] = []
        self._ids: list[str] = []
        self._tokenized_corpus: list[list[str]] = []

    @property
    def is_built(self) -> bool:
        return self._bm is not None and len(self._docs) > 0

    def build(
        self,
        docs: list[str],
        metas: list[dict[str, Any]],
        ids: list[str],
    ) -> int:
        """建索引。docs/metas/ids 同序等长。返回文档数"""
        self._reset()
        self._docs = list(docs)
        self._metas = list(metas)
        self._ids = list(ids)
        self._tokenized_corpus = [_tokenize_zh(d) for d in docs]
        if not self._tokenized_corpus:
            logger.warning("BM25 建索引：语料为空")
            return 0
        self._bm = BM25Okapi(self._tokenized_corpus)
        logger.info("BM25 索引就绪 docs=%d", len(docs))
        return len(docs)

    def search(
        self,
        query: str,
        top_n: int,
        dept_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """稀疏检索 Top-N。返回 [{id, document, dept, source, score}]"""
        if not self.is_built:
            return []
        q_tokens = _tokenize_zh(query)
        if not q_tokens:
            return []
        scores = self._bm.get_scores(q_tokens)

        scored: list[tuple[int, float]] = []
        for i, s in enumerate(scores):
            if dept_filter and self._metas[i].get("dept") != dept_filter:
                continue
            scored.append((i, float(s)))
        # 按分降序取 Top-N
        scored.sort(key=lambda x: x[1], reverse=True)
        out: list[dict[str, Any]] = []
        for i, s in scored[:top_n]:
            out.append({
                "id": self._ids[i],
                "document": self._docs[i],
                "dept": self._metas[i].get("dept", ""),
                "source": self._metas[i].get("source", ""),
                "score": round(s, 4),
            })
        return out


bm25_index = BM25Index()
