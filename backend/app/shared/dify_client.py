"""Dify Chatflow / Chatbot API HTTP 客户端

支持两种 Dify App 模式:
  - chatflow (advanced-chat): Chatflow 模式，通过 Start 节点的 inputs 变量传参
  - chatbot  (chat)       : 聊天助手模式，直接用 query 字段传参

默认为 chatflow 模式，通过 DIFY_APP_MODE 配置切换。
"""

import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class DifyClient:
    """Dify Chatflow/Chatbot 异步 HTTP 客户端（单例）"""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.DIFY_API_KEY)

    @property
    def mode(self) -> str:
        return settings.DIFY_APP_MODE

    async def start(self) -> None:
        if not self.enabled:
            logger.info("Dify API Key 未配置，智能导诊将使用本地规则引擎")
            return
        self._client = httpx.AsyncClient(
            base_url=settings.DIFY_BASE_URL,
            timeout=httpx.Timeout(settings.DIFY_TIMEOUT),
            headers={
                "Authorization": f"Bearer {settings.DIFY_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        logger.info("Dify 客户端已就绪 mode=%s base_url=%s", self.mode, settings.DIFY_BASE_URL)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        query: str,
        user_id: str = "anonymous",
        inputs: dict | None = None,
    ) -> str:
        """调用 Dify API（blocking 模式），返回 LLM 生成的文本答案。

        根据 DIFY_APP_MODE 自动选择传参方式:
          - chatflow: 通过 inputs 字段传递 Start 节点变量
          - chatbot:  直接通过 query 字段传递问题

        Dify Chatflow API (POST /v1/chat-messages):
          Request:  {"inputs": {"var_name": "..."}, "query": "...", "response_mode": "blocking", "user": "..."}
          Response: {"answer": "...", "conversation_id": "...", ...}

        Args:
            query:   用户输入的问题文本
            user_id: Dify 用户标识（用于会话隔离）
            inputs:  Chatflow Start 节点的输入变量字典（chatflow 模式使用）

        Returns:
            LLM 生成的文本答案（由后端 service 层解析）
        """
        if not self._client:
            raise RuntimeError("DifyClient 未启动，请先调用 start()")

        # Chatflow 模式：将 query 映射为 symptom_text 输入变量
        if self.mode == "chatflow":
            payload_inputs = inputs or {"symptom_text": query}
        else:
            payload_inputs = inputs or {}

        payload = {
            "inputs": payload_inputs,
            "query": query,
            "response_mode": "blocking",
            "user": user_id,
        }

        last_error = None
        for attempt in range(settings.DIFY_MAX_RETRIES + 1):
            try:
                resp = await self._client.post(
                    settings.DIFY_CHAT_ENDPOINT,
                    json=payload,
                )
                resp.raise_for_status()
                body = resp.json()
                answer = body.get("answer", "")
                conv_id = body.get("conversation_id", "")
                logger.info("Dify API 调用成功 mode=%s conversation_id=%s", self.mode, conv_id)
                return answer

            except httpx.TimeoutException:
                last_error = f"请求超时 (attempt {attempt + 1})"
                logger.warning("Dify API %s", last_error)

            except httpx.HTTPStatusError as exc:
                last_error = f"HTTP {exc.response.status_code}"
                logger.error("Dify API 返回错误: %s body=%s", last_error,
                           exc.response.text[:200] if exc.response else "")
                if 400 <= exc.response.status_code < 500:
                    raise

        raise httpx.TimeoutException(last_error or "Dify 请求失败")


# 模块级单例
dify_client = DifyClient()
