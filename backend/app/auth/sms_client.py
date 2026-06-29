"""阿里云号码认证服务客户端封装（短信验证码）"""

import random
import logging
from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
from alibabacloud_tea_util import models as util_models

from app.config import settings

logger = logging.getLogger(__name__)

# 全局客户端单例
_sms_client: DypnsapiClient | None = None


def _get_sms_client() -> DypnsapiClient:
    """获取阿里云号码认证客户端单例"""
    global _sms_client
    if _sms_client is not None:
        return _sms_client

    config = open_api_models.Config(
        access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
        access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
    )
    config.endpoint = "dypnsapi.aliyuncs.com"
    _sms_client = DypnsapiClient(config)
    return _sms_client


def generate_verify_code(length: int = 6) -> str:
    """生成指定长度的数字验证码"""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


async def send_sms_code(phone: str, code: str) -> bool:
    """
    发送短信验证码

    Args:
        phone: 手机号
        code: 验证码

    Returns:
        bool: 是否发送成功
    """
    client = _get_sms_client()

    request = dypnsapi_models.SendSmsVerifyCodeRequest(
        phone_number=phone,
        sign_name="速通互联验证码",
        template_code="100001",
        template_param=f'{{"code":"{code}","min":"5"}}',
    )

    runtime = util_models.RuntimeOptions()

    try:
        resp = await client.send_sms_verify_code_with_options_async(request, runtime)
        if resp.body.code == "OK":
            logger.info(f"短信发送成功: {phone}")
            return True
        else:
            logger.error(f"短信发送失败: {resp.body.message}")
            raise Exception(f"阿里云短信发送失败: {resp.body.message}")
    except Exception as e:
        logger.error(f"短信发送异常: {e}")
        raise
