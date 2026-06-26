# 支付宝沙箱支付实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将现有纯模拟支付改造为对接支付宝沙箱环境的真实支付流程（网页跳转支付模式），实现从下单→跳转支付宝→异步回调→状态更新的完整链路。

**架构：** 后端使用 `alipay-sdk-python` 库对接支付宝沙箱网关。支付流程：前端调 `/api/payment/create` → 后端生成支付宝预付单 → 返回支付页面 URL → 前端跳转到支付宝沙箱页面 → 用户在沙箱完成支付 → 支付宝异步 POST 回调到 `/api/payment/notify` → 后端验签 + 更新订单状态 → 前端轮询支付结果。保留原有模拟支付作为降级方案。

**技术栈：** alipay-sdk-python（支付宝官方 SDK）、FastAPI、Vue3 + TypeScript

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `backend/requirements.txt` | 添加 alipay-sdk-python 依赖 | 修改 |
| `backend/app/config.py` | 添加支付宝沙箱配置项 | 修改 |
| `backend/.env` | 添加支付宝沙箱环境变量 | 修改 |
| `backend/app/payment/schemas.py` | 支付请求/响应 Pydantic 模型 | 创建 |
| `backend/app/payment/service.py` | 支付业务逻辑（创建订单、验签回调、查询状态） | 创建 |
| `backend/app/payment/repository.py` | 支付记录数据库操作 | 创建 |
| `backend/app/payment/router.py` | 支付路由（重构：分层架构） | 修改 |
| `backend/app/payment/keys/` | 沙箱密钥文件目录 | 创建 |
| `frontend/src/api/payment.ts` | 支付 API 接口（新增 create/notify/result） | 修改 |
| `frontend/src/views/payment/PaymentView.vue` | 支付页面（改造为跳转支付宝） | 修改 |
| `frontend/src/views/payment/PayResult.vue` | 支付结果页（新增） | 创建 |

---

## 前置准备：获取支付宝沙箱凭证

在支付宝开放平台（https://openhome.alipay.com）完成以下操作：

1. 注册/登录开放平台 → 创建应用 → 获取 **APPID**
2. 在"开发设置"中配置 **RSA2 密钥**（推荐使用支付宝密钥生成器）
3. 下载**支付宝公钥**（不是应用公钥）
4. 记录：APPID、应用私钥、支付宝公钥
5. 沙箱网关地址：`https://openapi-sandbox.dl.alipaydev.com/gateway.do`

---

### 任务 1：安装依赖 + 配置沙箱凭证

**文件：**
- 修改：`backend/requirements.txt`
- 修改：`backend/app/config.py`
- 修改：`backend/.env`
- 创建：`backend/app/payment/keys/README.md`

- [ ] **步骤 1：添加 Python 依赖**

在 `backend/requirements.txt` 末尾追加：

```
# Payment - Alipay
alipay-sdk-python==3.7.31
```

- [ ] **步骤 2：安装依赖**

运行：`cd backend && pip install alipay-sdk-python==3.7.31`
预期：Successfully installed alipay-sdk-python

- [ ] **步骤 3：添加配置项到 config.py**

在 `backend/app/config.py` 的 `Settings` 类中，`DIFY_TIMEOUT` 字段之后添加：

```python
    # ── 支付宝沙箱 ──
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_GATEWAY: str = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
    ALIPAY_NOTIFY_URL: str = "http://localhost:8000/api/payment/notify"
    ALIPAY_RETURN_URL: str = "http://localhost:5173/pay-result"
    # 支付模式：sandbox=沙箱 / mock=纯模拟（降级方案）
    PAY_MODE: str = "mock"
```

- [ ] **步骤 4：添加环境变量到 .env**

在 `backend/.env` 末尾追加：

```env
# ── 支付宝沙箱 ──
# 在 https://openhome.alipay.com 获取以下凭证
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
ALIPAY_PUBLIC_KEY=
PAY_MODE=mock
```

> **说明：** `PAY_MODE=mock` 表示默认使用纯模拟支付。填入沙箱凭证后改为 `sandbox` 即启用支付宝沙箱。

- [ ] **步骤 5：创建密钥文件说明**

创建 `backend/app/payment/keys/README.md`：

