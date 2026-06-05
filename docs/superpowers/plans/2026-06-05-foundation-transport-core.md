# Foundation Transport Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the sync + async HTTP foundation for the VNDB Kana client — transport, a sans-I/O core, an exception hierarchy, and a generic `Page[T]` envelope — with an internal generic query primitive proven end-to-end against a mocked transport.

**Architecture:** A sans-I/O `core` builds request specs and parses responses into typed models with no I/O. Two thin transports (`SyncTransport`/`AsyncTransport`) execute via httpx and drive a retry loop whose *decision* is a pure function in core. `Client`/`AsyncClient` wrap a transport and expose an internal generic `_query`. Public entity resources are out of scope (later epics).

**Tech Stack:** Python 3.10–3.14, httpx, Pydantic v2, pytest (async via `asyncio.run`, no extra plugin), uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/foundation-transport-core/` (proposal, design, specs, tasks). **Design:** `docs/2026-06-05_foundation_design.md`.

**Conventions for every commit in this plan:**
- Run from the worktree root: `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\foundation-transport-core`.
- Use `uv run python -m pytest ...` (the worktree has its own `.venv`; `uv run` targets it).
- End each commit message with the trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```
- All new modules begin with `from __future__ import annotations`.

---

## Task 1: Dependencies & scaffolding cleanup

**Files:**
- Modify: `pyproject.toml` (add `[project].dependencies`)
- Delete: `src/vndb_client/foo.py`, `tests/test_foo.py`

- [ ] **Step 1: Add runtime dependencies to `pyproject.toml`**

Insert a `dependencies` array into the `[project]` table (immediately after the `classifiers = [...]` block, before `[project.urls]`):

```toml
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.7",
]
```

- [ ] **Step 2: Lock and sync**

Run: `uv lock` then `uv sync`
Expected: lock file updates; `httpx` and `pydantic` resolve and install into `.venv`.

- [ ] **Step 3: Remove placeholder module and its test**

Run:
```bash
git rm src/vndb_client/foo.py tests/test_foo.py
```
Expected: both files deleted.

- [ ] **Step 4: Verify the suite still collects (0 tests is OK)**

Run: `uv run python -m pytest`
Expected: `no tests ran` (exit code 5) — acceptable; the placeholder is gone and no tests exist yet.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/vndb_client/foo.py tests/test_foo.py
git commit -m "chore(foundation): add httpx + pydantic deps, drop placeholder foo

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Exception hierarchy

**Files:**
- Create: `src/vndb_client/exceptions.py`
- Test: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing test**

`tests/test_exceptions.py`:
```python
from __future__ import annotations

import pytest

from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbError,
    VndbNetworkError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)


@pytest.mark.parametrize(
    "exc_type",
    [
        VndbBadRequestError,
        VndbAuthError,
        VndbNotFoundError,
        VndbRateLimitError,
        VndbServerError,
    ],
)
def test_api_errors_are_vndb_errors_and_carry_status_and_message(exc_type):
    err = exc_type(status_code=418, message="teapot")
    assert isinstance(err, VndbError)
    assert isinstance(err, VndbAPIError)
    assert err.status_code == 418
    assert err.message == "teapot"
    assert "418" in str(err)
    assert "teapot" in str(err)


def test_network_error_is_vndb_error_and_chains_cause():
    original = ConnectionError("boom")
    err = VndbNetworkError("connect failed")
    assert isinstance(err, VndbError)
    assert err.message == "connect failed"
    # chaining is done at raise sites via `raise ... from`
    err.__cause__ = original
    assert err.__cause__ is original


def test_parse_error_is_vndb_error():
    err = VndbParseError("bad shape")
    assert isinstance(err, VndbError)
    assert err.message == "bad shape"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_exceptions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.exceptions'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/exceptions.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_exceptions.py -v`
Expected: PASS (all parametrized cases + network + parse).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/exceptions.py tests/test_exceptions.py
git commit -m "feat(foundation): add exception hierarchy

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Response models — `VndbModel` and generic `Page[T]`

**Files:**
- Create: `src/vndb_client/models.py`
- Test: `tests/test_models.py`

**Design note:** VNDB response keys are snake_case/lowercase, so we do **not** impose a camelCase alias generator. `VndbModel` enables `populate_by_name` so subclasses can declare per-field `Field(alias=...)` where an API key differs from a valid Python identifier, while still allowing construction by field name.

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
from __future__ import annotations

from pydantic import Field

