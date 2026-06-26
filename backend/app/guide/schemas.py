"""智能导诊 Pydantic 模型

Dify AI 增强版 — 向后兼容规则引擎返回格式。
规则引擎返回时，AI 专属字段为默认值/空列表。
"""

from pydantic import BaseModel, Field


class GuideRequest(BaseModel):
    symptom_text: str = Field(
        min_length=1, max_length=500,
        description="症状描述（支持方言/口语，如: 头疼三天）"
    )


# ── Dify AI 专属模型 ──

class MedicationSuggestion(BaseModel):
    """用药建议（仅 OTC，来自 Dify AI）"""
    drug_name: str = Field(default="", description="药品通用名")
    indication: str = Field(default="", description="适应症说明")
    dosage_note: str = Field(default="", description="用法用量参考")
    elderly_precaution: str = Field(default="", description="老年患者特别注意事项")
    contraindication: str = Field(default="", description="禁忌症")


# ── 向后兼容的匹配结果 ──

class MatchResult(BaseModel):
    """科室匹配结果（同时兼容规则引擎和 Dify AI）

    - 规则引擎填充: dept_name, total_score, matched_symptoms
    - Dify AI 填充:   dept_name, confidence, reasoning
    """
    dept_name: str
    total_score: int = 0              # 规则引擎：加权匹配分数
    matched_symptoms: list[str] = []  # 规则引擎：匹配到的症状关键词
    confidence: float = 0.0           # Dify AI：置信度 (0.0-1.0)
    reasoning: str = ""               # Dify AI：推荐理由


class GuideResponse(BaseModel):
    """导诊响应（扩展版，向后兼容）"""
    symptom_text: str
    results: list[MatchResult] = []    # 科室推荐列表（降序）
    suggestion: str = ""               # 综合就医建议文本

    # ── Dify AI 专属字段（规则引擎返回时为空/默认值） ──
    medications: list[MedicationSuggestion] = []
    elderly_precautions: str = ""
    emergency_flag: bool = False
    general_advice: str = ""
    engine: str = "rule"               # "dify" | "rule" — 前端据此区分展示
