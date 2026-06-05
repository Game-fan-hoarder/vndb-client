from __future__ import annotations


class VndbError(Exception):
    """Base class for every error raised by vndb-client."""


class VndbAPIError(VndbError):
    """The VNDB API returned an unsuccessful HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class VndbBadRequestError(VndbAPIError):
    """HTTP 400 — malformed request or invalid query."""


class VndbAuthError(VndbAPIError):
    """HTTP 401 — missing or invalid token."""


class VndbNotFoundError(VndbAPIError):
    """HTTP 404 — unknown path or method."""


class VndbRateLimitError(VndbAPIError):
    """HTTP 429 — rate limit exceeded."""


class VndbServerError(VndbAPIError):
    """HTTP 5xx — server-side failure."""


class VndbNetworkError(VndbError):
    """The underlying HTTP transport failed (connect/read/timeout)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VndbParseError(VndbError):
    """A response could not be parsed into the expected model."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
