from __future__ import annotations

from enum import IntEnum

from vndb_client.entities.common import Image
from vndb_client.models import VndbModel


class DevStatus(IntEnum):
    """Mirror of VNDB ``devstatus`` values (for comparison; not a field type)."""

    FINISHED = 0
    IN_DEVELOPMENT = 1
    CANCELLED = 2


class VNLength(IntEnum):
    """Mirror of VNDB ``length`` values (for comparison; not a field type)."""

    VERY_SHORT = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    VERY_LONG = 5


class Title(VndbModel):
    lang: str
    title: str | None = None
    latin: str | None = None
    official: bool | None = None
    main: bool | None = None


class VN(VndbModel):
    id: str
    title: str | None = None
    alttitle: str | None = None
    titles: list[Title] | None = None
    aliases: list[str] | None = None
    olang: str | None = None
    devstatus: int | None = None
    released: str | None = None
    languages: list[str] | None = None
    platforms: list[str] | None = None
    image: Image | None = None
    length: int | None = None
    length_minutes: int | None = None
    length_votes: int | None = None
    description: str | None = None
    rating: float | None = None
    votecount: int | None = None
    average: float | None = None
