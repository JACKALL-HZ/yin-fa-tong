"""挂号消息生产者 —— 延时取消 + 挂号成功通知"""

import logging
from app.shared.rabbitmq import publish_direct, publish_delay

logger = logging.getLogger(__name__)

# 15 分钟超时（毫秒）
TIMEOUT_MS = 15 * 60 * 1000


async def send_reserve_success(user_id: int, reserve_id: int, queue_code: str):
    """挂号成功通知"""
    await publish_direct(
        exchange="ex_reserve",
        routing_key="reserve.success",
        body={
            "type": "reserve_success",
            "user_id": user_id,
            "reserve_id": reserve_id,
            "queue_code": queue_code,
        },
    )


async def send_payment_timeout(reserve_id: int, schedule_id: int, source_type: str):
    """延时取消消息：15 分钟后自动取消未支付订单"""
    await publish_delay(
        routing_key="delay.task",
        body={
            "type": "payment_timeout",
            "reserve_id": reserve_id,
            "schedule_id": schedule_id,
            "source_type": source_type,
        },
        delay_ms=TIMEOUT_MS,
    )
    logger.info("已发送延时取消消息 reserve_id=%s delay=%sms", reserve_id, TIMEOUT_MS)
