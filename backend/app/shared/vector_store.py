"""Chroma 向量库封装

知识库 md → 分块 → 本地 BGE-M3 向量化 → Chroma 持久化 + 语义检索。

设计要点：
- Embedding 由本地 BGE-M3 模型计算（shared/embedding.py），零联网依赖。
- 手动传给 collection.add/query，不依赖 chromadb 内置 ef。
- 创建 collection 时挂一个占位 ef（__call__ 抛错），仅用于绕开 chromadb 默认 ef 的 import。
- 所有方法 async（BGE-M3 推理走 to_thread 不阻塞，chromadb 本地操作同步但极快）。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import chromadb

from app.config import settings
from app.shared.bm25_index import bm25_index
from app.shared.llm import llm_client
from app.shared.reranker import rerank

logger = logging.getLogger(__name__)


class _NoOpEmbeddingFunction:
    """占位 ef：强制调用方手动传 embeddings/query_embeddings，禁止 chromadb 自动算 embedding。

    挂上它只为绕开 chromadb 默认 ef（sentence-transformers）的 import 依赖。
    若被误触发（未手动传 embeddings），立刻抛错而非静默下载模型。
    """
    def name(self) -> str:
        return "noop"

    @staticmethod
    def signature() -> str:
        return "noop"

    def __call__(self, input: Any) -> list[list[float]]:
        raise RuntimeError("禁止自动 embedding：请手动传 embeddings/query_embeddings 参数")


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按字符长度滑动窗口分块（中文按字数）"""
    if not text:
        return []
    text = text.strip()
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_size])
        i += chunk_size - overlap
    return chunks


def _clean_md(raw: str) -> str:
    """简易清洗 markdown：去图片/链接标记，保留正文文本"""
    out = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", raw)
    out = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", out)
    out = re.sub(r"`{1,3}", "", out)
    return out.strip()


