"""BGE-M3 本地 embedding 冒烟测试

验证：
1. FlagEmbedding 已安装
2. 模型可加载（首次会下载，约 2GB）
3. 向量维度正确（1024）
4. 语义相似度合理（"头疼" vs "头痛" 应高于 "头疼" vs "肚子饿"）
"""
import asyncio
import sys


async def main():
    print("── 1. 检查 FlagEmbedding 安装 ──")
    from app.shared.embedding import bge_embedder
    if not bge_embedder.available:
        print("✗ FlagEmbedding 未安装，请 pip install FlagEmbedding")
        sys.exit(1)
    print("✓ FlagEmbedding 已安装")

    print("\n── 2. 加载模型 + 编码测试（首次会下载模型，请耐心等待）──")
    texts = ["头疼头晕", "头痛", "肚子饿了", "高血压用药"]
    vecs = await bge_embedder.embed(texts)
    print(f"✓ 编码完成：{len(vecs)} 条向量，维度={len(vecs[0])}")
    assert len(vecs) == 4
    assert len(vecs[0]) == 1024, f"期望 1024 维，实际 {len(vecs[0])}"

    print("\n── 3. 语义相似度验证 ──")
    # cosine similarity
    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb) if na and nb else 0.0

    sim_headache = cosine(vecs[0], vecs[1])  # 头疼 vs 头痛
    sim_unrelated = cosine(vecs[0], vecs[2])  # 头疼 vs 肚子饿
    print(f"  '头疼头晕' vs '头痛'    = {sim_headache:.4f}")
    print(f"  '头疼头晕' vs '肚子饿了' = {sim_unrelated:.4f}")
    assert sim_headache > sim_unrelated, "近义句相似度应高于无关句"
    print("✓ 语义相似度合理（近义 > 无关）")

    print("\n── 4. 单条 embed_one 测试 ──")
    v = await bge_embedder.embed_one("测试")
    assert len(v) == 1024
    print("✓ embed_one 正常")

    print("\n=== BGE-M3 本地 embedding 冒烟全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
