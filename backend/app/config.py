"""系统配置模块 —— 读取 .env 环境变量"""

from pathlib import Path
from pydantic_settings import BaseSettings

# 项目根目录（backend/）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ---- 应用 ----
    APP_NAME: str = "银发通"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ---- 数据库 ----
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root123"
    DB_NAME: str = "yinfa_tong"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # ---- Redis ----
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ---- RabbitMQ ----
    RABBITMQ_HOST: str = "127.0.0.1"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    # ---- Elasticsearch ----
    ES_HOST: str = "127.0.0.1"
    ES_PORT: int = 9200

    # ---- JWT ----
    JWT_SECRET_KEY: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ---- 文件上传 ----
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ---- Dify AI (Chatflow 模式) ----
    DIFY_API_KEY: str = ""
    DIFY_BASE_URL: str = "https://api.dify.ai"
    DIFY_CHAT_ENDPOINT: str = "/v1/chat-messages"
    DIFY_TIMEOUT: int = 60

    # ── 支付宝沙箱 ──
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_GATEWAY: str = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    ALIPAY_NOTIFY_URL: str = "http://118.31.120.180/api/payment/notify"
    ALIPAY_RETURN_URL: str = "http://118.31.120.180/pay-result"
    ALIPAY_OAUTH_REDIRECT_URI: str = "http://118.31.120.180/auth/callback"
    # 支付模式：sandbox=沙箱 / mock=纯模拟（降级方案）
    PAY_MODE: str = "mock"
    DIFY_MAX_RETRIES: int = 1
    DIFY_APP_MODE: str = "chatflow"  # "chatflow" (Chatflow/Advanced-Chat) | "chatbot" (聊天助手)

    # ── 管理员注册码 ──
    ADMIN_REGISTER_CODE: str = "yft-admin-2026"

    @property
    def upload_dir_absolute(self) -> Path:
        """返回绝对路径的上传目录"""
        return BASE_DIR / self.UPLOAD_DIR

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# ── 生产环境安全校验（测试环境跳过） ──
import os as _os
if not _os.environ.get("YFT_SKIP_CONFIG_CHECK"):
    if settings.JWT_SECRET_KEY in ("change-me-jwt-secret", "change-me-in-production-use-random-string"):
        raise RuntimeError(
            "JWT_SECRET_KEY 不能使用默认值，请修改 .env 中的 JWT_SECRET_KEY 为随机字符串后再启动"
        )
    if settings.DB_PASSWORD in ("root123", "root"):
        import warnings
        warnings.warn("DB_PASSWORD 使用了默认值，生产环境必须修改", RuntimeWarning)

# 确保上传目录存在
settings.upload_dir_absolute.mkdir(parents=True, exist_ok=True)
