from __future__ import annotations

from vndb_client.models import VndbModel


class Stats(VndbModel):
    """Database-wide counts from ``GET /stats``."""

    chars: int
    producers: int
    releases: int
    staff: int
    tags: int
    traits: int
    vn: int


class AuthInfo(VndbModel):
    """Token info from ``GET /authinfo``."""

    id: str
    username: str | None = None
    permissions: list[str] | None = None


class User(VndbModel):
    """A user record from ``GET /user``."""

    id: str
    username: str | None = None
    lengthvotes: int | None = None
    lengthvotes_sum: int | None = None


class UlistLabel(VndbModel):
    """A list label from ``GET /ulist_labels`` (``id`` is an integer)."""

    id: int
    label: str | None = None
    private: bool | None = None
    count: int | None = None
