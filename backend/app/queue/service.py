"""候诊排队业务逻辑层

Redis 缓存候诊数据：当前叫号数、排队人数、预估等待时间
"""

import logging
from app.shared.redis import get_redis

logger = logging.getLogger(__name__)


async def get_queue_status(schedule_id: int) -> dict:
    """获取某个排班的实时候诊进度"""
    r = await get_redis()
    current = await r.get(f"queue:{schedule_id}:current") or "0"
    total = await r.get(f"queue:{schedule_id}:total") or "0"
    return {
        "schedule_id": schedule_id,
        "current_number": int(current),      # 当前叫到几号
        "total_waiting": int(total),          # 总候诊人数
        "before_you": max(0, int(total) - int(current)),  # 前方等待人数
        "estimated_minutes": max(1, (int(total) - int(current)) * 5),  # 预估等待（每人5分钟）
    }


async def get_my_queue_position(queue_code: str) -> dict | None:
    """根据候诊编号查询个人排队位置"""
    r = await get_redis()
    data = await r.hgetall(f"queue_item:{queue_code}")
    if not data:
        # Redis 中无记录（可能重启丢失或旧订单），返回默认值
        return {
            "queue_code": queue_code,
            "my_number": 0,
            "current_number": 0,
            "before_you": 0,
            "estimated_minutes": 0,
        }
    schedule_id = int(data.get("schedule_id", 0))
    my_number = int(data.get("number", 0))
    current = int(await r.get(f"queue:{schedule_id}:current") or 0)
    return {
        "queue_code": queue_code,
        "my_number": my_number,
        "current_number": current,
        "before_you": max(0, my_number - current),
        "estimated_minutes": max(1, (my_number - current) * 5),
    }


async def enqueue(reserve_id: int, schedule_id: int, queue_code: str):
    """加入候诊队列"""
    r = await get_redis()
    # 递增排队总数
    total = await r.incr(f"queue:{schedule_id}:total")
    # 存储个人排队信息
    await r.hset(f"queue_item:{queue_code}", mapping={
        "reserve_id": str(reserve_id),
        "schedule_id": str(schedule_id),
        "number": str(total),
    })


async def call_next(schedule_id: int) -> int:
    """医生叫下一个号（模拟）"""
    r = await get_redis()
    return await r.incr(f"queue:{schedule_id}:current")
