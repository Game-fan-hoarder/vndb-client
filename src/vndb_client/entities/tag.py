from __future__ import annotations

from enum import Enum

from vndb_client.models import VndbModel


class TagCategory(str, Enum):
    """Mirror of VNDB tag ``category`` values (for comparison; not a field type)."""

    CONT = "cont"
    ERO = "ero"
    TECH = "tech"


class Tag(VndbModel):
    id: str
    name: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    category: str | None = None
    searchable: bool | None = None
    applicable: bool | None = None
    vn_count: int | None = None
