## Why

Every other epic in the VNDB client depends on a working HTTP foundation. Before any
entity (VN, releases, etc.) can be queried, we need a sync **and** async transport,
a sans-I/O core that builds requests and parses responses, an exception hierarchy,
and a generic response envelope. This change builds that foundation.

## What Changes

- Add `Client` and `AsyncClient` classes with config (token, base URL, timeout,
  user-agent, retry settings), optional injection of a pre-built httpx client, and
  context-manager lifecycle (`close()`/`aclose()`).
- Add a sans-I/O `core` that serializes the standard VNDB query body
  (`filters`, `fields`, `sort`, `reverse`, `results`, `page`, `count`) into a
  request spec and parses a JSON response envelope into a typed `Page[T]`.
- Add an internal generic query primitive (`_query`) on both clients returning
  `Page[T]` for any Pydantic model — verified with `httpx.MockTransport` and a
  dummy model. (Public entity resources are out of scope; VN is a later epic.)
- Add bounded, configurable auto-retry: 429 (honoring `Retry-After`) plus transient
  5xx and httpx network/timeout errors, with the retry *decision* implemented as a
  pure function in core and the loop/sleep owned by each transport.
- Add an exception hierarchy mapping HTTP status codes (400/401/404/429/5xx) and
  wrapping network failures, reading VNDB's plain-text error bodies.
- Add a generic `Page[T]` envelope and a `VndbModel` base with camelCase↔snake
  aliasing.
- Add `httpx` and `pydantic` (v2) as runtime dependencies.
- Remove the placeholder `src/vndb_client/foo.py`.

## Capabilities

### New Capabilities

- `http-transport`: Sync/async clients — configuration, optional injected httpx
  client, auth header, request execution, lifecycle, and the internal generic
  query primitive.
- `request-retry`: Bounded, configurable retry/backoff policy for rate limits
  (429), transient 5xx, and network/timeout failures, decided by a pure core
  function.
- `error-handling`: Exception hierarchy and HTTP-status→exception mapping,
  including network-failure wrapping and plain-text error bodies.
- `response-envelope`: Generic `Page[T]` response model and the `VndbModel`
  parsing base (alias handling), with sans-I/O response parsing.

### Modified Capabilities

<!-- None — greenfield; no existing specs in openspec/specs/. -->

## Impact

- **New runtime dependencies:** `httpx`, `pydantic>=2`.
- **New modules** under `src/vndb_client/`: `client.py`, `_transport.py`,
  `core.py`, `models.py`, `config.py`, `exceptions.py`, and updated `__init__.py`.
- **Removed:** `src/vndb_client/foo.py` (and its placeholder test, if any).
- **Public API surface:** `Client`, `AsyncClient`, `Page`, exception types,
  `RetryConfig` exported from the package root.
- **No breaking changes** (pre-1.0, no prior public API).
