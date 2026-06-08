from __future__ import annotations

from dataclasses import dataclass, field

PROD_BASE_URL = "https://api.vndb.org/kana"
SANDBOX_BASE_URL = "https://beta.vndb.org/api/kana"

DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "vndb-client/1.0.0 (+https://github.com/Game-fan-hoarder/vndb-client)"


@dataclass(frozen=True)
class RetryConfig:
    """Bounds and timing for the retry policy."""

    max_attempts: int = 3
    backoff_base: float = 0.5
    backoff_cap: float = 10.0
    retry_statuses: frozenset[int] = field(default_factory=lambda: frozenset({429, 502, 503}))
