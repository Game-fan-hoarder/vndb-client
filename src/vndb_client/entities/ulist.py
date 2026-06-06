from __future__ import annotations

from vndb_client.models import VndbModel


class UlistVN(VndbModel):
    """Minimal VN reference inside a ulist entry."""

    id: str
    title: str | None = None


class UlistEntryLabel(VndbModel):
    """A label on a ulist entry."""

    id: int
    label: str | None = None
    private: bool | None = None


class UlistEntry(VndbModel):
    """A user's list entry from ``POST /ulist``."""

    id: str
    added: int | None = None
    voted: int | None = None
    lastmod: int | None = None
    vote: int | None = None
    started: str | None = None
    finished: str | None = None
    notes: str | None = None
    labels: list[UlistEntryLabel] | None = None
    vn: UlistVN | None = None
