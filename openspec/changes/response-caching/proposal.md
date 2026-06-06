## Why

Repeated identical read queries (same filters/fields) re-hit the VNDB API every
time, wasting calls against rate limits. An opt-in client-side cache lets callers
serve recent reads from memory. It must never serve stale write results or leak
data across tokens.

## What Changes

- Add a private `src/vndb_client/_cache.py` with:
  - `ResponseCache(ttl, maxsize=128, *, clock=time.monotonic)` — an in-memory,
    bounded (LRU) TTL store; `get(key)` returns the cached `httpx.Response` or
    `None` (miss/expiry), `set(key, response)` stores it.
  - `cache_key(spec)` — a stable key from the request's method, path, JSON body,
    and params.
  - `is_cacheable(spec)` — `True` for `GET`/`POST` (reads), `False` for
    `PATCH`/`DELETE` (writes).
- Wrap `SyncTransport.send` / `AsyncTransport.send`: extract the retry loop into
  `_send_uncached`; when a cache is present and the spec is cacheable, serve a
  hit or fetch-then-store. Only successful (`< 400`) responses are cached; writes
  bypass the cache entirely.
- Add opt-in `cache_ttl: float | None = None` and `cache_maxsize: int = 128`
  params to `Client` and `AsyncClient`, forwarded to their transports. Default
  `None` keeps caching off and behavior byte-identical.

Out of scope: ETag/conditional requests, write-triggered invalidation,
shared/persistent caches, caching error responses.

## Capabilities

### New Capabilities

- `response-caching`: an opt-in, per-client in-memory TTL cache of read responses
  at the transport layer, with write bypass and token-scoped isolation.

### Modified Capabilities

<!-- None. Caching is additive; existing http-transport behavior is unchanged
     when no cache is configured. -->

## Impact

- **New code:** `src/vndb_client/_cache.py`.
- **Modified code:** `src/vndb_client/_transport.py` (both transports gain an
  optional cache + `_send_uncached` split); `src/vndb_client/client.py`
  (`Client`/`AsyncClient` gain `cache_ttl`/`cache_maxsize`, forwarded to the
  transport).
- **Tests:** `tests/test_cache.py` (new), plus transport/client cache-behavior
  tests.
- **Backward compatible:** default `cache_ttl=None` → caching off; no behavior
  change for existing callers.
