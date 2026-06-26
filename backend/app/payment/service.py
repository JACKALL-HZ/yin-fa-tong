"""支付宝沙箱支付业务逻辑

支付模式：
  - sandbox: 调用支付宝沙箱 API，生成真实支付页面
  - mock:    纯模拟，直接更新数据库状态（降级方案）
"""

import time
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.payment import repository as pay_repo
from app.payment.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResultResponse,
)
from app.reserve import repository as reserve_repo
from app.reserve.models import ReserveModel
from app.schedule import repository as schedule_repo
from app.doctor import repository as doctor_repo

logger = logging.getLogger(__name__)

# ── 支付宝客户端单例 ──
_alipay_client = None


def _format_private_key(key_str: str) -> str:
    """将私钥（裸 base64 / PKCS#8 PEM）转换为 PKCS#1 PEM（alipay SDK 要求）"""
    import base64
    key_str = key_str.strip()
    if key_str.startswith("-----BEGIN RSA PRIVATE KEY-----"):
        return key_str  # 已经是 PKCS#1
    # 去掉 PEM 头尾（如果有）
    if "-----" in key_str:
        key_str = key_str.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").replace("-----BEGIN RSA PRIVATE KEY-----", "").replace("-----END RSA PRIVATE KEY-----", "").strip()
    try:
        from cryptography.hazmat.primitives.serialization import load_der_private_key, Encoding, PrivateFormat, NoEncryption
        der = base64.b64decode(key_str)
        private_key = load_der_private_key(der, password=None)
        pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        return pem.decode("utf-8")
    except Exception:
        # fallback：直接包装 PEM 头
        lines = ["-----BEGIN RSA PRIVATE KEY-----"]
        for i in range(0, len(key_str), 64):
            lines.append(key_str[i : i + 64])
        lines.append("-----END RSA PRIVATE KEY-----")
        return "\n".join(lines)


def _format_public_key(key_str: str) -> str:
    """将公钥格式化为 PEM 格式"""
    key_str = key_str.strip()
    if key_str.startswith("-----"):
        return key_str
    lines = ["-----BEGIN PUBLIC KEY-----"]
    for i in range(0, len(key_str), 64):
        lines.append(key_str[i : i + 64])
    lines.append("-----END PUBLIC KEY-----")
    return "\n".join(lines)


def _get_alipay_client():
    """延迟初始化支付宝客户端（仅 sandbox 模式需要）"""
    global _alipay_client
    if _alipay_client is not None:
        return _alipay_client

    from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
    from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

    private_key = _format_private_key(settings.ALIPAY_PRIVATE_KEY)
    public_key = _format_public_key(settings.ALIPAY_PUBLIC_KEY)

    config = AlipayClientConfig()
    config.server_url = settings.ALIPAY_GATEWAY
    config.app_id = settings.ALIPAY_APP_ID
    config.app_private_key = private_key
    config.alipay_public_key = public_key
    config.sign_type = "RSA2"

    _alipay_client = DefaultAlipayClient(alipay_client_config=config)
    logger.info("支付宝沙箱客户端已初始化 app_id=%s", settings.ALIPAY_APP_ID)
    return _alipay_client


def _generate_out_trade_no() -> str:
    """生成商户订单号：YFT + 时间戳 + 随机后缀"""
    return f"YFT{int(time.time())}{uuid.uuid4().hex[:6].upper()}"


async def _get_register_fee(session: AsyncSession, reserve: ReserveModel) -> float:
    """通过 reserve -> schedule -> doctor 链路查询挂号费"""
    schedule = await schedule_repo.get_by_id(session, reserve.schedule_id)
    if not schedule:
        return 0.0
    doctor = await doctor_repo.get_by_id(session, schedule.doctor_id)
    if not doctor:
        return 0.0
    return float(doctor.register_fee) if doctor.register_fee else 0.0


