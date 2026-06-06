from __future__ import annotations

from enum import Enum

from vndb_client.models import VndbModel


class ProducerType(str, Enum):
    """Mirror of VNDB producer ``type`` values (for comparison; not a field type)."""

    CO = "co"
    IN = "in"
    NG = "ng"


class Producer(VndbModel):
    id: str
    name: str | None = None
    original: str | None = None
    aliases: list[str] | None = None
    lang: str | None = None
    type: str | None = None
    description: str | None = None