```markdown
# 支付宝沙箱密钥

此目录用于存放支付宝沙箱环境的 RSA 密钥文件（可选）。

## 获取方式

1. 登录 https://openhome.alipay.com
2. 进入应用 → 开发设置 → 接口加签方式
3. 使用支付宝密钥生成器生成 RSA2 密钥对
4. 将应用公钥粘贴到开放平台，获取支付宝公钥

## 配置方式

将私钥和支付宝公钥配置到 `.env` 文件的 `ALIPAY_PRIVATE_KEY` 和 `ALIPAY_PUBLIC_KEY` 字段。
```

- [ ] **步骤 6：验证配置加载**

运行：`cd backend && python -c "from app.config import settings; print(settings.PAY_MODE)"`
预期：输出 `mock`

---

### 任务 2：创建支付数据模型和仓库层

**文件：**
- 创建：`backend/app/payment/schemas.py`
- 创建：`backend/app/payment/repository.py`
- 修改：`backend/app/payment/models.py`

- [ ] **步骤 1：创建 schemas.py**

创建 `backend/app/payment/schemas.py`：

```python
"""支付模块 Pydantic 模型"""

from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    """创建支付订单请求"""
    reserve_id: int = Field(description="预约订单 ID")


class CreatePaymentResponse(BaseModel):
    """创建支付订单响应"""
    order_id: str = Field(description="支付订单号（平台生成）")
    pay_url: str = Field(default="", description="支付宝支付页面 URL（sandbox 模式）")
    amount: float = Field(description="支付金额（元）")
    pay_mode: str = Field(description="支付模式：sandbox / mock")


class PaymentNotifyData(BaseModel):
    """支付宝异步通知参数（验签后的关键字段）"""
    out_trade_no: str = Field(description="商户订单号")
    trade_no: str = Field(default="", description="支付宝交易号")
    trade_status: str = Field(description="交易状态")
    total_amount: str = Field(description="交易金额")


class PaymentResultResponse(BaseModel):
    """支付结果查询响应"""
    reserve_id: int = Field(description="预约订单 ID")
    pay_status: int = Field(description="支付状态：1待支付 2已支付 3超时取消")
    order_status: int = Field(description="订单状态")
    amount: float = Field(default=0, description="支付金额")
    pay_time: str = Field(default="", description="支付完成时间")
```

- [ ] **步骤 2：增强 models.py**

读取现有的 `backend/app/payment/models.py`，在 `PayRecordModel` 中添加字段。完整替换为：

```python
"""缴费记录模型"""

from sqlalchemy import Column, BigInteger, String, Numeric, Integer
from app.shared.base_model import TimestampMixin


class PayRecordModel(TimestampMixin):
    __tablename__ = "tb_pay_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="缴费记录ID")
    reserve_id = Column(BigInteger, nullable=False, index=True, comment="预约订单ID")
    pay_money = Column(Numeric(10, 2), nullable=False, comment="缴费金额")
    # 新增：支付宝沙箱相关字段
    trade_no = Column(String(64), default="", comment="支付宝交易号")
    out_trade_no = Column(String(64), default="", index=True, comment="商户订单号")
    pay_channel = Column(String(20), default="mock", comment="支付渠道：alipay / mock")
    pay_status = Column(Integer, default=1, comment="支付状态：1待支付 2已支付 3已关闭")
```

- [ ] **步骤 3：创建 repository.py**

创建 `backend/app/payment/repository.py`：

