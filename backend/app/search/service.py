"""搜索模块业务逻辑层"""

from app.shared.elasticsearch import get_es, INDEX_HOSPITAL, INDEX_DEPARTMENT, INDEX_DOCTOR, INDEX_SYMPTOM
from app.search import repository as search_repo
from app.search.schemas import SearchResultItem, SearchResponse

# ES _index → 前端 type
_INDEX_TO_TYPE = {
    INDEX_HOSPITAL: "hospital",
    INDEX_DEPARTMENT: "department",
    INDEX_DOCTOR: "doctor",
    INDEX_SYMPTOM: "symptom",
}

VALID_TYPES = {"hospital", "department", "doctor", "symptom", "all"}


async def search(keyword: str, search_type: str = "all") -> SearchResponse:
    """统一搜索入口"""
    keyword = keyword.strip()
    if not keyword:
        return SearchResponse(keyword=keyword, total=0, results=[])

    es = await get_es()

    types = (
        ["hospital", "department", "doctor", "symptom"]
        if search_type == "all"
        else [search_type]
    )

    raw = await search_repo.search_multi(es, keyword, types)
    results = [_hit_to_result(h) for h in raw["hits"]]

    return SearchResponse(keyword=keyword, total=raw["total"], results=results)


def _hit_to_result(hit: dict) -> SearchResultItem:
    """将 ES 命中转换为统一的 SearchResultItem"""
    doc_type = _INDEX_TO_TYPE.get(hit.get("_index", ""), "unknown")
    doc_id = hit.get("id", 0)

    if doc_type == "hospital":
        return SearchResultItem(
            type="hospital",
            id=doc_id,
            title=hit.get("hospital_name", ""),
            subtitle=hit.get("address") or "",
            extra={
                "hospital_level": hit.get("hospital_level"),
                "route": f"/hospitals/{doc_id}/departments",
            },
        )

    if doc_type == "department":
        return SearchResultItem(
            type="department",
            id=doc_id,
            title=hit.get("dept_name", ""),
            subtitle=hit.get("hospital_name", ""),
            extra={
                "hospital_id": hit.get("hospital_id"),
                "route": f"/departments/{doc_id}/doctors",
            },
        )

    if doc_type == "doctor":
        return SearchResultItem(
            type="doctor",
            id=doc_id,
            title=hit.get("doctor_name", ""),
            subtitle=f"{hit.get('dept_name', '')} · {hit.get('hospital_name', '')}",
            extra={
                "doctor_title": hit.get("doctor_title"),
                "specialty": hit.get("specialty"),
                "register_fee": str(hit.get("register_fee", 0)),
                "route": f"/doctors/{doc_id}/schedules",
            },
        )

    if doc_type == "symptom":
        kw_list = hit.get("keywords", [])
        kw_str = "、".join(kw_list[:3])
        return SearchResultItem(
            type="symptom",
            id=hit.get("id", ""),
            title=kw_str,
            subtitle=f"推荐科室：{hit.get('dept_name', '')}",
            extra={
                "dept_name": hit.get("dept_name"),
                "weight": hit.get("weight"),
            },
        )

    return SearchResultItem(type="unknown", id=0, title="未知", subtitle="")
