"""BGE-M3 本地 Embedding 封装

模型：BAAI/bge-m3（1024 维稠密向量）
部署：本地 CPU/GPU 推理，零联网依赖（模型下载后），符合"零第三方大模型依赖"红线。

设计要点：
- 单例懒加载：首次 embed() 时才加载模型（~2GB 内存），import 时不占资源
- 模型下载：优先 ModelScope（阿里达摩院，国内直连），降级 HuggingFace
- 线程安全：asyncio.to_thread 包裹同步推理，不阻塞事件循环
- CPU 模式默认：use_fp16=False，有 CUDA 自动用 GPU 加速
- 模型缓存：ModelScope → ~/.cache/modelscope/，HF → ~/.cache/huggingface/
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def _download_model() -> str:
    """下载 BGE-M3 模型到本地，返回本地路径

    优先 ModelScope（国内直连快），降级 HuggingFace（需代理/镜像）。
    已下载则直接返回缓存路径。
    缓存目录由 MODELSCOPE_CACHE 配置控制（默认 E:/modelscope_cache，避免 C 盘爆满）。
    """
    model_id = "BAAI/bge-m3"

    # 从配置读取缓存目录（必须在 import modelscope 前设置 env）
    from app.config import settings
    cache_dir = settings.MODELSCOPE_CACHE or "E:/modelscope_cache"
    os.environ["MODELSCOPE_CACHE"] = cache_dir
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    logger.info("ModelScope 缓存目录: %s", cache_dir)

    # 尝试 ModelScope
    try:
        from modelscope import snapshot_download
        logger.info("正在通过 ModelScope 下载 BGE-M3 模型（首次约 2GB）...")
        path = snapshot_download(model_id, cache_dir=cache_dir)
        logger.info("BGE-M3 模型下载完成: %s", path)
        return str(path)
    except Exception as e:
        logger.warning("ModelScope 下载失败: %s，尝试 HuggingFace...", e)

    # 降级 HuggingFace（设置镜像 + 缓存目录）
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HOME", cache_dir)
    try:
        from huggingface_hub import snapshot_download as hf_download
        logger.info("正在通过 HuggingFace 下载 BGE-M3 模型...")
        path = hf_download(model_id, cache_dir=cache_dir)
        logger.info("BGE-M3 模型下载完成: %s", path)
        return str(path)
    except Exception as e:
        raise RuntimeError(
            f"BGE-M3 模型下载失败（ModelScope + HuggingFace 均不可用）: {e}\n"
            "请手动下载模型到本地，或检查网络/代理设置。"
        )


class BGEM3Embedder:
    """BGE-M3 本地 embedding 单例"""

    def __init__(self) -> None:
        self._model: Any = None
        self._model_path: str | None = None

    @property
    def available(self) -> bool:
        """FlagEmbedding 是否已安装"""
        try:
            import FlagEmbedding  # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure(self):
        """懒加载模型（首次加载含模型下载，可能需数分钟）"""
        if self._model is not None:
            return self._model
        if not self.available:
            raise RuntimeError(
                "FlagEmbedding 未安装，请 pip install FlagEmbedding"
            )
        from FlagEmbedding import BGEM3FlagModel

        import torch
        use_fp16 = torch.cuda.is_available()
        device = "cuda" if use_fp16 else "cpu"

        # 确保模型已下载到本地
        if self._model_path is None:
            self._model_path = _download_model()

        logger.info("正在加载 BGE-M3 模型（device=%s, fp16=%s）...", device, use_fp16)
        self._model = BGEM3FlagModel(
            self._model_path,
            use_fp16=use_fp16,
            device=device,
        )
        logger.info("BGE-M3 模型加载完成 device=%s", device)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """批量算 embedding（async，内部 to_thread 不阻塞事件循环）

        返回 1024 维稠密向量列表。
        """
        if not texts:
            return []

        def _encode() -> list[list[float]]:
            model = self._ensure()
            # BGE-M3 encode 返回 dict: {'dense_vecs': np.ndarray, ...}
            result = model.encode(
                texts,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            # dense_vecs 是 numpy ndarray [N, 1024]
            vecs = result["dense_vecs"]
            return [v.tolist() for v in vecs]

        return await asyncio.to_thread(_encode)

    async def embed_one(self, text: str) -> list[float]:
        """单条 embedding（便捷方法）"""
        vecs = await self.embed([text])
        return vecs[0] if vecs else []


class ApiEmbedder:
    """API embedding：硅基流动 BGE-M3（OpenAI 兼容），零本地内存占用。

    适用低配服务器（2C4G）：模型在云端推理，本地只发 HTTP 请求拿向量。
    维度与本地 BGE-M3 完全一致（1024），Chroma 已灌向量可直接复用。
    """

    def __init__(self) -> None:
        self._client = None

    @property
    def available(self) -> bool:
        """配置了 API key 即可用"""
        return bool(settings.EMBEDDING_API_KEY)

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                base_url=settings.EMBEDDING_API_BASE,
                headers={"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"},
                timeout=30,
            )
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """批量算 embedding（同步 HTTP 走 to_thread 不阻塞事件循环）"""
        if not texts:
            return []
        if not self.available:
            raise RuntimeError("API embedding 未配置（EMBEDDING_API_KEY 为空）")

        def _call() -> list[list[float]]:
            client = self._get_client()
            resp = client.post(
                "/embeddings",
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "input": texts,
                    "encoding_format": "float",
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            data.sort(key=lambda x: x.get("index", 0))
            return [d["embedding"] for d in data]

        return await asyncio.to_thread(_call)

    async def embed_one(self, text: str) -> list[float]:
        vecs = await self.embed([text])
        return vecs[0] if vecs else []


def get_embedder():
    """按 EMBEDDING_PROVIDER 选择 embedding 后端（local/api）"""
    return api_embedder if settings.EMBEDDING_PROVIDER == "api" else bge_embedder


# 模块级单例
bge_embedder = BGEM3Embedder()
api_embedder = ApiEmbedder()
embedder = get_embedder()