async def create_payment(
    session: AsyncSession,
    req: CreatePaymentRequest,
    user_id: int,
) -> CreatePaymentResponse:
    """创建支付订单

    sandbox 模式：调用支付宝 trade_page_pay 接口，返回支付页面 URL
    mock 模式：直接更新订单状态，返回空 URL
    """
    # 1. 校验预约订单
    reserve = await reserve_repo.get_by_id(session, req.reserve_id)
    if not reserve or reserve.user_id != user_id:
        raise ValueError("预约订单不存在")
    if reserve.pay_status != 1:
        raise ValueError("订单状态异常，无法支付")

    # 2. 查询金额
    amount = await _get_register_fee(session, reserve)
    if amount <= 0:
        raise ValueError("挂号费查询失败")

    # 3. 检查是否已有进行中的支付记录
    out_trade_no = None
    existing = await pay_repo.get_by_reserve_id(session, req.reserve_id)
    if existing and existing.pay_status == 1:
        # 检查是否已超时（15 分钟）
        created = existing.create_time.replace(tzinfo=timezone.utc) if existing.create_time.tzinfo is None else existing.create_time
        elapsed = (datetime.now(timezone.utc) - created).total_seconds()
        if elapsed > 15 * 60:
            await pay_repo.mark_closed(session, existing.out_trade_no)
            raise ValueError("支付已超时，请重新预约")
        out_trade_no = existing.out_trade_no

    if not out_trade_no:
        # 生成新订单号
        out_trade_no = _generate_out_trade_no()
        await pay_repo.create_record(
            session, reserve_id=req.reserve_id,
            pay_money=amount, out_trade_no=out_trade_no,
            pay_channel="alipay" if settings.PAY_MODE == "sandbox" else "mock",
        )

    # 4. 根据模式处理
    pay_url = ""

    if settings.PAY_MODE == "sandbox" and settings.ALIPAY_APP_ID:
        # ── 沙箱模式：调用支付宝 API ──
        from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
        from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest

        client = _get_alipay_client()

        model = AlipayTradePagePayModel()
        model.out_trade_no = out_trade_no
        model.total_amount = str(amount)
        model.subject = f"YFT-Registration-{out_trade_no}"
        model.product_code = "FAST_INSTANT_TRADE_PAY"
        model.timeout_express = "15m"

        request = AlipayTradePagePayRequest(biz_model=model)
        request.notify_url = settings.ALIPAY_NOTIFY_URL
        request.return_url = settings.ALIPAY_RETURN_URL

        pay_url = client.page_execute(request, http_method="GET")
        if not pay_url:
            raise ValueError("支付宝返回的支付链接为空，请检查沙箱配置")
        logger.info("支付宝沙箱支付链接已生成 out_trade_no=%s amount=%.2f", out_trade_no, amount)
    else:
        # ── 模拟模式：直接完成支付 ──
        logger.info("模拟支付模式，直接完成 out_trade_no=%s", out_trade_no)
        await _complete_mock_payment(session, reserve, out_trade_no, amount)

    await session.commit()

    return CreatePaymentResponse(
        order_id=out_trade_no,
        pay_url=pay_url,
        amount=amount,
        pay_mode="sandbox" if pay_url else "mock",
    )


async def _complete_mock_payment(
    session: AsyncSession,
    reserve: ReserveModel,
    out_trade_no: str,
    amount: float,
) -> None:
    """模拟支付完成：更新订单状态 + 入候诊队列"""
    from app.queue.service import enqueue

    # 更新预约订单状态
    reserve.pay_status = 2
    reserve.order_status = 2
    reserve.queue_status = 1

    # 标记支付记录为已支付
    await pay_repo.mark_paid(session, out_trade_no, trade_no=f"MOCK_{out_trade_no}")

    # 入候诊队列（enqueue 接受 reserve_id, schedule_id, queue_code）
    try:
        queue_code = reserve.queue_code or f"Q{reserve.id}{int(time.time()) % 10000:04d}"
        await enqueue(reserve.id, reserve.schedule_id, queue_code)
    except Exception as e:
        logger.warning("模拟支付入队失败: %s", e)

    logger.info("模拟支付完成 out_trade_no=%s amount=%.2f", out_trade_no, amount)


