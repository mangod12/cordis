"""Standard API response envelope."""
from __future__ import annotations
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None
