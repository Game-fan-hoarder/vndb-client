## 1. The cache module (`_cache.py`)

- [ ] 1.1 Create `src/vndb_client/_cache.py` with `is_cacheable(spec)` (`GET`/`POST` → True, `PATCH`/`DELETE` → False) and `cache_key(spec)` (stable tuple of method, path, sorted-JSON body, sorted-JSON params)
- [ ] 1.2 Test (`tests/test_cache.py`): `is_cacheable` for each method; `cache_key` identical for identical specs and distinct for differing method/path/json/params
- [ ] 1.3 Implement `ResponseCache(ttl, maxsize=128, *, clock=time.monotonic)` with `get`/`set`, TTL expiry, and LRU eviction (`OrderedDict`)
- [ ] 1.4 Test (`tests/test_cache.py`, injected fake clock): hit, miss on absent key, miss after TTL elapses, LRU eviction beyond maxsize

## 2. Wire the cache into the transport

- [ ] 2.1 Extract the existing retry loop in `SyncTransport.send`/`AsyncTransport.send` into `_send_uncached`; add an optional `_cache` (built from `cache_ttl`/`cache_maxsize` ctor args) and make `send` serve hits / store successful cacheable responses around `_send_uncached`
- [ ] 2.2 Test (`tests/test_transport.py`, httpx `MockTransport` call counter): two identical cacheable reads → one network call; a `PATCH` write (repeated) → a network call each time; after the injected clock passes the TTL → refetch; with no cache → every call hits network

## 3. Expose on the clients

- [ ] 3.1 Add `cache_ttl: float | None = None` and `cache_maxsize: int = 128` to `Client` and `AsyncClient`, forwarded to their transports
- [ ] 3.2 Test (`tests/test_client.py` or `tests/test_resource.py`): `Client(cache_ttl=...)` repeated `vn.query(...)` issues one network call; `cache_ttl=None` issues one per call

## 4. Docs

- [ ] 4.1 Add a short "Response caching" section to a guide (e.g. `docs/guides/getting-started.md` or a note in `querying.md`) showing `Client(cache_ttl=60)` and noting reads-only, per-client, TTL-bounded staleness

## 5. Verification

- [ ] 5.1 `make check` (ruff, mypy, deptry) clean and `make test` passes with the coverage gate satisfied
- [ ] 5.2 `uv run mkdocs build --strict` exit 0
