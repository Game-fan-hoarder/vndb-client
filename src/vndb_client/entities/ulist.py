from __future__ import annotations

from enum import IntEnum

from vndb_client.models import VndbModel


class UnsetType:
    """Sentinel marking a PATCH field as 'not provided' (distinct from None=unset)."""

    def __repr__(self) -> str:
        return "UNSET"


UNSET = UnsetType()


class RListStatus(IntEnum):
    """Mirror of VNDB rlist ``status`` values (for comparison; not a field type)."""

    UNKNOWN = 0
    PENDING = 1
    OBTAINED = 2
    ON_LOAN = 3
    DELETED = 4


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
