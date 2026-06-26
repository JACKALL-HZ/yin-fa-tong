"""统一响应结构"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    code: int = 200
    message: str = "ok"
    data: T | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "ok") -> "ApiResponse":
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 400, message: str = "请求错误") -> "ApiResponse":
        return cls(code=code, message=message, data=None)
