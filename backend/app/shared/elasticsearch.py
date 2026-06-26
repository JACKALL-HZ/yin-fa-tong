"""Elasticsearch 异步客户端

仅同步四类基础数据：医院/科室/医生/症状词库
"""

import asyncio
from elasticsearch import AsyncElasticsearch
from app.config import settings

es_client: AsyncElasticsearch | None = None
_es_lock = asyncio.Lock()


async def init_es() -> AsyncElasticsearch:
    """初始化 ES 客户端"""
    global es_client
    es_client = AsyncElasticsearch(
        hosts=[f"http://{settings.ES_HOST}:{settings.ES_PORT}"],
        request_timeout=10,
        retry_on_timeout=True,
        max_retries=3,
    )
    # 验证连接
    await es_client.info()
    return es_client


async def close_es():
    """关闭 ES 客户端"""
    global es_client
    if es_client:
        await es_client.close()
        es_client = None


async def get_es() -> AsyncElasticsearch:
    """返回 ES 客户端（未初始化则自动连接，双重检查锁保证并发安全）"""
    global es_client
    if es_client is None:
        async with _es_lock:
            if es_client is None:
                es_client = await init_es()
    return es_client


# 索引名称常量
INDEX_HOSPITAL = "yft_hospital"
INDEX_DEPARTMENT = "yft_department"
INDEX_DOCTOR = "yft_doctor"
INDEX_SYMPTOM = "yft_symptom"


async def ensure_indexes(es: AsyncElasticsearch):
    """启动时幂等创建所有索引（已存在则跳过）"""
    from app.search.mappings import INDEX_MAPPINGS
    for index_name, body in INDEX_MAPPINGS.items():
        if not await es.indices.exists(index=index_name):
            await es.indices.create(index=index_name, **body)
