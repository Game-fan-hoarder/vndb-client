from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from vndb_client.config import RetryConfig
from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)
from vndb_client.models import Page

ModelT = TypeVar("ModelT", bound=BaseModel)

_STATUS_EXCEPTIONS: dict[int, type[VndbAPIError]] = {
    400: VndbBadRequestError,
    401: VndbAuthError,
    404: VndbNotFoundError,
    429: VndbRateLimitError,
}


@dataclass(frozen=True)
class RequestSpec:
    """A fully-described HTTP request, independent of any HTTP client."""

    method: str
    path: str
    json: dict[str, Any] | None = None
    params: dict[str, Any] | None = None


def build_query_request(
    endpoint: str,
    *,
    filters: Any = None,
    fields: str | None = None,
    sort: str | None = None,
    reverse: bool | None = None,
    results: int | None = None,
    page: int | None = None,
    count: bool | None = None,
    user: str | None = None,
    compact_filters: bool | None = None,
    normalized_filters: bool | None = None,
) -> RequestSpec:
    """Serialize the standard VNDB query parameters into a POST request spec."""
    candidates: dict[str, Any] = {
        "filters": filters,
        "fields": fields,
        "sort": sort,
        "reverse": reverse,
        "results": results,
        "page": page,
        "count": count,
        "user": user,
        "compact_filters": compact_filters,
        "normalized_filters": normalized_filters,
    }
    body = {k: v for k, v in candidates.items() if v is not None}
    return RequestSpec(method="POST", path=f"/{endpoint.lstrip('/')}", json=body)


def raise_for_status(status: int, body: str) -> None:
    """Raise the mapped exception for a non-2xx status; no-op below 400."""
    if status < 400:
        return
    exc_type = _STATUS_EXCEPTIONS.get(status)
    if exc_type is None:
        exc_type = VndbServerError if status >= 500 else VndbAPIError
    raise exc_type(status_code=status, message=body.strip())


def decode_json(response: Any) -> Any:
    """Decode a response body as JSON, raising :class:`VndbParseError` on malformed bodies."""
    try:
        return response.json()
    except ValueError as exc:
        raise VndbParseError(str(exc)) from exc


def parse_page(raw: dict[str, Any], model: type[ModelT]) -> Page[ModelT]:
    """Parse a raw response envelope into a typed ``Page[model]``."""
    page_type = Page[model]  # type: ignore[valid-type]
    try:
        validated = page_type.model_validate(raw)
    except ValidationError as exc:
        raise VndbParseError(str(exc)) from exc
    return cast("Page[ModelT]", validated)


@dataclass(frozen=True)
class RetryPolicy:
    """Pure retry decision: no I/O, no clock."""

    config: RetryConfig

    def next(
        self,
        attempt: int,
        status: int | None,
        exc: Exception | None,
        retry_after: float | None = None,
    ) -> tuple[bool, float]:
        """Decide whether to retry after ``attempt`` tries, and how long to wait.

        ``attempt`` is the number of attempts already made (>= 1).
        """
        if attempt >= self.config.max_attempts:
            return (False, 0.0)
        retryable = exc is not None or (status is not None and status in self.config.retry_statuses)
        if not retryable:
            return (False, 0.0)
        if retry_after is not None:
            delay = retry_after
        else:
            delay = min(self.config.backoff_base * (2 ** (attempt - 1)), self.config.backoff_cap)
        return (True, delay)


@dataclass(frozen=True)
class PageWalk:
    """Pure pagination decision: no I/O, no transport.

    Owns the two questions a paginated walk has to answer — how much of a page
    to keep, and whether to ask for another one — so the sync and async
    generators contain only request-and-yield scaffolding.

    In both methods ``yielded`` is the number of records this walk has already
    emitted, and ``available`` is the record count the API returned for the
    current page, *before* any truncation.

    Args:
        start_page: 1-based page number the walk begins at.
        limit: Maximum number of records the walk may emit in total, or
            ``None`` for an unbounded walk.

    Raises:
        ValueError: If ``start_page`` is below 1, or ``limit`` is not positive.
    """

    start_page: int = 1
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.start_page < 1:
            msg = f"start_page must be >= 1, got {self.start_page}"
            raise ValueError(msg)
        if self.limit is not None and self.limit <= 0:
            msg = f"limit must be positive, got {self.limit}"
            raise ValueError(msg)

    def take(self, yielded: int, available: int) -> int:
        """Return how many of this page's records to keep within the record budget."""
        if self.limit is None:
            return available
        return min(available, max(self.limit - yielded, 0))

    def should_continue(self, *, more: bool, yielded: int, available: int) -> bool:
        """Return whether to request another page.

        Stops when the API reports no further pages, when the record budget is
        spent, or when a page came back empty while still claiming more pages —
        the last guard is what keeps a misreporting server from driving an
        unbounded request loop.
        """
        if not more or available == 0:
            return False
        return self.limit is None or yielded < self.limit
