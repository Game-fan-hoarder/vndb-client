# Response caching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in, per-client in-memory TTL cache of read responses at the transport layer, with writes bypassing the cache.

**Architecture:** A new private `src/vndb_client/_cache.py` holds `is_cacheable(spec)`, `cache_key(spec)`, and a bounded-LRU `ResponseCache(ttl, maxsize, *, clock)`. Both transports gain an optional `_cache` (built from new `cache_ttl`/`cache_maxsize` ctor args); their retry loop is split into `_send_uncached`, and `send` consults the cache around it (serve hit, else fetch-then-store). `Client`/`AsyncClient` gain `cache_ttl`/`cache_maxsize`, forwarded to the transport. Default `cache_ttl=None` → caching off.

**Tech Stack:** Python 3.10+, httpx, `collections.OrderedDict`, `time.monotonic`; pytest with httpx `MockTransport` and an injected fake clock.

**Source of truth:** approved design `docs/2026-06-06_response_caching_design.md`; delta spec `openspec/changes/response-caching/specs/response-caching/spec.md`.

**Worktree note:** pre-commit hooks are NOT installed here. Before each commit run `uv run ruff format .` and `uv run ruff check --fix .` and re-stage.

---

## Verified facts (use verbatim)

- `RequestSpec` (in `core.py`) is a frozen dataclass: `method: str`, `path: str`, `json: dict[str,Any]|None=None`, `params: dict[str,Any]|None=None`.
- `SyncTransport.send(spec)` / `AsyncTransport.send(spec)` run a `while True` retry loop that `return`s the `httpx.Response` on status `< 400`, else raises (`VndbNetworkError` on transport error, or `core.raise_for_status`). Constructors take `token`, `base_url`, `timeout`, `user_agent`, `retry`, `http_client`.
- `Client.__init__(self, token=None, *, base_url=PROD_BASE_URL, timeout=DEFAULT_TIMEOUT, user_agent=DEFAULT_USER_AGENT, retry=None, http_client=None)` builds `self._transport = SyncTransport(token=..., base_url=..., timeout=..., user_agent=..., retry=retry, http_client=http_client)`. `AsyncClient` mirrors it with `AsyncTransport`.
- Test helpers: `tests/test_transport.py` has `_mock_client(handler)` / `_mock_async_client(handler)` (httpx `MockTransport`) and an autouse `_no_sleep` fixture patching `_transport._sleep`/`_asleep`. `tests/test_resource.py` has `_capture()`/`_client()`/`_aclient()`.
- httpx buffers `.content` after the first read, so re-serving a read `Response` supports repeated `.json()`.

---

## Task 1: `is_cacheable` + `cache_key` (`_cache.py`)

**Files:**
- Create: `src/vndb_client/_cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cache.py`:

```python
from __future__ import annotations

from vndb_client._cache import cache_key, is_cacheable
from vndb_client.core import RequestSpec


def test_is_cacheable_reads_true_writes_false():
    assert is_cacheable(RequestSpec(method="GET", path="/stats")) is True
    assert is_cacheable(RequestSpec(method="POST", path="/vn", json={"fields": "id"})) is True
    assert is_cacheable(RequestSpec(method="PATCH", path="/ulist/v17", json={"vote": 90})) is False
    assert is_cacheable(RequestSpec(method="DELETE", path="/ulist/v17")) is False


def test_cache_key_identical_for_identical_specs():
    a = RequestSpec(method="POST", path="/vn", json={"fields": "id", "filters": ["x"]})
    b = RequestSpec(method="POST", path="/vn", json={"filters": ["x"], "fields": "id"})
    assert cache_key(a) == cache_key(b)  # key order in json must not matter


def test_cache_key_differs_on_method_path_body_params():
    base = RequestSpec(method="POST", path="/vn", json={"fields": "id"})
    assert cache_key(base) != cache_key(RequestSpec(method="GET", path="/vn", json={"fields": "id"}))
    assert cache_key(base) != cache_key(RequestSpec(method="POST", path="/release", json={"fields": "id"}))
    assert cache_key(base) != cache_key(RequestSpec(method="POST", path="/vn", json={"fields": "id,title"}))
    assert cache_key(base) != cache_key(RequestSpec(method="POST", path="/vn", json={"fields": "id"}, params={"x": "1"}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_cache.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vndb_client._cache'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/vndb_client/_cache.py`:

```python
from __future__ import annotations

import json

from vndb_client.core import RequestSpec

_CACHEABLE_METHODS = frozenset({"GET", "POST"})


def is_cacheable(spec: RequestSpec) -> bool:
    """True for read requests (GET/POST); False for writes (PATCH/DELETE)."""
    return spec.method in _CACHEABLE_METHODS


def cache_key(spec: RequestSpec) -> tuple[str, str, str, str]:
    """A stable cache key from the request's method, path, JSON body, and params."""
    return (
        spec.method,
        spec.path,
        json.dumps(spec.json, sort_keys=True),
        json.dumps(spec.params, sort_keys=True),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_cache.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/_cache.py tests/test_cache.py
uv run ruff check --fix src/vndb_client/_cache.py tests/test_cache.py
git add src/vndb_client/_cache.py tests/test_cache.py
git commit -m "feat(cache): is_cacheable + cache_key helpers"
```

---

## Task 2: `ResponseCache` (TTL + LRU)

**Files:**
- Modify: `src/vndb_client/_cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_cache.py`:

```python
import httpx

from vndb_client._cache import ResponseCache


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _resp(n: int) -> httpx.Response:
    return httpx.Response(200, json={"n": n})


def test_response_cache_hit_and_miss():
    clock = _FakeClock()
    cache = ResponseCache(ttl=10.0, clock=clock)
    assert cache.get(("k",)) is None  # miss on absent
    cache.set(("k",), _resp(1))
    assert cache.get(("k",)).json() == {"n": 1}  # hit


def test_response_cache_expires_after_ttl():
    clock = _FakeClock()
    cache = ResponseCache(ttl=10.0, clock=clock)
    cache.set(("k",), _resp(1))
    clock.now = 9.999
    assert cache.get(("k",)) is not None  # still fresh
    clock.now = 10.0
    assert cache.get(("k",)) is None  # expired at/after ttl


def test_response_cache_evicts_lru_beyond_maxsize():
    clock = _FakeClock()
    cache = ResponseCache(ttl=100.0, maxsize=2, clock=clock)
    cache.set(("a",), _resp(1))
    cache.set(("b",), _resp(2))
    cache.get(("a",))  # touch "a" so "b" is now least-recently-used
    cache.set(("c",), _resp(3))  # exceeds maxsize -> evict LRU ("b")
    assert cache.get(("b",)) is None
    assert cache.get(("a",)) is not None
    assert cache.get(("c",)) is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_cache.py -q -k response_cache`
Expected: FAIL with `ImportError: cannot import name 'ResponseCache'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/vndb_client/_cache.py` (extend imports with `import time`, `from collections import OrderedDict`, `from collections.abc import Callable`, `import httpx`):

```python
class ResponseCache:
    """An in-memory, bounded (LRU) TTL cache of ``httpx.Response`` objects."""

    def __init__(self, ttl: float, maxsize: int = 128, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl
        self._maxsize = maxsize
        self._clock = clock
        self._store: OrderedDict[tuple[str, ...], tuple[float, httpx.Response]] = OrderedDict()

    def get(self, key: tuple[str, ...]) -> httpx.Response | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, response = entry
        if self._clock() >= expiry:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return response

    def set(self, key: tuple[str, ...], response: httpx.Response) -> None:
        self._store[key] = (self._clock() + self._ttl, response)
        self._store.move_to_end(key)
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)
```

Note: the existing `cache_key` returns a 4-tuple, which is a `tuple[str, ...]`; the cache's key type is widened to `tuple[str, ...]` so both unit tests (using `("k",)`) and real keys type-check.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_cache.py -q`
Expected: PASS (6 tests). Then `uv run mypy` → `Success: no issues found`.

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/_cache.py tests/test_cache.py
uv run ruff check --fix src/vndb_client/_cache.py tests/test_cache.py
git add src/vndb_client/_cache.py tests/test_cache.py
git commit -m "feat(cache): ResponseCache with TTL expiry and LRU eviction"
```

---

## Task 3: Wire the cache into both transports

**Files:**
- Modify: `src/vndb_client/_transport.py`
- Test: `tests/test_transport.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_transport.py`:

```python
def _counting_handler():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json={"results": [], "more": False})

    return calls, handler


