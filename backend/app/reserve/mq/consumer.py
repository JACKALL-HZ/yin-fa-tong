"""支付超时消费者 —— 超时未支付自动取消，释放号源"""

import json
import logging
import aio_pika
from sqlalchemy import update as sa_update

from app.shared.rabbitmq import get_channel
from app.shared.database import AsyncSessionLocal
from app.reserve.models import ReserveModel

logger = logging.getLogger(__name__)


async def _handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        reserve_id = data["reserve_id"]
        schedule_id = data["schedule_id"]
        source_type = data["source_type"]

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                sa_update(ReserveModel)
                .where(ReserveModel.id == reserve_id, ReserveModel.pay_status == 1)
                .values(pay_status=3, order_status=4)
            )
            if result.rowcount == 1:
                await session.commit()
                from app.shared.redis import rollback_source_redis
                await rollback_source_redis(schedule_id, source_type)
                logger.info("支付超时自动取消 reserve_id=%s", reserve_id)
            else:
                logger.info("订单已处理过或不存在，跳过 reserve_id=%s", reserve_id)


async def start_payment_timeout_consumer():
    """启动支付超时消费者（由 main.py lifespan 调用）"""
    channel = get_channel()
    queue = await channel.declare_queue("q_delay_tasks", durable=True)
    await queue.consume(_handle_message)
    logger.info("支付超时消费者启动监听")


# main.py 导入名
start_consumer = start_payment_timeout_consumer
