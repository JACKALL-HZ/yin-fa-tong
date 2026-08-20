"""冒烟测试：全降级路径（LLM 未配置，图内节点全部走词库/规则降级）"""
import os
os.environ["YFT_SKIP_CONFIG_CHECK"] = "1"

import asyncio


async def main():
    from app.guide.schemas import GuideRequest
    from app.guide.service import guide_diagnose

    print("── case 1: 常规症状（词库降级链路）──")
    resp = await guide_diagnose(GuideRequest(symptom_text="头疼三天了，还有点发烧咳嗽"))
    print("engine:", resp.engine)
    print("results:", [(r.dept_name, r.total_score) for r in resp.results])
    print("suggestion:", resp.suggestion[:80])
    print("thread_id:", resp.thread_id[:8] + "...")

    print("\n── case 2: 红色急症（条件边直跳 assemble）──")
    resp2 = await guide_diagnose(GuideRequest(symptom_text="突然剧烈胸痛伴大汗，压榨样胸痛不止"))
    print("engine:", resp2.engine)
    print("emergency_level:", resp2.emergency_level)
    print("emergency_flag:", resp2.emergency_flag)
    print("results:", resp2.results)
    print("suggestion:", resp2.suggestion[:80])


asyncio.run(main())
