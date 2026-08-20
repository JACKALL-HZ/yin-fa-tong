"""LangGraph 导诊图状态定义（GraphState）

TypedDict + total=False：所有字段可选，节点按需填充。
断点续推时 Checkpointer 按 thread_id 持久化整个 state。
"""
from __future__ import annotations

from typing import TypedDict


class GuideState(TypedDict, total=False):
    # ── 输入 ──
    user_id: str
    symptom_text: str
    thread_id: str | None            # 断点续推：上轮返回的，下轮带上即 resume

    # ── [1] 症状抽取 ──
    symptoms: list[dict]             # [{entity, modifier, duration}]
    candidate_depts: list[str]       # 词库预筛科室
    extract_engine: str              # "llm" | "lexicon" | "rule"

    # ── [2] 知识库检索 ──
    kb_context: list[dict]           # [{source, chunk, score}]

    # ── [3] 科室推荐 ──
    departments: list[dict]         # [{dept_name, confidence, reasoning}]

    # ── [4] 用药建议 ──
    medications: list[dict]          # [{drug_name, indication, ...}]

    # ── [5] 紧急分级 ──
    emergency_level: str             # "red" | "yellow" | "green"
    emergency_message: str

    # ── [6] 组装 ──
    response: dict                   # GuideResponse.model_dump()，assemble 节点填充（checkpoint 只存原生类型）
    engine: str                      # "langgraph" | "rule"（前端据此区分展示）
    trace: list[dict]                # 节点级 trace（回调写入）
