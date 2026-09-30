"""
统一响应体
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T = None


def ok(data: Any = None, message: str = "success") -> Response:
    return Response(code=0, message=message, data=data)
