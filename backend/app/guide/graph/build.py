"""LangGraph 导诊图构建与运行入口

图结构：
  symptom_extract → triage ─┬─(red)──────────────────────────────→ assemble
                            └─(yellow/green)→ retrieve → recommend → medication → assemble

- Checkpointer: AsyncSqliteSaver（按 thread_id 断点续推）
- run_guide_graph(): service.py 调用入口，返回 GuideResponse
"""
from __future__ import annotations

import json
import logging
import time
import uuid

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.guide.graph.callbacks import save_guide_run
from app.guide.graph.state import GuideState
from app.guide.graph.nodes.assemble import assemble
from app.guide.graph.nodes.extract import symptom_extract
from app.guide.graph.nodes.medication import medication
from app.guide.graph.nodes.recommend import recommend
from app.guide.graph.nodes.retrieve import retrieve
from app.guide.graph.nodes.triage import triage
from app.guide.schemas import GuideRequest, GuideResponse

logger = logging.getLogger(__name__)


def route_after_triage(state: GuideState) -> str:
    """红色急症：跳过检索/推荐/用药，直接组装紧急响应"""
    if state.get("emergency_level") == "red":
        return "assemble"
    return "retrieve"


def build_graph(checkpointer=None):
    """构建导诊图并 compile"""
    g = StateGraph(GuideState)
    g.add_node("symptom_extract", symptom_extract)
    g.add_node("triage", triage)
    g.add_node("retrieve", retrieve)
    g.add_node("recommend", recommend)
    g.add_node("medication", medication)
    g.add_node("assemble", assemble)

    g.add_edge(START, "symptom_extract")
    g.add_edge("symptom_extract", "triage")
    g.add_conditional_edges(
        "triage", route_after_triage,
        {"retrieve": "retrieve", "assemble": "assemble"},
    )
    g.add_edge("retrieve", "recommend")
    g.add_edge("recommend", "medication")
    g.add_edge("medication", "assemble")
    g.add_edge("assemble", END)
    return g.compile(checkpointer=checkpointer)


# ── checkpointer + graph 模块级单例 ──
_saver: AsyncSqliteSaver | None = None
_graph = None
_conn: aiosqlite.Connection | None = None


async def _ensure_graph():
    global _saver, _graph, _conn
    if _graph is None:
        db_path = settings.BASE_DIR / settings.GUIDE_CHECKPOINT_DB
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = await aiosqlite.connect(str(db_path))
        _saver = AsyncSqliteSaver(_conn)
        _graph = build_graph(checkpointer=_saver)
        logger.info("LangGraph 导诊图就绪 checkpointer=%s", db_path)
    return _graph


async def close_graph():
    """app shutdown 时调用：关闭 sqlite checkpointer 连接"""
    global _saver, _graph, _conn
    if _conn is not None:
        await _conn.close()
        _conn = None
        _saver = None
        _graph = None
        logger.info("LangGraph 导诊图已关闭")


async def run_guide_graph(req: GuideRequest) -> GuideResponse:
    """service.py 调用入口：跑图 → 返回 GuideResponse

    req.thread_id 非空 → 续推（Checkpointer 恢复上轮 state）
    req.thread_id 为空 → 新一轮（生成新 thread_id）

    astream(stream_mode="updates") 逐节点收集执行轨迹，结束后落 guide_runs（可观测）。
    """
    graph = await _ensure_graph()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    started = time.monotonic()
    nodes: list[str] = []
    final_state: dict = {}
    status, error = "ok", ""

    try:
        async for chunk in graph.astream(
            {"symptom_text": req.symptom_text, "thread_id": thread_id},
            config=config,
            stream_mode="updates",
        ):
            for node_name, update in chunk.items():
                nodes.append(node_name)
                if isinstance(update, dict):
                    final_state.update(update)
    except Exception as exc:
        status, error = "error", str(exc)[:500]
        raise
    finally:
        duration_ms = int((time.monotonic() - started) * 1000)
        # 落库 best-effort（失败仅告警，不影响响应/异常上抛）
        await save_guide_run(
            trace_id=thread_id,
            thread_id=thread_id,
            symptom_text=req.symptom_text,
            engine="langgraph",
            final_state=final_state,
            nodes=nodes,
            duration_ms=duration_ms,
            status=status,
            error=error,
        )
        logger.info("导诊图执行完成 nodes=%s duration=%dms", "→".join(nodes), duration_ms)

    resp_data = final_state.get("response")
    if isinstance(resp_data, dict) and resp_data:
        resp = GuideResponse.model_validate(resp_data)
        resp.thread_id = thread_id  # 返回给前端，下轮带上即续推
        if not resp.trace_id:
            resp.trace_id = thread_id
        return resp
    raise RuntimeError("LangGraph 图执行完成但未生成 response")


# ── SSE 流式入口 ──

def _sse(event: str, data) -> str:
    """格式化一条 SSE 事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# 节点中文展示名（前端进度条用）
_NODE_LABELS = {
    "symptom_extract": "正在分析症状",
    "triage": "紧急程度评估",
    "retrieve": "检索医学知识库",
    "recommend": "推荐就诊科室",
    "medication": "生成用药建议",
    "assemble": "组装导诊结果",
}


async def stream_guide_graph(req: GuideRequest):
    """SSE 流式：逐节点推送进度事件，结束推 final GuideResponse

    事件序列：node_start → node_end(×N) → final  （异常时 → error）
    llm_client 用裸 openai（非 LangChain ChatModel），故无 token 级流，
    此处为节点级进度流 + 最终整块结果。
    """
    graph = await _ensure_graph()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    started = time.monotonic()
    nodes: list[str] = []
    final_state: dict = {}
    status, error = "ok", ""

    try:
        yield _sse("start", {"thread_id": thread_id})
        async for chunk in graph.astream(
            {"symptom_text": req.symptom_text, "thread_id": thread_id},
            config=config,
            stream_mode="updates",
        ):
            for node_name, update in chunk.items():
                nodes.append(node_name)
                if isinstance(update, dict):
                    final_state.update(update)
                evt: dict = {
                    "node": node_name,
                    "label": _NODE_LABELS.get(node_name, node_name),
                }
                # 节点专属摘要（前端可据此前置展示）
                if node_name == "triage" and isinstance(update, dict):
                    evt["emergency_level"] = update.get("emergency_level")
                if node_name == "retrieve" and isinstance(update, dict):
                    evt["hits"] = len(update.get("kb_context", []))
                if node_name == "recommend" and isinstance(update, dict):
                    evt["dept"] = (update.get("results") or [{}])[0].get("dept_name", "") if update.get("results") else ""
                yield _sse("node_end", evt)

        resp_data = final_state.get("response")
        if isinstance(resp_data, dict) and resp_data:
            resp = GuideResponse.model_validate(resp_data)
            resp.thread_id = thread_id
            if not resp.trace_id:
                resp.trace_id = thread_id
            yield _sse("final", resp.model_dump())
        else:
            status, error = "error", "未生成 response"
            yield _sse("error", {"message": "导诊图未生成结果"})
    except Exception as exc:
        status, error = "error", str(exc)[:500]
        yield _sse("error", {"message": str(exc)[:200]})
    finally:
        duration_ms = int((time.monotonic() - started) * 1000)
        await save_guide_run(
            trace_id=thread_id, thread_id=thread_id,
            symptom_text=req.symptom_text, engine="langgraph",
            final_state=final_state, nodes=nodes,
            duration_ms=duration_ms, status=status, error=error,
        )
        logger.info("流式导诊完成 nodes=%s duration=%dms", "→".join(nodes), duration_ms)
