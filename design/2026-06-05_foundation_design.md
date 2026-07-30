# Foundation — Design

**Date:** 2026-06-05
**Epic:** `vndb-client-sp7` — Foundation: transport, sans-I/O core, exceptions, Page[T]
**Milestone:** MVP foundation
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans

## Purpose

Build the internal plumbing every other epic depends on: a sync **and** async
httpx transport, a sans-I/O core, the exception hierarchy, and the generic
`Page[T]` response envelope. Foundation ships assembled `Client`/`AsyncClient`
classes with an internal generic query primitive, but no public entity resources
(the first of those, VN, is a separate epic).

## Decisions (this design)

| Decision | Choice |
|----------|--------|
| Rate-limit handling | Auto-retry 429 with bounded, configurable backoff (honor `Retry-After`, else exponential); raise `VndbRateLimitError` once exhausted. |
| Retry scope | 429 **and** transient 5xx (502/503) + httpx network/timeout errors. Never 400/401/404 or `ValidationError`. |
| HTTP configurability | Constructor kwargs (`token`, `base_url`, `timeout`, `retry`, `user_agent`) **plus** an optional injected `httpx.Client`/`AsyncClient`. |
| Scope boundary | `Client`/`AsyncClient` shells + internal generic `_query` returning `Page[T]`; verified with `httpx.MockTransport` + a dummy model. |
| Retry/sans-I/O boundary | Approach A: pure `RetryPolicy.next()` in core decides retry+delay; each transport owns the loop and the sleep. |

Inherited from the vision (`2026-06-05_full_api_client.md`): httpx + Pydantic v2,
sync+async over a shared sans-I/O core, Python 3.10–3.14, strict typing.

## Module layout (`src/vndb_client/`)

| Module | Responsibility |
|--------|----------------|
| `exceptions.py` | `VndbError` (base) → `VndbAPIError` (`status_code` + `message`/body) with subclasses `VndbBadRequestError` (400), `VndbAuthError` (401), `VndbNotFoundError` (404), `VndbRateLimitError` (429), `VndbServerError` (5xx); plus `VndbNetworkError` (wraps httpx transport/timeout failures). |
| `models.py` | `VndbModel` base (Pydantic v2 `model_config`: `populate_by_name`, snake↔API-key alias generator); generic `Page[T]` envelope. |
| `core.py` | **Sans-I/O.** `RequestSpec`; `build_query_request(...)`; `parse_page(raw_json, model_type) -> Page[model_type]`; `raise_for_status(status, body_text)`; `RetryPolicy.next(attempt, status, exc) -> (retry, delay)`. No httpx import. |
| `config.py` | `PROD_BASE_URL`, `SANDBOX_BASE_URL`, default timeout, default user-agent, `RetryConfig` (max attempts, base/backoff, retry-on set). |
| `_transport.py` | `SyncTransport` / `AsyncTransport`: build or adopt an injected httpx client; execute a `RequestSpec`; drive the retry loop (`RetryPolicy.next` + `time.sleep`/`asyncio.sleep`); map failures via `core.raise_for_status`. |
| `client.py` | `Client` / `AsyncClient`: construct from config kwargs + optional injected client; context-manager lifecycle (`__enter__/__exit__`, async variants) + `close()`/`aclose()`; internal generic `_query(endpoint, model, **params) -> Page[model]` (+ `_get` helper for later simple-GET endpoints). |
| `__init__.py` | Public exports: `Client`, `AsyncClient`, `Page`, exception types, `RetryConfig`. |

The placeholder `foo.py` is removed as part of this epic.

## Data flow

Sync and async are identical except for await points:

```
client._query(endpoint, model, **params)
  -> core.build_query_request(endpoint, params)  -> RequestSpec        (pure)
  -> transport.send(spec):
        attempt = 0
        loop:
          try: raw = httpx_client.request(spec)            # I/O
          except httpx.TransportError as e: exc = e, raw = None
          retry, delay = core.RetryPolicy.next(attempt, raw.status?, exc?)  (pure)
          if retry: sleep(delay); attempt += 1; continue   # time/asyncio.sleep
          if exc:   raise VndbNetworkError(...) from exc
          if raw.status >= 400: core.raise_for_status(raw.status, raw.text)
          return raw
  -> core.parse_page(raw.json(), model)  -> Page[model]                (pure)
  -> return Page[model]
```

## Error handling

- `core.raise_for_status` maps: 400→`VndbBadRequestError`, 401→`VndbAuthError`,
  404→`VndbNotFoundError`, 429→`VndbRateLimitError`, 5xx→`VndbServerError`.
- VNDB returns error detail as a **plain-text body**, so the message is taken from
  `response.text` (not JSON). Each `VndbAPIError` carries `status_code` + body.
- httpx network/timeout failures are wrapped in `VndbNetworkError`.
- A Pydantic `ValidationError` in `parse_page` is a schema mismatch, not an API
  error. **Open choice for the plan:** propagate as-is vs. wrap in a
  `VndbError` subclass. Default leaning: wrap for a cleaner public surface.

## Retry policy

- `RetryConfig` drives the pure `RetryPolicy.next`:
  - Retries on 429, 502/503, and httpx transport/timeout errors; never on
    400/401/404 or `ValidationError`.
  - Backoff: honor `Retry-After` on 429 when present; otherwise exponential
    (`base * 2**attempt`) with a cap. Bounded by `max_attempts` (default 3).
    On exhaustion, the last error is raised.
  - `RetryPolicy.next` is fully unit-testable from synthetic
    `(attempt, status, exc)` inputs — no network, no clock.

## `Page[T]` modeling

- `VndbModel(BaseModel)` sets shared `model_config` (`populate_by_name=True` + alias
  generator) so entity models inherit consistent parsing.
- `Page(BaseModel, Generic[T])`: `results: list[T]`, `more: bool`,
  `count: int | None = None`, `compact_filters: str | None = None`,
  `normalized_filters: list | None = None`.
- Pydantic v2 generics work across 3.10–3.14; `from __future__ import annotations`
  used and verified under tox.
- Foundation has no entity, so parsing is exercised with a tiny **dummy model**
  in tests: `class _Dummy(VndbModel): id: str; title: str | None = None`, decoded
  via `Page[_Dummy]`.

## Test strategy

pytest with mocked transport (enabled by the injectable-client decision):

- **Sans-I/O unit tests (no network):**
  - `RetryPolicy.next` decision table: 429 with/without `Retry-After`, 502,
    network exc, 400 → no retry, attempts exhausted.
  - `raise_for_status` status→exception mapping including plain-text body.
  - `build_query_request` body serialization.
  - `parse_page` against sample envelopes incl. `more`/`count` variants.
- **Transport/client tests (mocked I/O):**
  - Inject `httpx.MockTransport(handler)` into `Client`/`AsyncClient`.
  - Generic `_query` returns a correct `Page[_Dummy]`.
  - `Authorization: Token <token>` sent only when a token is configured.
  - Retry re-requests on a 429-then-200 handler (sleep patched, so instant).
  - Exhaustion raises the mapped error.
  - Context-manager + `close()`/`aclose()` close the underlying client.
  - Async tests via pytest async support.
- All tests run under the 3.10–3.14 tox matrix; coverage meets the project gate.
- **Sleep indirection:** transport sleep is a small injectable/patchable
  indirection (e.g. module-level `_sleep`/`_asleep`) so retry tests never wait.

## Out of scope (later epics)

- Public entity resources and models (VN flagship and beyond).
- The fluent query builder / filter DSL (Foundation accepts raw filter/field
  values through the generic primitive).
- Simple GET endpoint resources, ulist read/write.
