"""冒烟测试2：续推 + 红色急症链路验证"""
import os
os.environ["YFT_SKIP_CONFIG_CHECK"] = "1"

import asyncio
import sys


async def main():
    from app.guide.schemas import GuideRequest
    from app.guide.graph.build import run_guide_graph

    r1 = await run_guide_graph(GuideRequest(symptom_text="最近总是头晕"))
    print("首轮 thread_id:", r1.thread_id[:8], "engine:", r1.engine)
    sys.stdout.flush()

    r2 = await run_guide_graph(GuideRequest(symptom_text="还有点耳鸣", thread_id=r1.thread_id))
    print("续推 thread_id 一致:", r1.thread_id == r2.thread_id, "engine:", r2.engine)
    print("二轮 results:", [(x.dept_name, x.confidence) for x in r2.results])
    sys.stdout.flush()

    r3 = await run_guide_graph(GuideRequest(symptom_text="突发剧烈胸痛伴大汗"))
    print("红色急症:", r3.emergency_level, r3.emergency_flag)
    print("=== 全部通过 ===")
    sys.stdout.flush()


asyncio.run(main())
