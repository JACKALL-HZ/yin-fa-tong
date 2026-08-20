"""OpenAI-compatible LLM 客户端封装

支持任一 OpenAI-compatible 服务（DeepSeek / 通义 / 硅基流动），
通过 LLM_BASE_URL 切换。仅作单节点能力调用，不再是整条链路。

节点级降级约定：llm_client.enabled=False 时，调用方走规则/词库兜底。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """从 LLM 文本中提取 JSON（兼容 ```json 代码块 / 裸花括号）"""
    if not text:
        return {}
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}


class LLMClient:
    """OpenAI-compatible 异步客户端（lazy init 单例）"""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._inited = False

    @property
    def enabled(self) -> bool:
        return bool(settings.LLM_API_KEY and settings.LLM_BASE_URL)

    def _ensure(self) -> AsyncOpenAI:
        """首次调用时创建 client（未配置则抛错，调用方应先判 enabled）"""
        if not self._inited:
            if not self.enabled:
                raise RuntimeError("LLM 未配置（LLM_BASE_URL/LLM_API_KEY），请走规则降级")
            self._client = AsyncOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
                timeout=settings.LLM_TIMEOUT,
            )
            self._inited = True
            logger.info("LLM 客户端就绪 model=%s base_url=%s", settings.LLM_MODEL, settings.LLM_BASE_URL)
        assert self._client is not None
        return self._client

    async def chat(self, system: str, user: str, temperature: float | None = None) -> str:
        """对话补全，返回 LLM 文本"""
        client = self._ensure()
        resp = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        return resp.choices[0].message.content or ""

    async def chat_json(self, system: str, user: str, temperature: float | None = None) -> dict[str, Any]:
        """对话补全 + 提取 JSON，返回解析后的 dict（解析失败返回 {}）"""
        text = await self.chat(system, user, temperature)
        parsed = _extract_json(text)
        if not parsed:
            logger.warning("LLM 输出 JSON 解析失败，文本前200字: %s", text[:200])
        return parsed

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """批量算 embedding（按 EMBEDDING_PROVIDER 路由：local BGE-M3 或 api）

        用于 Chroma 向量检索。API 模式零本地内存占用。
        """
        from app.shared.embedding import get_embedder
        return await get_embedder().embed(texts)


# 模块级单例
llm_client = LLMClient()