from vndb_client.models import Page, VndbModel


class _Dummy(VndbModel):
    id: str
    title: str | None = None
    dev_status: int | None = Field(default=None, alias="devstatus")


def test_vndbmodel_populates_from_api_alias():
    obj = _Dummy.model_validate({"id": "v17", "devstatus": 0})
    assert obj.id == "v17"
    assert obj.dev_status == 0


def test_vndbmodel_populates_by_field_name():
    obj = _Dummy(id="v17", dev_status=2)
    assert obj.dev_status == 2


def test_page_parses_results_more_and_count():
    page = Page[_Dummy].model_validate(
        {"results": [{"id": "v1"}, {"id": "v2"}], "more": True, "count": 2}
    )
    assert page.more is True
    assert page.count == 2
    assert [r.id for r in page.results] == ["v1", "v2"]
    assert all(isinstance(r, _Dummy) for r in page.results)


def test_page_count_defaults_to_none():
    page = Page[_Dummy].model_validate({"results": [], "more": False})
    assert page.count is None
    assert page.compact_filters is None
    assert page.normalized_filters is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.models'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/models.py`:
```python
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class VndbModel(BaseModel):
    """Base for all VNDB response models.

    Allows population either by the API's response key (via per-field aliases on
    subclasses) or by the Python field name.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Page(BaseModel, Generic[T]):
    """The VNDB query response envelope."""

    results: list[T]
    more: bool = False
    count: int | None = None
    compact_filters: str | None = None
    normalized_filters: list[Any] | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_models.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/models.py tests/test_models.py
git commit -m "feat(foundation): add VndbModel base and generic Page[T] envelope

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Configuration constants and `RetryConfig`

**Files:**
- Create: `src/vndb_client/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
from __future__ import annotations

from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    SANDBOX_BASE_URL,
    RetryConfig,
)


def test_base_urls():
    assert PROD_BASE_URL == "https://api.vndb.org/kana"
    assert SANDBOX_BASE_URL == "https://beta.vndb.org/api/kana"


def test_defaults_present():
    assert DEFAULT_TIMEOUT > 0
    assert "vndb-client" in DEFAULT_USER_AGENT


def test_retry_config_defaults_and_immutability():
    cfg = RetryConfig()
    assert cfg.max_attempts == 3
    assert cfg.backoff_base > 0
    assert cfg.backoff_cap >= cfg.backoff_base
    assert 429 in cfg.retry_statuses
    assert 502 in cfg.retry_statuses
    assert 503 in cfg.retry_statuses
    assert 500 not in cfg.retry_statuses
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.config'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/config.py`:
```python
from __future__ import annotations

from dataclasses import dataclass, field

PROD_BASE_URL = "https://api.vndb.org/kana"
SANDBOX_BASE_URL = "https://beta.vndb.org/api/kana"

DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "vndb-client/0.0.1 (+https://github.com/HOZHENWAI/vndb-client)"


@dataclass(frozen=True)
class RetryConfig:
    """Bounds and timing for the retry policy."""

    max_attempts: int = 3
    backoff_base: float = 0.5
    backoff_cap: float = 10.0
    retry_statuses: frozenset[int] = field(default_factory=lambda: frozenset({429, 502, 503}))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/config.py tests/test_config.py
git commit -m "feat(foundation): add config constants and RetryConfig

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Sans-I/O core

**Files:**
- Create: `src/vndb_client/core.py`
- Test: `tests/test_core.py`

This task has four independently-testable pieces. Build them in sub-steps, committing once at the end.

- [ ] **Step 1: Write the failing tests**

`tests/test_core.py`:
```python
from __future__ import annotations

import httpx
import pytest

from vndb_client import core
from vndb_client.config import RetryConfig
from vndb_client.core import RequestSpec, RetryPolicy
from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)
from vndb_client.models import Page, VndbModel


class _Dummy(VndbModel):
    id: str


# --- build_query_request ---

def test_build_query_request_includes_only_provided_fields():
    spec = core.build_query_request("vn", filters=["id", "=", "v17"], fields="id,title", results=5)
    assert isinstance(spec, RequestSpec)
    assert spec.method == "POST"
    assert spec.path == "/vn"
    assert spec.json == {"filters": ["id", "=", "v17"], "fields": "id,title", "results": 5}


def test_build_query_request_normalizes_leading_slash():
    spec = core.build_query_request("/vn", count=True)
    assert spec.path == "/vn"
    assert spec.json == {"count": True}