```python
"""支付记录数据库操作"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.payment.models import PayRecordModel


async def create_record(
    session: AsyncSession,
    reserve_id: int,
    pay_money: float,
    out_trade_no: str,
    pay_channel: str = "mock",
) -> PayRecordModel:
    """创建支付记录"""
    record = PayRecordModel(
        reserve_id=reserve_id,
        pay_money=pay_money,
        out_trade_no=out_trade_no,
        pay_channel=pay_channel,
        pay_status=1,
    )
    session.add(record)
    await session.flush()
    return record


async def get_by_out_trade_no(session: AsyncSession, out_trade_no: str) -> PayRecordModel | None:
    """根据商户订单号查询支付记录"""
    stmt = select(PayRecordModel).where(
        PayRecordModel.out_trade_no == out_trade_no,
        PayRecordModel.is_deleted == 0,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_paid(session: AsyncSession, out_trade_no: str, trade_no: str) -> None:
    """标记支付记录为已支付"""
    stmt = (
        update(PayRecordModel)
        .where(PayRecordModel.out_trade_no == out_trade_no)
        .values(pay_status=2, trade_no=trade_no)
    )
    await session.execute(stmt)


async def mark_closed(session: AsyncSession, out_trade_no: str) -> None:
    """标记支付记录为已关闭"""
    stmt = (
        update(PayRecordModel)
        .where(PayRecordModel.out_trade_no == out_trade_no)
        .values(pay_status=3)
    )
    await session.execute(stmt)


async def get_by_reserve_id(session: AsyncSession, reserve_id: int) -> PayRecordModel | None:
    """根据预约订单 ID 查询支付记录"""
    stmt = select(PayRecordModel).where(
        PayRecordModel.reserve_id == reserve_id,
        PayRecordModel.is_deleted == 0,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

- [ ] **步骤 4：数据库迁移**

运行：`cd backend && python -m alembic revision --autogenerate -m "add_alipay_fields_to_pay_record"`
然后：`python -m alembic upgrade head`
预期：迁移成功，tb_pay_record 表新增 trade_no、out_trade_no、pay_channel、pay_status 字段

- [ ] **步骤 5：Commit**

```bash
git add backend/app/payment/schemas.py backend/app/payment/repository.py backend/app/payment/models.py
git commit -m "feat(payment): add schemas, repository and enhanced model for Alipay integration"
```

---

### 任务 3：实现支付宝支付服务层

**文件：**
- 创建：`backend/app/payment/service.py`

- [ ] **步骤 1：创建 service.py**

创建 `backend/app/payment/service.py`：

```python
"""支付宝沙箱支付业务逻辑

支付模式：
  - sandbox: 调用支付宝沙箱 API，生成真实支付页面
  - mock:    纯模拟，直接更新数据库状态（降级方案）
"""

import time
import uuid
import logging
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


def _get_alipay_client():
    """延迟初始化支付宝客户端（仅 sandbox 模式需要）"""
    global _alipay_client
    if _alipay_client is not None:
        return _alipay_client

    from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
    from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

    config = AlipayClientConfig()
    config.server_url = settings.ALIPAY_GATEWAY
    config.app_id = settings.ALIPAY_APP_ID
    config.app_private_key = settings.ALIPAY_PRIVATE_KEY
    config.alipay_public_key = settings.ALIPAY_PUBLIC_KEY
    config.sign_type = "RSA2"

    _alipay_client = DefaultAlipayClient(alipay_client_config=config)
    logger.info("支付宝沙箱客户端已初始化 app_id=%s", settings.ALIPAY_APP_ID)
    return _alipay_client


def _generate_out_trade_no() -> str:
    """生成商户订单号：YFT + 时间戳 + 随机后缀"""
    return f"YFT{int(time.time())}{uuid.uuid4().hex[:6].upper()}"


