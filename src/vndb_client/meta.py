from __future__ import annotations

from typing import Any, TypeVar

from pydantic import ValidationError

from vndb_client.exceptions import VndbParseError
from vndb_client.models import VndbModel

_MetaT = TypeVar("_MetaT", bound=VndbModel)


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


def parse_one(model: type[_MetaT], raw: Any) -> _MetaT:
    """Validate ``raw`` into ``model``, surfacing a mismatch as ``VndbParseError``."""
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        raise VndbParseError(str(exc)) from exc


def parse_user_map(raw: Any) -> dict[str, User | None]:
    """Parse a ``GET /user`` response (a map of query -> user object or null)."""
    if not isinstance(raw, dict):
        msg = f"expected a user map, got {type(raw).__name__}"
        raise VndbParseError(msg)
    return {key: (parse_one(User, value) if value is not None else None) for key, value in raw.items()}


def parse_labels(raw: Any) -> list[UlistLabel]:
    """Parse a ``GET /ulist_labels`` response, unwrapping the ``labels`` array."""
    if not isinstance(raw, dict) or "labels" not in raw:
        msg = "missing 'labels' in ulist_labels response"
        raise VndbParseError(msg)
    return [parse_one(UlistLabel, item) for item in raw["labels"]]