# --- raise_for_status ---

@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (400, VndbBadRequestError),
        (401, VndbAuthError),
        (404, VndbNotFoundError),
        (429, VndbRateLimitError),
        (500, VndbServerError),
        (502, VndbServerError),
        (418, VndbAPIError),
    ],
)
def test_raise_for_status_maps_codes(status, exc_type):
    with pytest.raises(exc_type) as info:
        core.raise_for_status(status, "  body text  ")
    assert info.value.status_code == status
    assert info.value.message == "body text"


def test_raise_for_status_noop_below_400():
    assert core.raise_for_status(200, "ok") is None


# --- RetryPolicy.next ---

def _policy():
    return RetryPolicy(RetryConfig(max_attempts=3, backoff_base=0.5, backoff_cap=10.0))


def test_retry_on_429_without_retry_after_uses_exponential_backoff():
    retry, delay = _policy().next(attempt=1, status=429, exc=None)
    assert retry is True
    assert delay == pytest.approx(0.5)  # base * 2**(1-1)
    retry2, delay2 = _policy().next(attempt=2, status=429, exc=None)
    assert retry2 is True
    assert delay2 == pytest.approx(1.0)  # base * 2**(2-1)


def test_retry_on_429_honors_retry_after():
    retry, delay = _policy().next(attempt=1, status=429, exc=None, retry_after=7.0)
    assert retry is True
    assert delay == pytest.approx(7.0)


def test_retry_on_transient_5xx_and_network():
    assert _policy().next(attempt=1, status=502, exc=None)[0] is True
    assert _policy().next(attempt=1, status=None, exc=httpx.ConnectError("x"))[0] is True


def test_no_retry_on_client_errors():
    for status in (400, 401, 404, 500):
        assert _policy().next(attempt=1, status=status, exc=None)[0] is False


def test_no_retry_when_attempts_exhausted():
    retry, delay = _policy().next(attempt=3, status=429, exc=None)
    assert retry is False
    assert delay == 0.0


def test_backoff_is_capped():
    cfg = RetryConfig(max_attempts=99, backoff_base=1.0, backoff_cap=4.0)
    retry, delay = RetryPolicy(cfg).next(attempt=10, status=429, exc=None)
    assert retry is True
    assert delay == pytest.approx(4.0)


# --- parse_page ---

def test_parse_page_returns_typed_page():
    page = core.parse_page({"results": [{"id": "v1"}], "more": False}, _Dummy)
    assert isinstance(page, Page)
    assert page.results[0].id == "v1"


def test_parse_page_wraps_validation_error():
    with pytest.raises(VndbParseError):
        core.parse_page({"results": [{"wrong": "shape"}], "more": False}, _Dummy)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_core.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.core'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/core.py`:
```python
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
) -> RequestSpec:
    """Serialize the standard VNDB query parameters into a POST request spec."""
    body: dict[str, Any] = {}
    if filters is not None:
        body["filters"] = filters
    if fields is not None:
        body["fields"] = fields
    if sort is not None:
        body["sort"] = sort
    if reverse is not None:
        body["reverse"] = reverse
    if results is not None:
        body["results"] = results
    if page is not None:
        body["page"] = page
    if count is not None:
        body["count"] = count
    if user is not None:
        body["user"] = user
    return RequestSpec(method="POST", path=f"/{endpoint.lstrip('/')}", json=body)


def raise_for_status(status: int, body: str) -> None:
    """Raise the mapped exception for a non-2xx status; no-op below 400."""
    if status < 400:
        return
    exc_type = _STATUS_EXCEPTIONS.get(status)
    if exc_type is None:
        exc_type = VndbServerError if status >= 500 else VndbAPIError
    raise exc_type(status_code=status, message=body.strip())


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
        if status == 429 and retry_after is not None:
            delay = retry_after
        else:
            delay = min(self.config.backoff_base * (2 ** (attempt - 1)), self.config.backoff_cap)
        return (True, delay)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_core.py -v`
Expected: PASS (all build/raise/retry/parse cases).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/core.py tests/test_core.py
git commit -m "feat(foundation): add sans-I/O core (request build, status map, retry policy, parse)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Transports (sync + async) with mocked I/O

**Files:**
- Create: `src/vndb_client/_transport.py`
- Test: `tests/test_transport.py`

