"""智能导诊 Pydantic 模型

向后兼容：规则引擎 / LangGraph 两档共用同一响应结构。
- 规则引擎填充: dept_name, total_score, matched_symptoms
- LangGraph 填充: dept_name, confidence, reasoning, medications, ...
LangGraph 新增可选字段（thread_id / trace_id / emergency_level），前端零改动。
"""

from pydantic import BaseModel, Field


class GuideRequest(BaseModel):
    symptom_text: str = Field(
        min_length=1, max_length=500,
        description="症状描述（支持方言/口语，如: 头疼三天）"
    )
    # LangGraph 断点续推用：传上次返回的 thread_id 即可 resume，不传则新开一轮
    thread_id: str | None = Field(
        default=None,
        description="续推线程ID（LangGraph 模式可选，首轮不传）"
    )


# ── AI 专属模型 ──

class MedicationSuggestion(BaseModel):
    """用药建议（仅 OTC）"""
    drug_name: str = Field(default="", description="药品通用名")
    indication: str = Field(default="", description="适应症说明")
    dosage_note: str = Field(default="", description="用法用量参考")
    elderly_precaution: str = Field(default="", description="老年患者特别注意事项")
    contraindication: str = Field(default="", description="禁忌症")


# ── 向后兼容的匹配结果 ──

class MatchResult(BaseModel):
    """科室匹配结果（兼容规则引擎 / LangGraph）

    - 规则引擎: dept_name, total_score, matched_symptoms
    - LangGraph: dept_name, confidence, reasoning
    """
    dept_name: str
    total_score: int = 0
    matched_symptoms: list[str] = []
    confidence: float = 0.0
    reasoning: str = ""


class GuideResponse(BaseModel):
    """导诊响应（扩展版，两档向后兼容）"""
    symptom_text: str
    results: list[MatchResult] = []
    suggestion: str = ""

    # ── AI 专属字段（规则引擎返回时为空/默认值） ──
    medications: list[MedicationSuggestion] = []
    elderly_precautions: str = ""
    emergency_flag: bool = False
    general_advice: str = ""
    engine: str = "rule"               # "langgraph" | "rule"

    # ── LangGraph 新增（可选，前端可忽略） ──
    thread_id: str = ""               # 续推用，首轮返回供前端下次带上
    trace_id: str = ""                # request_id → thread_id → trace_id 三层可追
    emergency_level: str = ""         # "red" | "yellow" | "green"（空=未分级）
    emergency_message: str = ""       # 紧急分级警示语
