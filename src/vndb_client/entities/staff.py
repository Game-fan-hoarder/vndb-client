from __future__ import annotations

from vndb_client.models import VndbModel


class StaffAlias(VndbModel):
    aid: int | None = None
    name: str | None = None
    latin: str | None = None
    ismain: bool | None = None


class Staff(VndbModel):
    id: str
    aid: int | None = None
    ismain: bool | None = None
    name: str | None = None
    original: str | None = None
    lang: str | None = None
    gender: str | None = None
    description: str | None = None
    aliases: list[StaffAlias] | None = None