**Test approach:** Inject an `httpx.Client`/`AsyncClient` built with `httpx.MockTransport(handler)` and a `base_url`. Patch the module-level sleep functions so retries don't wait. Async tests run via `asyncio.run`, avoiding any pytest async plugin.

- [ ] **Step 1: Write the failing test**

`tests/test_transport.py`:
```python
from __future__ import annotations

import asyncio

import httpx
import pytest

from vndb_client import _transport
from vndb_client.config import PROD_BASE_URL, RetryConfig
from vndb_client.core import RequestSpec
from vndb_client.exceptions import VndbNetworkError, VndbRateLimitError
from vndb_client._transport import AsyncTransport, SyncTransport


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(_transport, "_sleep", lambda seconds: None)

    async def _anoop(seconds):
        return None

    monkeypatch.setattr(_transport, "_asleep", _anoop)


def _mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _mock_async_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


SPEC = RequestSpec(method="POST", path="/vn", json={"fields": "id"})


def test_sync_success_returns_response():
    def handler(request):
        return httpx.Response(200, json={"results": [], "more": False})

    transport = SyncTransport(http_client=_mock_client(handler))
    response = transport.send(SPEC)
    assert response.status_code == 200
    assert response.json() == {"results": [], "more": False}


def test_sync_sends_authorization_header_only_with_token():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={})

    SyncTransport(http_client=_mock_client(handler)).send(SPEC)
    assert seen["auth"] is None

    SyncTransport(token="tok", http_client=_mock_client(handler)).send(SPEC)
    assert seen["auth"] == "Token tok"


def test_sync_retries_429_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, text="slow down")
        return httpx.Response(200, json={"ok": True})

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=3))
    response = transport.send(SPEC)
    assert calls["n"] == 2
    assert response.json() == {"ok": True}


def test_sync_raises_after_exhausting_retries():
    def handler(request):
        return httpx.Response(429, text="slow down")

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=2))
    with pytest.raises(VndbRateLimitError) as info:
        transport.send(SPEC)
    assert info.value.status_code == 429


def test_sync_wraps_network_error():
    def handler(request):
        raise httpx.ConnectError("no route")

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=1))
    with pytest.raises(VndbNetworkError):
        transport.send(SPEC)


def test_sync_close_only_closes_owned_client():
    injected = _mock_client(lambda r: httpx.Response(200, json={}))
    transport = SyncTransport(http_client=injected)
    transport.close()
    assert injected.is_closed is False  # injected client left open


def _run(coro):
    return asyncio.run(coro)


def test_async_success_and_retry():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, text="slow")
        return httpx.Response(200, json={"ok": True})

    async def scenario():
        transport = AsyncTransport(http_client=_mock_async_client(handler), retry=RetryConfig(max_attempts=3))
        response = await transport.send(SPEC)
        await transport.aclose()
        return response

    response = _run(scenario())
    assert calls["n"] == 2
    assert response.json() == {"ok": True}


def test_async_wraps_network_error():
    def handler(request):
        raise httpx.ConnectError("down")

    async def scenario():
        transport = AsyncTransport(http_client=_mock_async_client(handler), retry=RetryConfig(max_attempts=1))
        try:
            await transport.send(SPEC)
        finally:
            await transport.aclose()

    with pytest.raises(VndbNetworkError):
        _run(scenario())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_transport.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client._transport'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/_transport.py`:
```python
from __future__ import annotations

import asyncio
import time

import httpx

from vndb_client import core
from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    RetryConfig,
)
from vndb_client.core import RequestSpec, RetryPolicy
from vndb_client.exceptions import VndbNetworkError


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


async def _asleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def _build_headers(token: str | None, user_agent: str) -> dict[str, str]:
    headers = {"User-Agent": user_agent}
    if token:
        headers["Authorization"] = f"Token {token}"
    return headers


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


class SyncTransport:
    """Synchronous HTTP transport with a bounded retry loop."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._policy = RetryPolicy(retry or RetryConfig())
        self._headers = _build_headers(token, user_agent)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(base_url=base_url, timeout=timeout)

    def send(self, spec: RequestSpec) -> httpx.Response:
        attempt = 0
        while True:
            attempt += 1
            status: int | None = None
            exc: Exception | None = None
            retry_after: float | None = None
            response: httpx.Response | None = None
            try:
                response = self._client.request(
                    spec.method, spec.path, json=spec.json, params=spec.params, headers=self._headers
                )
            except httpx.TransportError as transport_exc:
                exc = transport_exc
            else:
                if response.status_code < 400:
                    return response
                status = response.status_code
                retry_after = _retry_after(response)
            should_retry, delay = self._policy.next(attempt, status, exc, retry_after)
            if should_retry:
                _sleep(delay)
                continue
            if response is None:
                raise VndbNetworkError(str(exc)) from exc
            core.raise_for_status(response.status_code, response.text)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class AsyncTransport:
    """Asynchronous HTTP transport with a bounded retry loop."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._policy = RetryPolicy(retry or RetryConfig())
        self._headers = _build_headers(token, user_agent)
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def send(self, spec: RequestSpec) -> httpx.Response:
        attempt = 0
        while True:
            attempt += 1
            status: int | None = None
            exc: Exception | None = None
            retry_after: float | None = None
            response: httpx.Response | None = None
            try:
                response = await self._client.request(
                    spec.method, spec.path, json=spec.json, params=spec.params, headers=self._headers
                )
            except httpx.TransportError as transport_exc:
                exc = transport_exc
            else:
                if response.status_code < 400:
                    return response
                status = response.status_code
                retry_after = _retry_after(response)
            should_retry, delay = self._policy.next(attempt, status, exc, retry_after)
            if should_retry:
                await _asleep(delay)
                continue
            if response is None:
                raise VndbNetworkError(str(exc)) from exc
            core.raise_for_status(response.status_code, response.text)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_transport.py -v`
Expected: PASS (all sync + async cases).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/_transport.py tests/test_transport.py
git commit -m "feat(foundation): add sync and async transports with retry loop

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Clients (`Client` / `AsyncClient`)

**Files:**
- Create: `src/vndb_client/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write the failing test**

`tests/test_client.py`:
```python
from __future__ import annotations

import asyncio

import httpx

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.models import Page, VndbModel


class _VN(VndbModel):
    id: str


def _handler(request):
    return httpx.Response(200, json={"results": [{"id": "v1"}], "more": False, "count": 1})


def _mock_client():
    return httpx.Client(transport=httpx.MockTransport(_handler), base_url=PROD_BASE_URL)


def _mock_async_client():
    return httpx.AsyncClient(transport=httpx.MockTransport(_handler), base_url=PROD_BASE_URL)


def test_sync_query_returns_typed_page():
    with Client(http_client=_mock_client()) as client:
        page = client._query("vn", _VN, fields="id", count=True)
    assert isinstance(page, Page)
    assert page.count == 1
    assert page.results[0].id == "v1"
    assert isinstance(page.results[0], _VN)


def test_sync_context_manager_closes_owned_client():
    client = Client()  # builds its own httpx client
    with client:
        pass
    # accessing the private transport's client to assert closure
    assert client._transport._client.is_closed is True


def test_async_query_returns_typed_page():
    async def scenario():
        async with AsyncClient(http_client=_mock_async_client()) as client:
            return await client._query("vn", _VN, fields="id")

    page = asyncio.run(scenario())
    assert page.results[0].id == "v1"
    assert isinstance(page.results[0], _VN)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.client'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/client.py`:
```python
from __future__ import annotations

from types import TracebackType
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from vndb_client import core
from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    RetryConfig,
)
from vndb_client.core import RequestSpec
from vndb_client.models import Page
from vndb_client._transport import AsyncTransport, SyncTransport

ModelT = TypeVar("ModelT", bound=BaseModel)


class Client:
    """Synchronous VNDB Kana API client."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = SyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
        )

    def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = self._transport.send(spec)
        return core.parse_page(response.json(), model)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncClient:
    """Asynchronous VNDB Kana API client."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
        )

    async def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = await self._transport.send(spec)
        return core.parse_page(response.json(), model)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_client.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/client.py tests/test_client.py
git commit -m "feat(foundation): add sync Client and AsyncClient with generic _query

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Public API surface

**Files:**
- Modify: `src/vndb_client/__init__.py`
- Test: `tests/test_public_api.py`

- [ ] **Step 1: Write the failing test**

`tests/test_public_api.py`:
```python
from __future__ import annotations

import vndb_client


def test_public_exports_present():
    for name in (
        "Client",
        "AsyncClient",
        "Page",
        "RetryConfig",
        "VndbError",
        "VndbAPIError",
        "VndbBadRequestError",
        "VndbAuthError",
        "VndbNotFoundError",
        "VndbRateLimitError",
        "VndbServerError",
        "VndbNetworkError",
        "VndbParseError",
    ):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: FAIL — exports/`__all__` not defined.

