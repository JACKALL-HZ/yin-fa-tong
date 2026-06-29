"""认证模块 Pydantic 请求/响应模型"""

import re
from datetime import date
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=11, max_length=11, description="登录账号（11位手机号）")
    password: str = Field(min_length=6, max_length=32, description="登录密码")
    nickname: str = Field(default="用户", max_length=64, description="用户昵称")
    user_type: int = Field(default=1, ge=1, le=3, description="1老年用户 2子女用户 3管理员")
    admin_code: str | None = Field(default=None, description="管理员注册码（仅 user_type=3 时必填）")

    @field_validator("username")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"\d{11}", v):
            raise ValueError("手机号必须为11位数字")
        return v


class RegisterWithCodeRequest(BaseModel):
    """手机号+验证码注册"""
    phone: str = Field(min_length=11, max_length=11, description="手机号")
    code: str = Field(min_length=6, max_length=6, description="验证码")
    password: str = Field(min_length=6, max_length=32, description="登录密码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("验证码必须为6位数字")
        return v


class SendSmsCodeRequest(BaseModel):
    """发送短信验证码请求"""
    phone: str = Field(min_length=11, max_length=11, description="手机号")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v


class SmsLoginRequest(BaseModel):
    """手机号验证码登录请求"""
    phone: str = Field(min_length=11, max_length=11, description="手机号")
    code: str = Field(min_length=6, max_length=6, description="验证码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("验证码必须为6位数字")
        return v


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str = Field(description="管理员账号")
    password: str = Field(description="登录密码")


class LoginRequest(BaseModel):
    username: str = Field(description="登录账号")
    password: str = Field(description="登录密码")


class WxLoginRequest(BaseModel):
    """模拟微信授权登录"""
    wx_openid: str = Field(description="模拟微信 OpenID")
    nickname: str = Field(default="微信用户", description="用户昵称")


class AlipayLoginRequest(BaseModel):
    """支付宝 OAuth 授权登录"""
    auth_code: str = Field(description="支付宝授权码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    nickname: str
    user_type: int


class UserInfoResponse(BaseModel):
    id: int
    username: str | None
    nickname: str
    user_type: int
    wx_openid: str | None
    real_name: str | None = None
    gender: int | None = None
    id_card: str | None = None
    birthday: date | None = None
    phone: str | None = None
    profile_complete: bool = False
