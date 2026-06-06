from __future__ import annotations

from vndb_client.models import VndbModel


class Trait(VndbModel):
    id: str
    name: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    searchable: bool | None = None
    applicable: bool | None = None
    sexual: bool | None = None
    group_id: str | None = None
    group_name: str | None = None
    char_count: int | None = None
