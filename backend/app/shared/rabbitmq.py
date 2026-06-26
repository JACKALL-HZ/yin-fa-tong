"""RabbitMQ 异步客户端 —— Direct 直连 + Delay 延迟双交换机

交换机定义：
- ex_reserve:      挂号成功通知（Direct）
- ex_queue:        候诊顺位/到号提醒（Direct）
- ex_accompany:    陪诊申请通知（Direct）
- ex_delay:        延时任务（Delay）：挂号超时取消、用药提醒、复诊提醒

队列绑定：
- ex_reserve → q_reserve_notify   (reserve.success)
- ex_queue   → q_queue_notify     (queue.progress)
- ex_accompany → q_accompany_notify (accompany.submit)
- ex_delay   → q_delay_tasks      (delay.task) — 支付超时取消等延时任务
"""

import json
import logging
import aio_pika
from app.config import settings

logger = logging.getLogger(__name__)

# 全局连接
_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.RobustChannel | None = None


async def init_rabbitmq():
    """初始化 RabbitMQ 连接 + 声明交换机/队列"""
    global _connection, _channel

    url = (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
        f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
    )
    _connection = await aio_pika.connect_robust(url)
    _channel = await _connection.channel()

    # ---- Direct 直连交换机 ----
    ex_reserve = await _channel.declare_exchange("ex_reserve", aio_pika.ExchangeType.DIRECT, durable=True)
    ex_queue = await _channel.declare_exchange("ex_queue", aio_pika.ExchangeType.DIRECT, durable=True)
    ex_accompany = await _channel.declare_exchange("ex_accompany", aio_pika.ExchangeType.DIRECT, durable=True)

    # ---- Delay 延迟交换机 ----
    ex_delay = await _channel.declare_exchange(
        "ex_delay",
        aio_pika.ExchangeType.X_DELAYED_MESSAGE,
        durable=True,
        arguments={"x-delayed-type": "direct"},
    )

    # 绑定队列
    for (exchange, queue_name, routing_key) in [
        (ex_reserve, "q_reserve_notify", "reserve.success"),
        (ex_queue, "q_queue_notify", "queue.progress"),
        (ex_accompany, "q_accompany_notify", "accompany.submit"),
        (ex_delay, "q_delay_tasks", "delay.task"),
    ]:
        queue = await _channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=routing_key)

    logger.info("RabbitMQ 连接初始化完成（Direct×3 + Delay×1）")


def get_channel() -> aio_pika.RobustChannel:
    """获取当前 channel（供消费者使用）"""
    if _channel is None:
        raise RuntimeError("RabbitMQ channel 未初始化")
    return _channel


async def close_rabbitmq():
    """关闭 RabbitMQ 连接"""
    global _connection
    if _connection:
        await _connection.close()
        _connection = None


async def publish_direct(exchange: str, routing_key: str, body: dict):
    """发布 Direct 消息"""
    global _channel
    if _channel is None:
        raise RuntimeError("RabbitMQ channel 未初始化")
    ex = await _channel.get_exchange(exchange)
    message = aio_pika.Message(
        body=json.dumps(body, ensure_ascii=False).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await ex.publish(message, routing_key=routing_key)


async def publish_delay(routing_key: str, body: dict, delay_ms: int):
    """发布延迟消息（到 ex_delay 交换机）"""
    global _channel
    if _channel is None:
        raise RuntimeError("RabbitMQ channel 未初始化")
    ex = await _channel.get_exchange("ex_delay")
    message = aio_pika.Message(
        body=json.dumps(body, ensure_ascii=False).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers={"x-delay": delay_ms},
    )
    await ex.publish(message, routing_key=routing_key)
