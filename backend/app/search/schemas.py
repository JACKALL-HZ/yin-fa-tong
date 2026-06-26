"""搜索模块 Pydantic 模型

包含：
  - ES 文档模型（用于索引/反序列化）
  - 统一搜索请求/响应模型
"""

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════
#  ES 文档模型
# ═══════════════════════════════════════════════════════════════

class HospitalDocument(BaseModel):
    id: int
    hospital_name: str
    hospital_level: str | None = None
    address: str | None = None


class DepartmentDocument(BaseModel):
    id: int
    hospital_id: int
    hospital_name: str
    dept_name: str


class DoctorDocument(BaseModel):
    id: int
    dept_id: int
    hospital_id: int
    doctor_name: str
    doctor_title: str | None = None
    specialty: str | None = None
    register_fee: float = 0
    doctor_avatar: str | None = None
    dept_name: str
    hospital_name: str


class SymptomDocument(BaseModel):
    id: str
    keywords: list[str]
    dept_name: str
    weight: int


# ═══════════════════════════════════════════════════════════════
#  搜索请求/响应
# ═══════════════════════════════════════════════════════════════

class SearchResultItem(BaseModel):
    """单条搜索结果（四类归一化）"""
    type: str           # hospital | department | doctor | symptom
    id: int | str
    title: str          # 主标题
    subtitle: str       # 副标题
    extra: dict | None = None  # 附加信息（等级/职称/route 等）


class SearchResponse(BaseModel):
    """搜索响应"""
    keyword: str
    total: int
    results: list[SearchResultItem]
