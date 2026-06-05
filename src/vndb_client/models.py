from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class VndbModel(BaseModel):
    """Base for all VNDB response models.

    Allows population either by the API's response key (via per-field aliases on
    subclasses) or by the Python field name.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Page(BaseModel, Generic[T]):
    """The VNDB query response envelope."""

    results: list[T]
    more: bool = False
    count: int | None = None
    compact_filters: str | None = None
    normalized_filters: list[Any] | None = None