- [ ] **Step 3: Write the implementation**

Replace the contents of `src/vndb_client/__init__.py` with:
```python
from __future__ import annotations

from vndb_client.client import AsyncClient, Client
from vndb_client.config import RetryConfig
from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbError,
    VndbNetworkError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)
from vndb_client.models import Page

__all__ = [
    "AsyncClient",
    "Client",
    "Page",
    "RetryConfig",
    "VndbAPIError",
    "VndbAuthError",
    "VndbBadRequestError",
    "VndbError",
    "VndbNetworkError",
    "VndbNotFoundError",
    "VndbParseError",
    "VndbRateLimitError",
    "VndbServerError",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/vndb_client/__init__.py tests/test_public_api.py
git commit -m "feat(foundation): export public API from package root

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Quality gate & full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite with coverage**

Run: `uv run python -m pytest`
Expected: ALL tests pass.

- [ ] **Step 2: Run doctest pass (as CI/tox does)**

Run: `uv run python -m pytest --doctest-modules src`
Expected: PASS (no doctests yet, or they pass).

- [ ] **Step 3: Type-check**

Run: `uv run mypy`
Expected: `Success: no issues found`. If the `parse_page` `# type: ignore[valid-type]` reports a different code, change the bracketed code to the one mypy prints (mypy with `warn_unused_ignores` will name it).

- [ ] **Step 4: Lint & format**

Run: `uv run ruff format` then `uv run ruff check --fix`
Expected: clean. Re-stage any files Ruff reformats.

- [ ] **Step 5: Dependency check**

Run: `uv run deptry src`
Expected: no missing/unused dependency findings (`httpx` and `pydantic` are both imported in `src`).

- [ ] **Step 6: Run the project's combined gate**

Run: `make check`
Expected: lock check + pre-commit (ruff) + mypy + deptry all pass.

- [ ] **Step 7: Commit any formatting/lint fixups**

```bash
git add -A
git commit -m "chore(foundation): satisfy ruff/mypy/deptry quality gate

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

(Skip this commit if Steps 4–6 produced no changes.)

---

## Self-Review

**Spec coverage** (each requirement → task):

| Spec capability / requirement | Task |
|---|---|
| `http-transport`: Client construction & config (defaults, token, injected client) | Task 7 (client) + Task 6 (`_build_headers`, injected client) |
| `http-transport`: Client lifecycle (sync/async context mgr, owned vs injected close) | Task 6 (`close`/`aclose`), Task 7 (context managers) |
| `http-transport`: Generic query primitive (typed Page, standard body params) | Task 5 (`build_query_request`), Task 7 (`_query`) |
| `request-retry`: Configurable bounded retry (retry-then-succeed, exhausted) | Task 4 (`RetryConfig`), Task 5 (`RetryPolicy`), Task 6 (loop) |
| `request-retry`: Retry classification (429/5xx/network yes; 4xx/validation no; pure) | Task 5 (`RetryPolicy.next` tests) |
| `request-retry`: Backoff timing (Retry-After, exponential cap, patchable sleep) | Task 5 (delay tests), Task 6 (`_sleep`/`_asleep` patched) |
| `error-handling`: Exception hierarchy (shared base, status+message) | Task 2 |
| `error-handling`: HTTP status mapping (plain-text body) + network wrap | Task 5 (`raise_for_status`), Task 6 (`VndbNetworkError`) |
| `response-envelope`: `VndbModel` parsing base (alias + by name) | Task 3 |
| `response-envelope`: Generic `Page[T]` (results/more/count/filters) | Task 3 |
| `response-envelope`: Sans-I/O parsing | Task 5 (`parse_page`) |
| Proposal: add httpx+pydantic deps, remove `foo.py` | Task 1 |
| Proposal: export public API | Task 8 |
| Design open question: wrap `ValidationError` | Task 2 (`VndbParseError`) + Task 5 (`parse_page` wrap) — **resolved: wrap** |

No gaps found.

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N" — every code step contains complete code.

**Type consistency:** `RequestSpec`, `RetryPolicy.next(attempt, status, exc, retry_after)`, `build_query_request(endpoint, *, ...)`, `parse_page(raw, model)`, `SyncTransport.send`/`close`, `AsyncTransport.send`/`aclose`, `Client._query`/`close`, `AsyncClient._query`/`aclose` are referenced consistently across tasks. Module-level `_sleep`/`_asleep` patched by name in Task 6 match their definitions.