async def handle_alipay_notify(session: AsyncSession, params: dict) -> bool:
    """处理支付宝异步通知

    Args:
        params: 支付宝 POST 过来的原始参数

    Returns:
        True 表示处理成功（返回 success 给支付宝），False 表示验签失败
    """
    # 1. 验签（fail-closed：仅 mock 模式跳过验证，其余一律校验）
    sign = params.get("sign", "")
    verify_params = {k: v for k, v in params.items() if k not in ("sign", "sign_type") and v}

    if settings.PAY_MODE == "mock":
        logger.info("Mock 模式，跳过验签")
    else:
        if not settings.ALIPAY_PUBLIC_KEY:
            logger.error("ALIPAY_PUBLIC_KEY 未配置，拒绝回调")
            return False

        from alipay.aop.api.util.SignatureUtils import verify_with_rsa

        sorted_params = sorted(verify_params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        try:
            is_valid = verify_with_rsa(settings.ALIPAY_PUBLIC_KEY.encode(), sign_str.encode(), sign)
            if not is_valid:
                logger.warning("支付宝回调验签失败")
                return False
        except Exception as e:
            logger.error("验签异常: %s", e)
            return False

    # 2. 提取关键字段
    out_trade_no = params.get("out_trade_no", "")
    trade_no = params.get("trade_no", "")
    trade_status = params.get("trade_status", "")

    logger.info("支付宝回调 out_trade_no=%s trade_status=%s", out_trade_no, trade_status)

    # 3. 根据交易状态处理
    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        record = await pay_repo.get_by_out_trade_no(session, out_trade_no)
        if not record:
            logger.warning("支付记录不存在: %s", out_trade_no)
            return False

        if record.pay_status == 2:
            return True  # 已支付，幂等返回

        # 标记支付记录为已支付（带 pay_status 守卫，防并发重复回调）
        rowcount = await pay_repo.mark_paid(session, out_trade_no, trade_no)
        if rowcount == 0:
            logger.info("并发回调命中幂等，跳过 out_trade_no=%s", out_trade_no)
            return True

        # 更新预约订单状态
        reserve = await reserve_repo.get_by_id(session, record.reserve_id)
        if reserve:
            reserve.pay_status = 2
            reserve.order_status = 2
            reserve.queue_status = 1

            from app.queue.service import enqueue
            try:
                queue_code = reserve.queue_code or f"Q{reserve.id}{int(time.time()) % 10000:04d}"
                await enqueue(reserve.id, reserve.schedule_id, queue_code)
            except Exception as e:
                logger.warning("回调入队失败: %s", e)

        await session.commit()
        logger.info("支付宝支付确认完成 out_trade_no=%s", out_trade_no)
        return True

    elif trade_status == "TRADE_CLOSED":
        await pay_repo.mark_closed(session, out_trade_no)
        await session.commit()
        return True

    return True


async def query_payment_result(
    session: AsyncSession,
    reserve_id: int,
    user_id: int,
) -> PaymentResultResponse:
    """查询支付结果（前端轮询用，需登录）"""
    reserve = await reserve_repo.get_by_id(session, reserve_id)
    if not reserve:
        raise ValueError("订单不存在")
    if reserve.user_id != user_id:
        raise PermissionError("无权查询此订单")

    record = await pay_repo.get_by_reserve_id(session, reserve_id)
    amount = float(record.pay_money) if record else 0.0
    pay_time = str(record.update_time) if record and record.pay_status == 2 else ""

    return PaymentResultResponse(
        reserve_id=reserve_id,
        pay_status=reserve.pay_status,
        order_status=reserve.order_status,
        amount=amount,
        pay_time=pay_time,
    )


async def query_payment_by_trade_no(
    session: AsyncSession,
    out_trade_no: str,
) -> PaymentResultResponse:
    """按商户订单号查询支付结果（支付宝回调跳转用，无需登录）"""
    record = await pay_repo.get_by_out_trade_no(session, out_trade_no)
    if not record:
        raise ValueError("订单不存在")

    reserve = await reserve_repo.get_by_id(session, record.reserve_id)
    if not reserve:
        raise ValueError("预约订单不存在")

    return PaymentResultResponse(
        reserve_id=reserve.id,
        pay_status=reserve.pay_status,
        order_status=reserve.order_status,
        amount=float(record.pay_money),
        pay_time=str(record.update_time) if record.pay_status == 2 else "",
    )


async def sync_payment_status(
    session: AsyncSession,
    out_trade_no: str,
) -> PaymentResultResponse:
    """主动同步支付宝支付状态（notify 回调未到达时的兜底方案）

    查询支付宝订单状态，若已支付则更新本地数据库。
    """
    record = await pay_repo.get_by_out_trade_no(session, out_trade_no)
    if not record:
        raise ValueError("订单不存在")

    reserve = await reserve_repo.get_by_id(session, record.reserve_id)
    if not reserve:
        raise ValueError("预约订单不存在")

    # 已经是支付成功状态，无需同步
    if record.pay_status == 2:
        return PaymentResultResponse(
            reserve_id=reserve.id,
            pay_status=reserve.pay_status,
            order_status=reserve.order_status,
            amount=float(record.pay_money),
            pay_time=str(record.update_time),
        )

    # 仅 sandbox 模式才主动查询支付宝
    if settings.PAY_MODE != "sandbox" or not settings.ALIPAY_APP_ID:
        raise ValueError("当前非沙箱模式，不支持主动同步")

    try:
        import json as _json
        client = _get_alipay_client()
        from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
        from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest

        model = AlipayTradeQueryModel()
        model.out_trade_no = out_trade_no
        request = AlipayTradeQueryRequest(biz_model=model)
        raw = client.execute(request)

        # SDK 可能返回 str 或 dict，统一处理
        if isinstance(raw, str):
            response = _json.loads(raw)
        else:
            response = raw

        # 响应可能嵌套在 alipay_trade_query_response 中
        if "alipay_trade_query_response" in response:
            response = response["alipay_trade_query_response"]

        trade_status = response.get("trade_status", "")
        trade_no = response.get("trade_no", "")
        logger.info("主动同步查询 out_trade_no=%s trade_status=%s resp=%s", out_trade_no, trade_status, response)

        if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            rowcount = await pay_repo.mark_paid(session, out_trade_no, trade_no)
            if rowcount > 0:
                reserve.pay_status = 2
                reserve.order_status = 2
                reserve.queue_status = 1

                from app.queue.service import enqueue
                try:
                    queue_code = reserve.queue_code or f"Q{reserve.id}{int(time.time()) % 10000:04d}"
                    await enqueue(reserve.id, reserve.schedule_id, queue_code)
                except Exception as e:
                    logger.warning("同步入队失败: %s", e)

                await session.commit()
                logger.info("主动同步支付成功 out_trade_no=%s", out_trade_no)
            else:
                logger.info("同步时已并发更新 out_trade_no=%s", out_trade_no)

        elif trade_status == "TRADE_CLOSED":
            await pay_repo.mark_closed(session, out_trade_no)
            await session.commit()

    except ValueError:
        raise
    except Exception as e:
        logger.error("主动同步支付宝状态异常: %s", e)
        raise ValueError(f"同步失败: {e}")

    # 重新查询最新状态
    reserve = await reserve_repo.get_by_id(session, record.reserve_id)
    record = await pay_repo.get_by_out_trade_no(session, out_trade_no)

    return PaymentResultResponse(
        reserve_id=reserve.id,
        pay_status=reserve.pay_status,
        order_status=reserve.order_status,
        amount=float(record.pay_money),
        pay_time=str(record.update_time) if record.pay_status == 2 else "",
    )
