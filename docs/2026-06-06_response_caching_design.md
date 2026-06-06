# Response caching (mjj) — Design

**Status:** Approved 2026-06-06
**Beads task:** `vndb-client-mjj` (post-V1 stretch, deferred from epic 6lp)

## Goal

An opt-in, per-client, in-memory TTL cache of read responses that cuts repeat
network calls, while staying correct for auth'd/user-scoped data and never
caching writes.

## Scope decisions (from brainstorm)

- **Strategy:** in-memory TTL cache (ETag/conditional does not fit VNDB's
  POST-based query API).
- **Enablement:** opt-in `cache_ttl` float param on `Client`/`AsyncClient`
  (default `None` = off), plus `cache_maxsize`.
- **Invalidation:** reads (`GET` + `POST` query) are cached; writes
  (`PATCH`/`DELETE`) bypass entirely; staleness bounded by the TTL. No
  write-triggered invalidation.

## Components

### 1. Cache at the `transport.send` chokepoint

All requests flow through `SyncTransport.send` / `AsyncTransport.send`, and each
transport is built per-`Client` with that client's token in its headers — so a
cache bound to the transport is naturally token-scoped (no cross-token leakage).
Extract the existing retry loop into `_send_uncached`; `send` wraps it:

```python
def send(self, spec):
    if self._cache is None or not is_cacheable(spec):
        return self._send_uncached(spec)
    key = cache_key(spec)
    hit = self._cache.get(key)
    if hit is not None:
        return hit
    response = self._send_uncached(spec)   # only returns on status < 400
    self._cache.set(key, response)
    return response
```

Only successful responses are cached (errors raise before `set`).

### 2. What is cacheable

`is_cacheable(spec)` → `spec.method in ("GET", "POST")`. In VNDB Kana, reads are
`GET` (stats/user/…) and `POST` (query endpoints); writes are `PATCH`/`DELETE`
(ulist/rlist) and bypass the cache (never read, never written). TTL-only expiry.

### 3. New module `src/vndb_client/_cache.py` (private)

- `ResponseCache(ttl: float, maxsize: int = 128, *, clock=time.monotonic)`:
  `get(key) -> httpx.Response | None` (None on miss/expiry), `set(key, response)`.
  Bounded LRU via `OrderedDict` (evict oldest beyond `maxsize`). The injectable
  `clock` keeps expiry tests hermetic.
- `cache_key(spec) -> tuple`: stable key from
  `(method, path, json.dumps(json, sort_keys=True), json.dumps(params, sort_keys=True))`.
  The `user` param lives in the POST body, so user-scoped queries get distinct
  keys.
- `is_cacheable(spec) -> bool`.

Caching the fully-read `httpx.Response` is safe: httpx buffers `.content` after
the first read, so the client's `core.decode_json(response)` (`response.json()`)
works on a re-served hit.

### 4. Enablement

`Client(..., cache_ttl: float | None = None, cache_maxsize: int = 128)` and the
same on `AsyncClient`. `cache_ttl=None` (default) → caching off, byte-identical
to today. When set, the client forwards `cache_ttl`/`cache_maxsize` to its
transport, which constructs a `ResponseCache`. Per-client only (no shared/global
cache).

## Testing

- `ResponseCache` unit tests (injected clock): hit, miss-on-absent, expiry after
  ttl, LRU eviction at maxsize.
- `cache_key`: identical spec → identical key; differing method/path/json/params
  → distinct keys. `is_cacheable`: GET/POST True, PATCH/DELETE False.
- Transport integration (httpx `MockTransport` with a call counter): two
  identical reads with `cache_ttl` set → one network call; a `PATCH` write →
  always a network call; after the clock advances past the TTL → refetch.
- Client wiring: `Client(cache_ttl=...)` with repeated `vn.query(...)` → one
  network call; `cache_ttl=None` → every call hits network (unchanged).

## Out of scope

- ETag / conditional requests.
- Write-triggered invalidation.
- Cross-client / shared / persistent (disk, Redis) caches.
- Caching error responses.

## Risk / notes

- **Auth correctness:** the cache is per-client / per-token by construction, and
  `user` is part of the key via the request body. Documented that a cache is not
  shared across clients.
- **Response reuse:** only fully-read successful responses are cached; safe for
  repeated `.json()`. Writes never enter the cache, so mutations are only stale
  within the read TTL window.
