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

    # ---- Chroma 向量库 ----
    CHROMA_DB_DIR: str = "data/chroma"
    CHROMA_COLLECTION: str = "yinfa_kb"
    # Embedding 部署模式：local(本机 BGE-M3 推理) | api(硅基流动 BGE-M3 API)
    EMBEDDING_PROVIDER: str = "local"
    # 本地模型（BAAI/bge-m3，1024 维，零联网依赖）
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024
    # ModelScope 模型缓存目录（仅 local 模式用，默认放 E 盘避免 C 盘爆满）
    MODELSCOPE_CACHE: str = "E:/modelscope_cache"
    # API 模式（硅基流动 OpenAI 兼容接口，BGE-M3 同维度，零本地内存占用）
    EMBEDDING_API_BASE: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_API_KEY: str = ""
    # 知识库分块参数
    KB_CHUNK_SIZE: int = 512
    KB_CHUNK_OVERLAP: int = 128
    KB_TOP_K: int = 8
    KB_SCORE_THRESHOLD: float = 0.35
    # 混合检索：稀疏(BM25) + 稠密(向量) → RRF 融合 → LLM Reranker 重排
    BM25_TOP_N: int = 12            # 稀疏路召回数
    DENSE_TOP_N: int = 12           # 稠密路召回数
    RRF_K: int = 60                 # RRF 融合常数（标准值 60）
    RERANK_ENABLED: bool = True     # 是否启用 LLM 重排（关闭则只用 RRF 序）
    RERANK_TOP_K: int = 6           # 重排后保留数

    # ---- 阿里云短信 ----
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""

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

    # ── LangGraph 导诊引擎 ──
    # 引擎分派：langgraph(自建图+Chroma向量检索) | rule(纯规则兜底)
    GUIDE_ENGINE: str = "langgraph"
    # OpenAI-compatible LLM（可配 DeepSeek/通义/硅基流动，任一 base_url）
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "qwen-plus"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2000
    LLM_TIMEOUT: int = 60
    # Checkpointer 断点续推（sqlite 文件级，零依赖）
    GUIDE_CHECKPOINT_DB: str = "data/guide_checkpoints.sqlite"
    # 知识库目录（相对 backend/ 根）
    KB_DIR: str = "docs/knowledge-base"

    # ── 管理员注册码 ──
    ADMIN_REGISTER_CODE: str = "yft-admin-2026"

    @property
    def upload_dir_absolute(self) -> Path:
        """返回绝对路径的上传目录"""
        return BASE_DIR / self.UPLOAD_DIR

    @property
    def BASE_DIR(self) -> Path:
        """项目根目录（backend/），供 data 目录/chroma/checkpoint 等绝对路径拼接"""
        return BASE_DIR

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