class VectorStore:
    """Chroma 向量库（lazy init 单例）

    - ingest_kb(): 扫描知识库科室目录，md 分块入库（首次/重建用）
    - search(): 语义检索 Top-K
    - is_ingested: 是否已入库
    """

    _instance: "VectorStore | None" = None

    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self) -> None:
        db_path = settings.BASE_DIR / settings.CHROMA_DB_DIR
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            embedding_function=_NoOpEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
        self._ingested = self._collection.count() > 0
        logger.info("Chroma 就绪 collection=%s 已入库=%s", settings.CHROMA_COLLECTION, self._ingested)

    @property
    def enabled(self) -> bool:
        """embedding 后端可用即启用（local: FlagEmbedding 已装 / api: API key 已配）"""
        from app.shared.embedding import get_embedder
        return get_embedder().available

    @property
    def is_ingested(self) -> bool:
        return self._ingested

    async def ingest_kb(self, kb_dir: Path | None = None) -> int:
        """扫描知识库科室目录，md 分块入库。返回入库 chunk 数"""
        kb_dir = kb_dir or (settings.BASE_DIR / settings.KB_DIR)
        if not kb_dir.exists():
            logger.warning("知识库目录不存在: %s", kb_dir)
            return 0

        all_docs, all_metas, all_ids = [], [], []
        idx = 0
        for dept_dir in sorted(kb_dir.iterdir()):
            if not dept_dir.is_dir() or dept_dir.name.startswith((".", "99")):
                # 跳过隐藏目录 + 99_老年用药安全手册（单独处理）
                continue
            dept_name = dept_dir.name
            for md_file in sorted(dept_dir.glob("*.md")):
                if md_file.name.lower() == "readme.md":
                    continue
                raw = md_file.read_text(encoding="utf-8", errors="ignore")
                cleaned = _clean_md(raw)
                chunks = _chunk_text(cleaned, settings.KB_CHUNK_SIZE, settings.KB_CHUNK_OVERLAP)
                for chunk in chunks:
                    all_docs.append(chunk)
                    all_metas.append({
                        "dept": dept_name,
                        "source": md_file.name,
                        "chunk_idx": idx,
                    })
                    all_ids.append(f"{dept_name}/{md_file.stem}/{idx}")
                    idx += 1

        # 99_老年用药安全手册 整库入库（供 medication 节点检索）
        med_dir = kb_dir / "99_老年用药安全手册"
        if med_dir.exists():
            for md_file in sorted(med_dir.glob("*.md")):
                raw = md_file.read_text(encoding="utf-8", errors="ignore")
                cleaned = _clean_md(raw)
                chunks = _chunk_text(cleaned, settings.KB_CHUNK_SIZE, settings.KB_CHUNK_OVERLAP)
                for chunk in chunks:
                    all_docs.append(chunk)
                    all_metas.append({
                        "dept": "99_老年用药安全手册",
                        "source": md_file.name,
                        "chunk_idx": idx,
                    })
                    all_ids.append(f"99_老年用药安全手册/{md_file.stem}/{idx}")
                    idx += 1

        if not all_docs:
            logger.warning("知识库扫描结果为空")
            return 0

        # 分批算 embedding + upsert（本地 BGE-M3 批量推理）
        batch = 64
        for i in range(0, len(all_docs), batch):
            batch_docs = all_docs[i:i + batch]
            batch_ids = all_ids[i:i + batch]
            batch_metas = all_metas[i:i + batch]
            embs = await llm_client.embed(batch_docs)
            self._collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=embs,
                metadatas=batch_metas,
            )
            logger.info("入库批次 %d/%d chunks=%d", i // batch + 1, (len(all_docs) - 1) // batch + 1, len(batch_docs))

        # 同步建 BM25 稀疏索引（与 Chroma 面对完全相同的文档集）
        bm25_index.build(all_docs, all_metas, all_ids)

        self._ingested = True
        logger.info("知识库入库完成 total_chunks=%d", len(all_docs))
        return len(all_docs)

    async def _search_dense(
        self,
        query: str,
        top_n: int,
        dept_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """稠密检索（Chroma 向量）。返回 [{id, document, dept, source, score}]"""
        if not self._ingested:
            return []
        where = {"dept": dept_filter} if dept_filter else None
        q_embs = await llm_client.embed([query])
        results = self._collection.query(query_embeddings=q_embs, n_results=top_n, where=where)

        out: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            # cosine space: distance ∈ [0,2]，similarity = 1 - distance
            score = 1.0 - dist if dist is not None else 0.0
            if score < settings.KB_SCORE_THRESHOLD:
                continue
            out.append({
                "id": cid,
                "document": doc,
                "dept": meta.get("dept", ""),
                "source": meta.get("source", ""),
                "score": round(score, 4),
            })
        return out

    async def hybrid_search(
        self,
        query: str,
        top_k: int | None = None,
        dept_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """混合检索：稀疏(BM25) + 稠密(向量) → RRF 融合 → LLM Reranker 重排

        返回 [{document, dept, source, score}]（重排后 Top-K）
        每层均可独立降级：稠密挂→纯稀疏；稀疏空→纯稠密；rerank 挂→RRF 序。
        """
        if not self._ingested:
            logger.warning("向量库未入库，混合检索跳过")
            return []
        top_k = top_k or settings.KB_TOP_K

        # ── 两路召回（并行） ──
        dense_hits: list[dict[str, Any]] = []
        sparse_hits: list[dict[str, Any]] = []
        try:
            dense_hits = await self._search_dense(query, settings.DENSE_TOP_N, dept_filter)
        except Exception as exc:
            logger.warning("稠密检索失败（混合检索仅用稀疏）: %s", exc)
        try:
            sparse_hits = bm25_index.search(query, settings.BM25_TOP_N, dept_filter)
        except Exception as exc:
            logger.warning("稀疏检索失败（混合检索仅用稠密）: %s", exc)

        logger.info("混合召回 dense=%d sparse=%d", len(dense_hits), len(sparse_hits))

        # ── RRF 融合 ──
        fused: dict[str, dict[str, Any]] = {}
        rrf_k = settings.RRF_K
        for rank, h in enumerate(dense_hits, 1):
            cid = h.get("id") or f"d_{rank}"
            item = fused.setdefault(cid, {
                "id": cid, "document": h.get("document", ""),
                "dept": h.get("dept", ""), "source": h.get("source", ""), "rrf": 0.0,
            })
            item["rrf"] += 1.0 / (rrf_k + rank)
        for rank, h in enumerate(sparse_hits, 1):
            cid = h.get("id") or f"s_{rank}"
            item = fused.setdefault(cid, {
                "id": cid, "document": h.get("document", ""),
                "dept": h.get("dept", ""), "source": h.get("source", ""), "rrf": 0.0,
            })
            item["rrf"] += 1.0 / (rrf_k + rank)

        fused_list = sorted(fused.values(), key=lambda x: x["rrf"], reverse=True)
        # RRF 后取 Top-2K 交 rerank（控制重排成本）
        candidates = fused_list[: max(settings.RERANK_TOP_K * 2, top_k * 2)]

        if not candidates:
            return []

        # ── LLM Reranker 重排（内部降级到 RRF 序） ──
        ranked = await rerank(query, candidates, top_k=top_k)
        # 补回 score 字段（用 rrf 分作为 score 返回）
        for x in ranked:
            x["score"] = round(x.get("rrf", 0.0), 4)
        logger.info("混合检索最终命中=%d", len(ranked))
        return ranked


# 模块级单例
vector_store = VectorStore()
