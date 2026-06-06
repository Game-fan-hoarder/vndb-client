## Why

The client covers public read endpoints but not authenticated user-list
management. This adds reading a user's list (`POST /ulist`) and modifying ulist/
rlist entries (`PATCH`/`DELETE`) — the first authenticated write path — completing
list coverage and unblocking the V1 release epic.

## What Changes

- Add a `user` parameter to `QueryResource.query` / `AsyncQueryResource.query`
  (forwarded to `build_query_request`, which already accepts it) — needed by
  `/ulist` and harmless for other entities (closes follow-up `dgl`).
- Add `src/vndb_client/entities/ulist.py`: read models `UlistEntry`,
  `UlistEntryLabel`, `UlistVN`; the `UnsetType`/`UNSET` write sentinel; and the
  `RListStatus` IntEnum mirror.
- Wire `client.ulist = QueryResource(self, "ulist", UlistEntry)` on both clients
  (read via `client.ulist.query(user="u2", ...)`).
- Add a private `_write(method, path, *, json=None) -> None` helper and 4 write
  methods on both clients:
  - `set_ulist(vn_id, *, vote, notes, started, finished, labels, labels_set, labels_unset)` → `PATCH /ulist/<vn_id>`
  - `delete_ulist(vn_id)` → `DELETE /ulist/<vn_id>`
  - `set_rlist(release_id, *, status)` → `PATCH /rlist/<release_id>`
  - `delete_rlist(release_id)` → `DELETE /rlist/<release_id>`
  - `set_ulist` uses the `UNSET` sentinel so omit (leave unchanged) is distinct
    from explicit `None` (unset on server).
- Export `UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, `UNSET` from
  the package root.
- Add docs (read + write usage + API reference).

## Capabilities

### New Capabilities

- `user-lists`: Reading a user's list (`POST /ulist` query → `Page[UlistEntry]`)
  and authenticated ulist/rlist writes (`PATCH`/`DELETE`), with the `UNSET`
  sentinel and `RListStatus` mirror.

### Modified Capabilities

<!-- None at the requirement level. `QueryResource.query` gains an additive
`user` param (raw/existing usage unchanged); treated as additive, not a
requirement change to query-resource. -->

## Impact

- **New module** `src/vndb_client/entities/ulist.py`.
- **Edited:** `src/vndb_client/resource.py` (add `user` param), `src/vndb_client/client.py`
  (wire `client.ulist` + `_write` + 4 write methods), `src/vndb_client/__init__.py`
  (exports), `docs/modules.md`.
- **No new runtime dependencies; no breaking changes** (additive; `core`/transport
  unchanged — transport already supports PATCH/DELETE + json + 204).
- **Auth:** writes require a `listwrite` token; private ulist reads require
  `listread`. Missing/invalid token surfaces as `VndbAuthError` via existing mapping.
- **Out of scope:** the `releases[]` array on ulist entries; auto-pagination.