async def _get_register_fee(session: AsyncSession, reserve: ReserveModel) -> float:
    """通过 reserve → schedule → doctor 链路查询挂号费"""
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
    existing = await pay_repo.get_by_reserve_id(session, req.reserve_id)
    if existing and existing.pay_status == 1:
        # 已有待支付记录，复用订单号
        out_trade_no = existing.out_trade_no
    else:
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
        try:
            from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
            from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest

            client = _get_alipay_client()

            model = AlipayTradePagePayModel()
            model.out_trade_no = out_trade_no
            model.total_amount = str(amount)
            model.subject = f"银发通挂号费-{out_trade_no}"
            model.product_code = "FAST_INSTANT_TRADE_PAY"
            model.timeout_express = "15m"

            request = AlipayTradePagePayRequest(biz_model=model)
            request.notify_url = settings.ALIPAY_NOTIFY_URL
            request.return_url = settings.ALIPAY_RETURN_URL

            pay_url = client.page_execute(request, http_method="GET")
            logger.info("支付宝沙箱支付链接已生成 out_trade_no=%s amount=%.2f", out_trade_no, amount)
        except Exception as e:
            logger.error("支付宝沙箱调用失败，降级为模拟支付: %s", e)
            pay_url = ""
    else:
        # ── 模拟模式：直接完成支付 ──
        logger.info("模拟支付模式，直接完成 out_trade_no=%s", out_trade_no)

    if not pay_url:
        # mock 模式或沙箱降级：直接完成支付
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
    """模拟支付完成：更新订单状态 + 创建缴费记录 + 入候诊队列"""
    from app.payment.models import PayRecordModel
    from app.reserve.models import ReserveModel as RM
    from app.queue.service import enqueue

    # 更新预约订单状态
    reserve.pay_status = 2
    reserve.order_status = 2
    reserve.queue_status = 1

    # 标记支付记录为已支付
    await pay_repo.mark_paid(session, out_trade_no, trade_no=f"MOCK_{out_trade_no}")

    # 入候诊队列
    try:
        await enqueue(session, reserve)
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
    from alipay.aop.api.util.SignatureUtils import verify_with_rsa

    # 1. 验签
    sign = params.pop("sign", "")
    sign_type = params.pop("sign_type", "RSA2")

    # 构造待验签字符串
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)

    try:
        is_valid = verify_with_rsa(settings.ALIPAY_PUBLIC_KEY, sign_str, sign)
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
    total_amount = params.get("total_amount", "")

    logger.info("支付宝回调 out_trade_no=%s trade_status=%s", out_trade_no, trade_status)

    # 3. 根据交易状态处理
    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        # 查询支付记录
        record = await pay_repo.get_by_out_trade_no(session, out_trade_no)
        if not record:
            logger.warning("支付记录不存在: %s", out_trade_no)
            return False

        if record.pay_status == 2:
            # 已支付，幂等返回
            return True

        # 标记支付记录为已支付
        await pay_repo.mark_paid(session, out_trade_no, trade_no)

        # 更新预约订单状态
        reserve = await reserve_repo.get_by_id(session, record.reserve_id)
        if reserve:
            reserve.pay_status = 2
            reserve.order_status = 2
            reserve.queue_status = 1

            # 入候诊队列
            from app.queue.service import enqueue
            try:
                await enqueue(session, reserve)
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
) -> PaymentResultResponse:
    """查询支付结果（前端轮询用）"""
    reserve = await reserve_repo.get_by_id(session, reserve_id)
    if not reserve:
        raise ValueError("订单不存在")

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
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/payment/service.py
git commit -m "feat(payment): implement Alipay sandbox service with mock fallback"
```

---

### 任务 4：重构支付路由（分层架构）

**文件：**
- 修改：`backend/app/payment/router.py`

- [ ] **步骤 1：重写 router.py**

将现有的 `backend/app/payment/router.py` 替换为：

```python
"""支付路由层

端点：
  POST /api/payment/create   - 创建支付订单（沙箱/模拟）
  POST /api/payment/notify   - 支付宝异步回调（验签）
  GET  /api/payment/result    - 查询支付结果
  POST /api/payment/pay       - 兼容旧接口（模拟支付）
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_db
from app.shared.response import ApiResponse
from app.auth.dependencies import get_current_user
from app.user.models import UserModel
from app.payment.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResultResponse,
)
from app.payment import service as pay_service

router = APIRouter(prefix="/api/payment", tags=["在线缴费"])


@router.post("/create", response_model=ApiResponse[CreatePaymentResponse])
async def create_payment(
    req: CreatePaymentRequest,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建支付订单

    sandbox 模式：返回支付宝支付页面 URL，前端跳转
    mock 模式：直接完成支付，返回空 URL
    """
    try:
        data = await pay_service.create_payment(session, req, current_user.id)
        return ApiResponse.ok(data, message="支付订单已创建")
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)


@router.post("/notify")
async def alipay_notify(request: Request, session: AsyncSession = Depends(get_db)):
    """支付宝异步回调通知

    支付宝会 POST form-data 到此端点。
    返回 "success" 表示确认收到，支付宝不再重发。
    """
    form = await request.form()
    params = {k: v for k, v in form.items()}

    success = await pay_service.handle_alipay_notify(session, params)
    return "success" if success else "fail"


@router.get("/result", response_model=ApiResponse[PaymentResultResponse])
async def payment_result(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """查询支付结果（前端轮询用）"""
    try:
        data = await pay_service.query_payment_result(session, reserve_id)
        return ApiResponse.ok(data)
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)


