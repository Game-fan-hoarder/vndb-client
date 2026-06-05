## Context

`vndb-client` is a greenfield, fully-typed Python client for the VNDB Kana HTTP API
(Python 3.10–3.14, strict mypy, Ruff). The vision
(`docs/2026-06-05_full_api_client.md`) fixes the stack as `httpx` + Pydantic v2 with
a sans-I/O core wrapped by thin sync and async clients. This change implements the
Foundation epic (`vndb-client-sp7`): the HTTP plumbing all later epics build on. The
full brainstorm is in `docs/2026-06-05_foundation_design.md`.

VNDB API constraints that shape the design: token auth via `Authorization: Token
<token>`; rate limits (200 req/5 min, 1s exec/min, 3s timeout) returning HTTP 429;
plain-text (not JSON) error bodies; a shared POST query body and response envelope
(`results`, `more`, `count`, `compact_filters`, `normalized_filters`).

## Goals / Non-Goals

**Goals:**
- Sync `Client` and async `AsyncClient` over a single shared sans-I/O core.
- Configurable transport (token, base URL, timeout, user-agent, retry) with an
  optional injected httpx client for testing and advanced use.
- Bounded auto-retry for 429 + transient 5xx + network/timeout errors.
- A typed exception hierarchy with HTTP-status mapping and network wrapping.
- A generic `Page[T]` envelope and a `VndbModel` parsing base.
- An internal generic query primitive proven end-to-end with mocked transport.

**Non-Goals:**
- Public entity resources/models (VN and beyond — later epics).
- The fluent query builder / filter DSL (Foundation accepts raw filter/field values).
- Simple GET endpoint resources, ulist read/write.
- Proactive client-side rate throttling (only reactive 429 retry here).

## Decisions

**1. Sans-I/O core + two thin transports.**
The core builds a `RequestSpec` and parses responses into models with no I/O; each
transport (sync/async) executes via httpx. *Alternative — write async + codegen
sync (`unasync`):* rejected for build-time complexity and harder debugging.
*Alternative — duplicate logic per transport:* rejected as non-DRY/untestable.

**2. Retry decision is pure; the loop lives in the transport.**
`core.RetryPolicy.next(attempt, status, exc) -> (retry, delay)` is pure and unit-
testable; each transport owns the loop and the sleep (`time.sleep` vs
`asyncio.sleep`). *Alternative — shared retry generator pumped by both transports:*
more DRY but more indirection. *Alternative — retry fully in each transport:*
duplicates policy, can't be tested without I/O.

**3. Auto-retry scope.** Retry on 429 (honor `Retry-After`, else exponential backoff
with cap), transient 502/503, and httpx transport/timeout errors; bounded by
`max_attempts` (default 3). Never retry 400/401/404 or Pydantic `ValidationError`.
*Alternative — 429-only / raise-immediately:* simpler but worse default DX for a
general-purpose library.

**4. Injectable httpx client.** Constructor accepts config kwargs and, optionally, a
pre-built `httpx.Client`/`AsyncClient` (enables `MockTransport`, proxies, custom
TLS). *Alternative — config kwargs only:* simpler surface, no escape hatch — rejected.

**5. Plain-text error bodies.** `core.raise_for_status(status, body_text)` reads the
message from `response.text`, matching VNDB's behavior, rather than assuming JSON.

**6. Generic `Page[T]` via Pydantic v2 generics**, with a `VndbModel` base carrying
shared `model_config` (alias generator + `populate_by_name`). Verified under the
3.10–3.14 tox matrix.

## Risks / Trade-offs

- **Pydantic v2 generic models across 3.10–3.14** → covered by the tox matrix; a
  tiny dummy model exercises `Page[T]` parsing in CI.
- **Retry could mask real outages** → bounded `max_attempts`, never retry 4xx
  (except 429), and surface the final error on exhaustion.
- **Sleep would slow tests** → transport sleep is an injectable/patchable
  indirection so retry tests run instantly.
- **`ValidationError` surface** (see Open Questions) → default to wrapping in a
  `VndbError` subclass for a cleaner public API; cheap to revisit.
- **Two transports drift** → mitigated by the shared pure core; only the ~3-line
  sleep/await differs.

## Open Questions

- Wrap Pydantic `ValidationError` from `parse_page` in a `VndbError` subclass, or
  let it propagate as-is? Leaning toward wrapping; final call during implementation.
