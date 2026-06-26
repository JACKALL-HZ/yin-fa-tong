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
