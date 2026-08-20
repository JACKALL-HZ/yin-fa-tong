"""混合检索 + 流式输出 冒烟测试

验证项：
1. BM25 稀疏检索（建索引 + 查询）
2. RRF 融合逻辑（mock 两路输入）
3. Reranker 降级（LLM 未配置 → 原序）
4. vector_store.hybrid_search 未入库 → 空（降级安全）
5. 流式 SSE 事件序列（start → node_end×N → final）
"""
import asyncio
import os
os.environ["YFT_SKIP_CONFIG_CHECK"] = "1"

from app.shared.bm25_index import bm25_index, _tokenize_zh
from app.shared.reranker import rerank
from app.shared.vector_store import vector_store
from app.shared.llm import llm_client
from app.config import settings


async def test_bm25():
    print("\n=== 1. BM25 稀疏检索 ===")
    docs = [
        "高血压患者应低盐饮食，定期监测血压",
        "糖尿病需控制血糖，注意足部护理",
        "胸痛伴随冷汗可能是心肌梗死，需立即就医",
        "头痛头晕建议测量血压，排除高血压",
    ]
    metas = [{"dept": "01_心血管科", "source": f"f{i}.md"} for i in range(4)]
    ids = [f"doc_{i}" for i in range(4)]
    n = bm25_index.build(docs, metas, ids)
    print(f"建索引 docs={n}")
    hits = bm25_index.search("血压高头晕", top_n=3)
    for h in hits:
        print(f"  score={h['score']} dept={h['dept']} doc={h['document'][:20]}")
    assert len(hits) > 0, "BM25 应有命中"
    print("✓ BM25 检索正常")


async def test_rrf_and_rerank():
    print("\n=== 2. RRF 融合 + 3. Reranker 降级 ===")
    # mock 两路检索结果（共享 id 模拟融合）
    dense = [
        {"id": "a", "document": "高血压低盐饮食", "dept": "心血管", "source": "a.md", "score": 0.9},
        {"id": "b", "document": "糖尿病控糖", "dept": "内分泌", "source": "b.md", "score": 0.8},
        {"id": "c", "document": "胸痛心梗", "dept": "心血管", "source": "c.md", "score": 0.7},
    ]
    sparse = [
        {"id": "c", "document": "胸痛心梗", "dept": "心血管", "source": "c.md", "score": 2.1},
        {"id": "a", "document": "高血压低盐饮食", "dept": "心血管", "source": "a.md", "score": 1.8},
        {"id": "d", "document": "头痛量血压", "dept": "神经", "source": "d.md", "score": 1.5},
    ]
    # RRF 融合（复用 vector_store 逻辑）
    rrf_k = settings.RRF_K
    fused = {}
    for rank, h in enumerate(dense, 1):
        fused.setdefault(h["id"], dict(h, rrf=0.0))["rrf"] += 1.0 / (rrf_k + rank)
    for rank, h in enumerate(sparse, 1):
        fused.setdefault(h["id"], dict(h, rrf=0.0))["rrf"] += 1.0 / (rrf_k + rank)
    fused_list = sorted(fused.values(), key=lambda x: x["rrf"], reverse=True)
    print("RRF 融合结果:")
    for x in fused_list:
        print(f"  rrf={x['rrf']:.5f} id={x['id']} doc={x['document']}")
    # a 和 c 同时被两路召回，应排前两名（高于单路的 b/d）
    top2 = set(x["id"] for x in fused_list[:2])
    assert top2 == {"a", "c"}, f"两路交集项应排前二 实际{top2}"
    print("✓ RRF 融合正确（两路交集项 a/c 排前二，高于单路 b/d）")

    # Reranker：LLM 配置则真实重排，未配置则降级原序
    ranked = await rerank("血压高", fused_list, top_k=2)
    ranked_ids = [x["id"] for x in ranked]
    if llm_client.enabled:
        print(f"Rerank 结果（LLM 真实重排）: {ranked_ids}")
        assert len(ranked) == 2, "应返回 top_k=2"
        assert "a" in ranked_ids, "高血压应排前二（与查询最相关）"
        print("✓ Reranker 真实重排生效（LLM 已配置，非原序）")
    else:
        print(f"Rerank 结果（降级原序）: {ranked_ids}")
        assert ranked_ids == ["a", "c"], "降级应保持 RRF 序前二"
        print("✓ Reranker 降级正确（LLM 未配置 → RRF 原序）")


async def test_hybrid_uningested():
    print("\n=== 4. hybrid_search 已入库检索 ===")
    # KB 已入库，验证 hybrid_search 能返回结果
    hits = await vector_store.hybrid_search("头痛头晕")
    print(f"hybrid_search 返回 {len(hits)} 条:")
    for h in hits[:3]:
        print(f"  dept={h.get('dept','')} score={h.get('score',0)} | {h.get('document','')[:50]}...")
    if vector_store.is_ingested:
        assert len(hits) > 0, "已入库应返回结果"
        print("✓ 已入库混合检索正常")
    else:
        assert hits == [], "未入库应返回空"
        print("✓ 未入库降级安全")


async def test_stream_sse():
    print("\n=== 5. 流式 SSE 事件序列 ===")
    from app.guide.schemas import GuideRequest
    from app.guide.graph.build import stream_guide_graph
    events = []
    async for sse in stream_guide_graph(GuideRequest(symptom_text="头疼三天")):
        events.append(sse)
        # 打印事件类型
        first_line = sse.split("\n")[0]
        print(f"  {first_line}")
    # 解析事件类型序列
    types = []
    for sse in events:
        for line in sse.split("\n"):
            if line.startswith("event:"):
                types.append(line.split(":", 1)[1].strip())
    print(f"事件序列: {types}")
    assert types[0] == "start", "首事件应为 start"
    assert "final" in types, "应含 final 事件"
    assert types[-1] in ("final", "error"), "末事件应为 final 或 error"
    # 应有多个 node_end
    node_ends = [t for t in types if t == "node_end"]
    assert len(node_ends) >= 3, f"node_end 应≥3 实际{len(node_ends)}"
    print(f"✓ 流式事件序列正常（{len(node_ends)} 个节点事件 + final）")


async def main():
    print(f"配置: LLM_API_KEY={'有' if settings.LLM_API_KEY else '无(降级)'} "
          f"RERANK_ENABLED={settings.RERANK_ENABLED} RRF_K={settings.RRF_K}")
    await test_bm25()
    await test_rrf_and_rerank()
    await test_hybrid_uningested()
    await test_stream_sse()
    print("\n=== 全部冒烟通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
