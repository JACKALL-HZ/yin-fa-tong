"""FastAPI 应用入口"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI


from app.config import settings
from app.exception.handler import register_exception_handlers
from app.middleware.cors import setup_cors
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化中间件连接（RabbitMQ/ES 连不上也能跑）
    from app.shared.redis import init_redis          # noqa: E402
    await init_redis()

    _consumer_task = None
    try:
        from app.shared.rabbitmq import init_rabbitmq    # noqa: E402
        await init_rabbitmq()
        # 启动延时队列消费者（后台协程）：监听 q_delay_tasks，处理支付超时取消
        from app.reserve.mq.consumer import start_consumer  # noqa: E402
        _consumer_task = asyncio.create_task(start_consumer())

        def _on_consumer_done(task: asyncio.Task):
            if task.exception():
                logger.error("延时队列消费者异常退出: %s", task.exception())

        _consumer_task.add_done_callback(_on_consumer_done)
        logger.info("延时队列消费者已启动")
    except Exception as e:
        logger.warning("RabbitMQ 连接失败，消息队列功能不可用: %s", e)

    # 启动时预热知识库向量入库（LangGraph 导诊依赖 Chroma 语义检索）
    try:
        from app.shared.vector_store import vector_store  # noqa: E402
        if vector_store.enabled and not vector_store.is_ingested:
            count = await vector_store.ingest_kb()
            logger.info("知识库向量入库完成 chunks=%d", count)
    except Exception as e:
        logger.warning("知识库向量入库失败，语义检索不可用（降级规则引擎）: %s", e)

    try:
        from app.shared.elasticsearch import init_es, get_es, ensure_indexes  # noqa: E402
        await init_es()
        es = await get_es()
        await ensure_indexes(es)
    except Exception as e:
        logger.warning("Elasticsearch 连接失败，搜索功能不可用: %s", e)

    # 启动定时任务调度器（过期订单 + 号源对账）
    try:
        from app.shared.scheduler import start_scheduler  # noqa: E402
        start_scheduler()
    except Exception as e:
        logger.warning("定时任务调度器启动失败: %s", e)

    yield

    # 关闭时：停止消费者 + 释放连接
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass

    # 停止定时任务调度器
    try:
        from app.shared.scheduler import scheduler  # noqa: E402
        scheduler.shutdown(wait=False)
    except Exception:
        pass

    # 关闭 LangGraph 导诊图 sqlite checkpointer
    try:
        from app.guide.graph.build import close_graph  # noqa: E402
        await close_graph()
    except Exception:
        pass

    from app.shared.redis import close_redis          # noqa: E402
    await close_redis()
    try:
        from app.shared.rabbitmq import close_rabbitmq    # noqa: E402
        await close_rabbitmq()
    except Exception:
        pass
    try:
        from app.shared.elasticsearch import close_es     # noqa: E402
        await close_es()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="适老化智慧就医服务平台",
    lifespan=lifespan,
)

# 中间件注册顺序：CORS → Request ID → 请求日志
setup_cors(app)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 注册全局异常处理器
register_exception_handlers(app)

# ---- 注册业务路由 ----
from app.auth.router import router as auth_router          # noqa: E402
from app.user.router import router as user_router          # noqa: E402
from app.hospital.router import router as hospital_router  # noqa: E402
from app.department.router import router as dept_router    # noqa: E402
from app.doctor.router import router as doctor_router      # noqa: E402
from app.schedule.router import router as schedule_router  # noqa: E402
from app.reserve.router import router as reserve_router    # noqa: E402
from app.queue.router import router as queue_router        # noqa: E402
from app.payment.router import router as payment_router    # noqa: E402
from app.message.router import router as message_router    # noqa: E402
from app.guide.router import router as guide_router        # noqa: E402
from app.reminder.router import router as reminder_router  # noqa: E402
from app.statistics.router import router as stats_router   # noqa: E402
from app.accompany.volunteer.router import router as volunteer_router  # noqa: E402
from app.accompany.order.router import router as accompany_router      # noqa: E402
from app.report.router import router as report_router                  # noqa: E402
from app.search.router import router as search_router                    # noqa: E402
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(hospital_router)
app.include_router(dept_router)
app.include_router(doctor_router)
app.include_router(schedule_router)
app.include_router(reserve_router)
app.include_router(queue_router)
app.include_router(payment_router)
app.include_router(message_router)
app.include_router(guide_router)
app.include_router(reminder_router)
app.include_router(stats_router)
app.include_router(volunteer_router)
app.include_router(accompany_router)
app.include_router(report_router)
app.include_router(search_router)


@app.get("/", tags=["Health"])
async def root():
    """健康检查"""
    return {"code": 200, "message": f"{settings.APP_NAME} v{settings.APP_VERSION} running"}
