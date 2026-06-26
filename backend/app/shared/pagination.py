"""分页工具"""

from math import ceil
from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """统一分页响应"""
    items: Sequence[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def of(cls, items: Sequence[T], total: int, page: int, page_size: int) -> "PageResponse":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0,
        )
