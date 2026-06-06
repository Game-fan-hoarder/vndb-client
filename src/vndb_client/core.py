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
