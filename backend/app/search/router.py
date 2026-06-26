"""搜索模块路由层"""

from fastapi import APIRouter, Query, Depends
from app.shared.response import ApiResponse
from app.auth.service import require_admin
from app.search import service
from app.search.service import VALID_TYPES
from app.search.schemas import SearchResponse

router = APIRouter(prefix="/api/search", tags=["全局搜索"])


@router.get("", response_model=ApiResponse[SearchResponse])
async def global_search(
    keyword: str = Query(min_length=1, max_length=200, description="搜索关键词"),
    type: str = Query(default="all", description="搜索类型: hospital|department|doctor|symptom|all"),
):
    """全局搜索

    支持按医院、科室、医生、症状四种类型搜索。
    使用 IK 中文分词器 + multi_match best_fields 匹配。
    """
    if type not in VALID_TYPES:
        type = "all"
    data = await service.search(keyword, type)
    return ApiResponse.ok(data, message="搜索完成")


@router.post("/sync", response_model=ApiResponse)
async def trigger_full_sync(_admin=Depends(require_admin)):
    """触发全量索引重建（管理员专用）"""
    from app.search.sync.service import full_sync_all
    await full_sync_all()
    return ApiResponse.ok(message="ES 全量同步完成")