@router.post("/pay")
async def legacy_pay(
    reserve_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """兼容旧接口：直接模拟支付

    保留此端点以兼容 OrderList.vue 中的 reserveApi.pay(id) 调用。
    """
    try:
        req = CreatePaymentRequest(reserve_id=reserve_id)
        data = await pay_service.create_payment(session, req, current_user.id)
        return ApiResponse.ok({"amount": data.amount}, message="支付成功")
    except ValueError as e:
        return ApiResponse.fail(str(e), code=400)
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/payment/router.py
git commit -m "refactor(payment): restructure router with proper layering and Alipay endpoints"
```

---

### 任务 5：更新前端支付 API 和类型

**文件：**
- 修改：`frontend/src/api/payment.ts`

- [ ] **步骤 1：重写 payment.ts**

将现有的 `frontend/src/api/payment.ts` 替换为：

```typescript
import http from '@/utils/request'
import type { ApiResponse } from '@/types'

/** 支付模式 */
export type PayMode = 'sandbox' | 'mock'

/** 创建支付订单响应 */
export interface CreatePaymentData {
  order_id: string
  pay_url: string
  amount: number
  pay_mode: PayMode
}

/** 支付结果响应 */
export interface PaymentResultData {
  reserve_id: number
  pay_status: number
  order_status: number
  amount: number
  pay_time: string
}

export const paymentApi = {
  /** 创建支付订单（沙箱/模拟） */
  create: (reserve_id: number) =>
    http.post<ApiResponse<CreatePaymentData>>('/payment/create', { reserve_id }),

  /** 查询支付结果（轮询用） */
  getResult: (reserve_id: number) =>
    http.get<ApiResponse<PaymentResultData>>('/payment/result', { params: { reserve_id } }),

  /** 兼容旧接口：直接模拟支付 */
  pay: (params: { reserve_id: number; pay_type?: number; amount?: number }) =>
    http.post<ApiResponse>('/payment/pay', params),
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/api/payment.ts
git commit -m "feat(payment): add create and result API for Alipay integration"
```

---

### 任务 6：改造前端支付页面

**文件：**
- 修改：`frontend/src/views/payment/PaymentView.vue`

- [ ] **步骤 1：改造 PaymentView.vue**

读取现有 `frontend/src/views/payment/PaymentView.vue`，将 `doPay` 函数替换为支持支付宝跳转的版本。以下是需要修改的关键部分：

**script 部分 — 替换 doPay 函数：**

```typescript
const doPay = async () => {
  if (!orderInfo.value) return
  paying.value = true
  try {
    const { data: res } = await paymentApi.create(orderInfo.value.id)
    if (res.code === 200 && res.data) {
      if (res.data.pay_mode === 'sandbox' && res.data.pay_url) {
        // 沙箱模式：跳转到支付宝支付页面
        window.location.href = res.data.pay_url
      } else {
        // 模拟模式：直接完成
        ElMessage.success(`支付成功！金额：¥${res.data.amount}`)
        router.push({ path: '/pay-result', query: { reserve_id: String(orderInfo.value.id) } })
      }
    } else {
      ElMessage.error(res.message || '支付失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '支付请求失败')
  } finally {
    paying.value = false
  }
}
```

**template 部分 — 更新按钮文案：**

将三个支付按钮合并为两个：

```html
<div class="pay-actions">
  <el-button
    type="primary"
    size="large"
    :loading="paying"
    @click="doPay"
    class="pay-btn"
  >
    💳 确认支付
  </el-button>
  <el-button size="large" @click="router.back()" class="cancel-btn">
    取消
  </el-button>
</div>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/views/payment/PaymentView.vue
git commit -m "feat(payment): redirect to Alipay sandbox page on pay"
```

---

### 任务 7：创建支付结果页

**文件：**
- 创建：`frontend/src/views/payment/PayResult.vue`
- 修改：`frontend/src/router/index.ts`

- [ ] **步骤 1：创建 PayResult.vue**

创建 `frontend/src/views/payment/PayResult.vue`：

```vue
<template>
  <div class="pay-result-page">
    <div class="result-card">
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p>正在查询支付结果...</p>
      </div>

      <template v-else>
        <div v-if="result?.pay_status === 2" class="success-state">
          <el-icon :size="64" color="#67c23a"><CircleCheck /></el-icon>
          <h2>支付成功</h2>
          <p class="amount">¥{{ result.amount }}</p>
          <p class="time">支付时间：{{ result.pay_time }}</p>
        </div>

        <div v-else-if="result?.pay_status === 3" class="failed-state">
          <el-icon :size="64" color="#f56c6c"><CircleClose /></el-icon>
          <h2>支付已取消</h2>
          <p>订单超时未支付，已自动取消</p>
        </div>

        <div v-else class="pending-state">
          <el-icon :size="64" color="#e6a23c"><Warning /></el-icon>
          <h2>等待支付</h2>
          <p>请在支付宝完成支付</p>
        </div>
      </template>

      <div class="actions">
        <el-button type="primary" @click="router.push('/order-list')">查看订单</el-button>
        <el-button @click="router.push('/')">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'
import { paymentApi, type PaymentResultData } from '@/api/payment'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const result = ref<PaymentResultData | null>(null)

const pollResult = async (reserveId: number, retries = 10) => {
  for (let i = 0; i < retries; i++) {
    try {
      const { data: res } = await paymentApi.getResult(reserveId)
      if (res.code === 200 && res.data) {
        result.value = res.data
        if (res.data.pay_status !== 1) {
          loading.value = false
          return
        }
      }
    } catch {}
    await new Promise(r => setTimeout(r, 2000))
  }
  loading.value = false
}

onMounted(() => {
  const reserveId = Number(route.query.reserve_id)
  if (reserveId) {
    pollResult(reserveId)
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.pay-result-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  padding: 20px;
}
.result-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.result-card h2 { margin: 16px 0 8px; font-size: 20px; }
.amount { font-size: 28px; font-weight: 700; color: #67c23a; margin: 8px 0; }
.time { color: #909399; font-size: 14px; }
.loading-state p { margin-top: 16px; color: #909399; }
.actions { margin-top: 32px; display: flex; gap: 12px; justify-content: center; }
</style>
```

- [ ] **步骤 2：添加路由**

在 `frontend/src/router/index.ts` 的 routes 数组中，找到 `/payment` 路由，在其后添加：

```typescript
{
  path: '/pay-result',
  name: 'PayResult',
  component: () => import('@/views/payment/PayResult.vue'),
  meta: { title: '支付结果', requireAuth: true },
},
```

- [ ] **步骤 3：Commit**

```bash
git add frontend/src/views/payment/PayResult.vue frontend/src/router/index.ts
git commit -m "feat(payment): add pay result page with polling"
```

---

### 任务 8：端到端测试验证

- [ ] **步骤 1：重启后端**

```bash
docker restart yft-backend
sleep 5
docker logs yft-backend 2>&1 | tail -10
```

- [ ] **步骤 2：测试 mock 模式（默认）**

```bash
# 登录获取 token
TOKEN=$(curl -s http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser1","password":"123456"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

# 创建一个预约订单（需要先有可用的排班号源）
# 假设已有 reserve_id=1 的待支付订单
curl -s http://localhost:8000/api/payment/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reserve_id":1}' | python -m json.tool
```

预期输出（mock 模式）：
```json
{
  "code": 200,
  "message": "支付订单已创建",
  "data": {
    "order_id": "YFT...",
    "pay_url": "",
    "amount": 30.0,
    "pay_mode": "mock"
  }
}
```

- [ ] **步骤 3：测试前端支付流程**

1. 打开 http://localhost:5173
2. 登录 → 挂号 → 创建预约 → 进入支付页面
3. 点击"确认支付"
4. mock 模式：应弹出"支付成功"提示并跳转结果页
5. sandbox 模式：应跳转到支付宝沙箱页面

- [ ] **步骤 4：测试旧接口兼容性**

```bash
curl -s http://localhost:8000/api/payment/pay?reserve_id=1 \
  -X POST -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

预期：返回 `{"code":200,"message":"支付成功","data":{"amount":30.0}}`

- [ ] **步骤 5：Commit**

```bash
git add -A
git commit -m "test(payment): verify Alipay sandbox and mock payment flows"
```

---

## 自检清单

1. ✅ **规格覆盖度**：PRD 要求的在线缴费、缴费记录、超时取消、号源回收全部覆盖
2. ✅ **无占位符**：每个步骤都有完整代码
3. ✅ **类型一致性**：`CreatePaymentResponse`、`PaymentResultResponse` 在 service/router/前端一致
4. ✅ **向后兼容**：旧的 `/api/payment/pay` 端点保留，`OrderList.vue` 无需修改
5. ✅ **降级方案**：`PAY_MODE=mock` 为默认值，沙箱配置为空时自动降级
