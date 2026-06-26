"""ES 数据访问层 —— 封装索引 CRUD 与多索引模糊搜索"""

import logging
from elasticsearch import AsyncElasticsearch
from app.shared.elasticsearch import INDEX_HOSPITAL, INDEX_DEPARTMENT, INDEX_DOCTOR, INDEX_SYMPTOM

logger = logging.getLogger(__name__)

# 类型 → 索引名映射
TYPE_TO_INDEX = {
    "hospital": INDEX_HOSPITAL,
    "department": INDEX_DEPARTMENT,
    "doctor": INDEX_DOCTOR,
    "symptom": INDEX_SYMPTOM,
}

# 各类型的搜索字段及权重（名称 ^3，专长 ^2，其余 ^1）
_SEARCH_FIELDS = {
    "hospital": ["hospital_name^3", "address"],
    "department": ["dept_name^3", "hospital_name"],
    "doctor": ["doctor_name^3", "specialty^2", "dept_name", "hospital_name", "doctor_title"],
    "symptom": ["keywords^3", "dept_name"],
}


async def index_document(es: AsyncElasticsearch, index: str, doc_id: int | str, document: dict):
    """索引（新建或全量替换）单条文档"""
    await es.index(index=index, id=str(doc_id), document=document)


async def bulk_index(es: AsyncElasticsearch, index: str, docs: list[dict]):
    """批量索引文档"""
    if not docs:
        return
    body = []
    for doc in docs:
        body.append({"index": {"_index": index, "_id": str(doc["id"])}})
        body.append(doc)
    resp = await es.bulk(body=body)
    if resp.get("errors"):
        for item in resp["items"]:
            op = item.get("index", {})
            if op.get("error"):
                logger.error("Bulk index error doc_id=%s: %s", op.get("_id"), op["error"])


async def delete_document(es: AsyncElasticsearch, index: str, doc_id: int | str):
    """删除单条文档（忽略不存在）"""
    await es.delete(index=index, id=str(doc_id), ignore=[404])


async def delete_index(es: AsyncElasticsearch, index: str):
    """删除整个索引（全量重建前使用）"""
    await es.indices.delete(index=index, ignore=[404])


async def search_multi(
    es: AsyncElasticsearch,
    keyword: str,
    search_types: list[str],
    size: int = 50,
) -> dict:
    """多索引模糊搜索

    使用 multi_match + best_fields：每个文档只取最佳匹配字段的分数，
    避免一个文档多个字段弱匹配反而排名虚高的问题。
    """
    indices = _resolve_indices(search_types)
    if not indices:
        return {"total": 0, "hits": []}

    # 合并所有目标类型的搜索字段
    all_fields = []
    for st in search_types:
        all_fields.extend(_SEARCH_FIELDS.get(st, []))

    query_body = {
        "query": {
            "multi_match": {
                "query": keyword,
                "fields": all_fields,
                "type": "best_fields",
            }
        },
        "size": size,
    }

    result = await es.search(index=indices, body=query_body)
    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]

    # 附加 _index 字段方便 service 层区分类型
    enriched = []
    for h in hits:
        src = h["_source"]
        src["_index"] = h["_index"]
        enriched.append(src)

    return {"total": total, "hits": enriched}


def _resolve_indices(search_types: list[str]) -> list[str]:
    """将搜索类型转换为 ES 索引名列表"""
    indices = []
    for st in search_types:
        idx = TYPE_TO_INDEX.get(st)
        if idx and idx not in indices:
            indices.append(idx)
    return indices
