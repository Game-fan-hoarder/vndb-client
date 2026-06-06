## Why

The client covers the POST query endpoints but none of VNDB's simple GET
endpoints (`/stats`, `/authinfo`, `/user`, `/ulist_labels`, `/schema`).
Implementing them rounds out non-query API coverage and is small — the Foundation
transport already supports GET; this adds a GET helper, typed response models, and
direct client methods.

## What Changes

- Add a private `_get(path, *, params=None) -> Any` on `Client`/`AsyncClient`
  (builds a GET `RequestSpec`, drops `None`-valued params, calls
  `transport.send`, returns `response.json()`; decode failure → `VndbParseError`).
- Add `src/vndb_client/meta.py` with typed models `Stats`, `AuthInfo`, `User`,
  `UlistLabel`.
- Add 5 direct client methods (sync + async):
  - `stats() -> Stats`
  - `authinfo() -> AuthInfo`
  - `get_user(q, *, fields=None) -> dict[str, User | None]`
  - `ulist_labels(user=None, *, fields=None) -> list[UlistLabel]`
  - `schema() -> dict[str, Any]` (raw)
- Export `Stats`, `AuthInfo`, `User`, `UlistLabel` from the package root.
- Add docs (usage snippet + API reference).

## Capabilities

### New Capabilities

- `simple-get-endpoints`: GET helper + typed models + direct client methods for
  `/stats`, `/authinfo`, `/user`, `/ulist_labels`, and `/schema`.

### Modified Capabilities

<!-- None at the requirement level. The Foundation transport/`RequestSpec` are
reused unchanged; adding client methods is additive. -->

## Impact

- **New module** `src/vndb_client/meta.py`.
- **Edited:** `src/vndb_client/client.py` (add `_get` + 5 methods on each client),
  `src/vndb_client/__init__.py` (exports), `docs/modules.md`.
- **No new runtime dependencies; no breaking changes** (purely additive; `core`
  and transport unchanged).
- **Out of scope** (later epics): ulist read/write (`04j`); auto-pagination;
  modeling `/schema`.
