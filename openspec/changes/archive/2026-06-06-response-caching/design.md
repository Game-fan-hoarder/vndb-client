## Context

Reads flow through `SyncTransport.send` / `AsyncTransport.send`, which retry then
return an `httpx.Response`; the client decodes via `core.decode_json`. Each
transport is built per-`Client` with that client's token in its headers. The full
approved design is at `design/2026-06-06_response_caching_design.md`; this records
decisions.

## Goals / Non-Goals

**Goals:**

- Opt-in in-memory TTL cache that serves recent identical reads without a network
  call.
- Correct for auth'd/user-scoped data (no cross-token leakage; per-user keys).
- Never cache or stale writes.

**Non-Goals:**

- ETag/conditional requests; write-triggered invalidation; shared/persistent
  caches; caching error responses.

## Decisions

- **Cache at the transport `send` chokepoint.** Every request passes through it,
  and the transport is per-client with the token baked into its headers, so a
  transport-bound cache is token-scoped by construction. Extract the retry loop
  into `_send_uncached`; `send` consults the cache around it.
- **GET + POST are cacheable; PATCH/DELETE bypass.** VNDB reads are GET (meta) and
  POST (query endpoints); writes are PATCH/DELETE. Writes never read or populate
  the cache. Alternative (cache only GET) was rejected — it would miss all the
  query traffic, which is the point.
- **TTL-only expiry, no write-invalidation.** Cached keys are query-shaped and
  can't be cleanly mapped to which results a ulist write affects; bounding
  staleness by TTL is simpler and predictable.
- **Cache only successful responses.** `_send_uncached` returns only on `< 400`
  (else raises), so errors are never cached.
- **Injectable clock.** `ResponseCache` takes `clock=time.monotonic` so expiry is
  testable without sleeping.
- **Cache the `httpx.Response` object.** httpx buffers `.content` after the first
  read, so re-serving a read response supports repeated `.json()`. Avoids a
  parallel decoded-payload cache layer.

## Risks / Trade-offs

- **Cross-token leakage** → mitigated structurally (per-client cache) and by
  including the body (which carries `user`) in the key; documented that caches
  are not shared across clients.
- **Stale reads after a write** → bounded by the TTL; writes themselves are never
  cached. Documented as the explicit trade-off of TTL-only invalidation.
- **Unbounded memory** → `maxsize` LRU eviction via `OrderedDict`.
- **Response object reuse across callers** → safe because callers only read
  (`.json()`/`.text`) and content is buffered; no mutation of the response.
