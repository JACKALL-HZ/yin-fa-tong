"""节点[5] 用药建议：仅 OTC，基于《老年用药安全手册》检索结果

安全红线：
- 只推荐 OTC 非处方药，绝不推荐处方药
- 手册检索无相关内容时返回空列表，不凭 LLM 记忆编造
- 红色急症不进此节点（条件边已跳过）
"""
from __future__ import annotations

import logging

from app.guide.graph.state import GuideState
from app.shared.llm import llm_client
from app.shared.vector_store import vector_store

logger = logging.getLogger(__name__)

MEDICATION_SYSTEM = """你是老年用药安全助手。仅根据提供的《老年用药安全手册》参考资料，给出非处方药(OTC)用药建议。

安全红线（必须遵守）：
1. 只推荐 OTC 非处方药，绝不推荐处方药
2. 参考资料中没有相关内容时，medications 输出空列表，不要凭记忆编造
3. 每条建议必须包含老年患者注意事项和禁忌说明
4. 提醒：用药建议仅供参考，具体用药请遵医嘱或咨询药师

输出严格 JSON，格式如下：
{
  "medications": [
    {"drug_name": "药品通用名", "indication": "适应症", "dosage_note": "用法用量参考", "elderly_precaution": "老年患者注意事项", "contraindication": "禁忌症"}
  ],
  "elderly_precautions": "老年患者总体用药安全提醒"
}

最多3条。只输出 JSON，不要任何其他文字。"""


async def medication(state: GuideState) -> dict:
    if not llm_client.enabled:
        return {"medications": [], "elderly_precautions": ""}

    try:
        # 单独检索老年用药手册（dept_filter 精确匹配手册目录）
        med_ctx: list[dict] = []
        if vector_store.enabled and vector_store.is_ingested:
            symptoms = state.get("symptoms", [])
            s_desc = "、".join(s.get("entity", "") for s in symptoms if s.get("entity"))
            query = f"{s_desc or state.get('symptom_text', '')} 老年用药 OTC 注意事项"
            med_ctx = await vector_store.hybrid_search(query, top_k=4, dept_filter="99_老年用药安全手册")

        if not med_ctx:
            logger.info("用药手册无相关检索结果，不给用药建议（安全红线：不编造）")
            return {"medications": [], "elderly_precautions": ""}

        ctx = "\n---\n".join(
            f"[{h.get('source', '')}] {h.get('document', '')[:500]}" for h in med_ctx
        )
        user_msg = f"患者症状：{state.get('symptom_text', '')}\n\n参考资料：\n{ctx}"

        parsed = await llm_client.chat_json(MEDICATION_SYSTEM, user_msg, temperature=0.1)
        meds = parsed.get("medications", [])
        # 防御：过滤空药品名
        meds = [m for m in meds if m.get("drug_name")]
        logger.info("用药建议 count=%d", len(meds))
        return {
            "medications": meds[:3],
            "elderly_precautions": parsed.get("elderly_precautions", ""),
        }
    except Exception as exc:
        logger.warning("用药建议生成失败（返回空）: %s", exc)
        return {"medications": [], "elderly_precautions": ""}