def test_cache_serves_repeated_read_once():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler), cache_ttl=60.0)
    t.send(SPEC)
    t.send(SPEC)
    assert calls["n"] == 1  # second read served from cache


def test_cache_disabled_hits_network_each_time():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler))  # no cache_ttl
    t.send(SPEC)
    t.send(SPEC)
    assert calls["n"] == 2


def test_cache_bypassed_for_writes():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler), cache_ttl=60.0)
    write = RequestSpec(method="PATCH", path="/ulist/v17", json={"vote": 90})
    t.send(write)
    t.send(write)
    assert calls["n"] == 2  # writes always hit the network


def test_async_cache_serves_repeated_read_once():
    calls, handler = _counting_handler()

    async def scenario():
        t = AsyncTransport(http_client=_mock_async_client(handler), cache_ttl=60.0)
        await t.send(SPEC)
        await t.send(SPEC)

    asyncio.run(scenario())
    assert calls["n"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_transport.py -q -k cache`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'cache_ttl'`.

- [ ] **Step 3: Write minimal implementation**

In `src/vndb_client/_transport.py`:

(a) Add the import near the top (after the existing imports):

```python
from vndb_client._cache import ResponseCache, cache_key, is_cacheable
```

(b) For BOTH `SyncTransport.__init__` and `AsyncTransport.__init__`, add two params at the end of the signature (after `http_client=...,`):

```python
        cache_ttl: float | None = None,
        cache_maxsize: int = 128,
```
and add this line to each constructor body (after `self._client = ...`):

```python
        self._cache = ResponseCache(cache_ttl, cache_maxsize) if cache_ttl is not None else None
```

(c) In `SyncTransport`, rename the existing `def send(self, spec)` method body to `def _send_uncached(self, spec: RequestSpec) -> httpx.Response:` (keep the entire retry loop unchanged), and add a new `send`:

```python
    def send(self, spec: RequestSpec) -> httpx.Response:
        if self._cache is None or not is_cacheable(spec):
            return self._send_uncached(spec)
        key = cache_key(spec)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        response = self._send_uncached(spec)
        self._cache.set(key, response)
        return response
```

(d) In `AsyncTransport`, do the same: rename the existing async send body to `async def _send_uncached(self, spec: RequestSpec) -> httpx.Response:` (loop unchanged), and add:

```python
    async def send(self, spec: RequestSpec) -> httpx.Response:
        if self._cache is None or not is_cacheable(spec):
            return await self._send_uncached(spec)
        key = cache_key(spec)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        response = await self._send_uncached(spec)
        self._cache.set(key, response)
        return response
```

(The cache's `get`/`set` are plain dict ops — safe to call from the async path without `await`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_transport.py -q`
Expected: PASS (all transport tests incl. the 4 new). Then `uv run mypy` → success.

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/_transport.py tests/test_transport.py
uv run ruff check --fix src/vndb_client/_transport.py tests/test_transport.py
git add src/vndb_client/_transport.py tests/test_transport.py
git commit -m "feat(transport): optional response cache around send()"
```

---

## Task 4: Expose `cache_ttl`/`cache_maxsize` on the clients

**Files:**
- Modify: `src/vndb_client/client.py`
- Test: `tests/test_resource.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_resource.py`:

```python
def test_client_cache_ttl_serves_repeated_query_once():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json=VN_RESPONSE)

    with Client(http_client=_client(handler), cache_ttl=60.0) as client:
        client.vn.query(filters=["search", "=", "ever"])
        client.vn.query(filters=["search", "=", "ever"])
    assert calls["n"] == 1


def test_client_without_cache_queries_each_time():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json=VN_RESPONSE)

    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=["search", "=", "ever"])
        client.vn.query(filters=["search", "=", "ever"])
    assert calls["n"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_resource.py -q -k cache`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'cache_ttl'`.

- [ ] **Step 3: Write minimal implementation**

In `src/vndb_client/client.py`, for BOTH `Client.__init__` and `AsyncClient.__init__`:

(a) add two params at the end of the signature (after `http_client: ... = None,`):

```python
        cache_ttl: float | None = None,
        cache_maxsize: int = 128,
```

(b) forward them in the transport construction — add to the `SyncTransport(...)` / `AsyncTransport(...)` call (after `http_client=http_client,`):

```python
            cache_ttl=cache_ttl,
            cache_maxsize=cache_maxsize,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_resource.py -q`
Expected: PASS (all resource tests incl. the 2 new). Then `uv run mypy` → success.

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/client.py tests/test_resource.py
uv run ruff check --fix src/vndb_client/client.py tests/test_resource.py
git add src/vndb_client/client.py tests/test_resource.py
git commit -m "feat(client): cache_ttl/cache_maxsize opt-in response caching"
```

---

## Task 5: Document caching

**Files:**
- Modify: `docs/guides/querying.md`

- [ ] **Step 1: Append a caching section**

Add to the END of `docs/guides/querying.md`:

````markdown
## Response caching

Reads are not cached by default. Pass `cache_ttl` (seconds) to enable an
in-memory cache of read responses on a client; identical reads within the TTL are
served without a network call:

```python
from vndb_client import Client

with Client(cache_ttl=60.0) as client:
    client.vn.query(filters=["search", "=", "ever17"])  # network
    client.vn.query(filters=["search", "=", "ever17"])  # served from cache
```

The cache is per-client (not shared across clients or tokens), bounded by
`cache_maxsize` (default 128, least-recently-used eviction), and applies only to
reads — writes (`set_ulist`/`delete_ulist`/`set_rlist`/`delete_rlist`) always hit
the API. Staleness is bounded by `cache_ttl`.
````

- [ ] **Step 2: Verify the docs build (strict)**

Run: `uv run mkdocs build --strict`
Expected: exit 0, no warnings. Then `rm -rf site`.

- [ ] **Step 3: Commit**

```bash
git add docs/guides/querying.md
git commit -m "docs(guides): document opt-in response caching"
```

---

## Task 6: Full verification

**Files:** none modified (verification only; commit only if a fix is required).

- [ ] **Step 1: Quality gate**

Run: `uv run mypy` → `Success: no issues found`.
Run: `uv run ruff format --check . && uv run ruff check .` → format check passes; `All checks passed!`.
Run: `uv run deptry src` → no violations.

- [ ] **Step 2: Full test suite + coverage gate**

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml -q`
Expected: all tests pass (171 prior + 15 new = 186), coverage `TOTAL` ≥ 90% with no fail-under message.

- [ ] **Step 3: Docs build**

Run: `uv run mkdocs build --strict` → exit 0, no warnings; then `rm -rf site`.

---

## Self-Review

**1. Spec coverage** (`response-caching` requirement → task):

- *Opt-in response cache* (disabled by default; repeated read served from cache) → Task 4 (`cache_ttl` param; `test_client_cache_ttl_serves_repeated_query_once` / `test_client_without_cache_queries_each_time`) + Task 3 transport hit test. ✓
- *Cache scope and key* (method/path/body/params; distinct queries not conflated) → Task 1 (`cache_key` tests for identical + differing specs). Per-client scope → Task 3/4 (cache built per transport per client). ✓
- *Writes bypass the cache* (write always hits network; errors not cached) → Task 1 (`is_cacheable` PATCH/DELETE False) + Task 3 (`test_cache_bypassed_for_writes`); errors-not-cached holds because `_send_uncached` raises before `set` (only `<400` returns). ✓
- *TTL expiry and bounded size* (refetch after expiry; bounded by maxsize) → Task 2 (`test_response_cache_expires_after_ttl`, `test_response_cache_evicts_lru_beyond_maxsize`). The transport's expiry path reuses the miss branch (already covered by `test_cache_serves_repeated_read_once`'s miss-then-hit and the disabled test). ✓

No spec requirement is left without a task.

**2. Placeholder scan:** No "TBD"/"handle edge cases". Every code step shows full code; every command has expected output. ✓

**3. Type/name consistency:** `is_cacheable`, `cache_key`, `ResponseCache(ttl, maxsize, *, clock)`, `_send_uncached`, `cache_ttl`/`cache_maxsize` are used identically across `_cache.py`, `_transport.py`, and `client.py`. The cache key type `tuple[str, ...]` accommodates both `cache_key`'s 4-tuple and the unit tests' `("k",)`. `get` returns `httpx.Response | None`; `send` returns `httpx.Response`. ✓
