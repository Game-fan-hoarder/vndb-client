# User Lists — Design

**Date:** 2026-06-06
**Epic:** `vndb-client-04j` — User lists: ulist read (Beta) then ulist/rlist writes (V1)
**Milestone:** Beta → V1 (both phases in this one cycle)
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans
**Builds on:** generic `QueryResource`/`AsyncQueryResource`, `field_spec`, `VndbModel`,
transport (`transport.send(RequestSpec)` supports any method + json + 204), exception hierarchy.

## Purpose

Add authenticated user-list management: read a user's list (`POST /ulist`, a query)
and modify ulist/rlist entries (`PATCH`/`DELETE`, the first authenticated write path).

## Decisions

| Decision | Choice |
|----------|--------|
| Scope | Both phases (read + writes) in one cycle/branch — same domain. |
| Read surface | Reuse the generic resource: `client.ulist = QueryResource(self, "ulist", UlistEntry)`, via `client.ulist.query(user="u2", ...)`. Requires adding a `user` param to `QueryResource.query` (closes follow-up `dgl`; harmless for other entities). |
| Write surface | Direct client methods `set_ulist`/`delete_ulist`/`set_rlist`/`delete_rlist` (like the GET-endpoint methods), backed by a private `_write(method, path, *, json=None) -> None`. |
| Omit vs unset | `set_ulist` nullable scalars (`vote`/`notes`/`started`/`finished`) default to an `UNSET` sentinel; only non-`UNSET` fields go in the PATCH body, and explicit `None` is sent as JSON `null` (server unsets). Label-list params use `None`=omit. |
| Nested `vn` | Minimal `UlistVN`(`id`, `title`) (consistent with the quote-ref convention; overridable via explicit `fields`). |
| `rlist` status | `status` stays a plain `int`; `RListStatus` IntEnum mirror provided. |
| Deferred | The `releases[]` array (with `list_status`) on ulist entries; auto-pagination. |

## Read side (`POST /ulist`)

- **`resource.py`:** add `user: str | None = None` to `QueryResource.query` /
  `AsyncQueryResource.query`, forwarded to `build_query_request` (which already
  accepts `user`).
- **`client.py`:** `self.ulist = QueryResource(self, "ulist", UlistEntry)` (async
  variant on `AsyncClient`).
- **`entities/ulist.py`** models (inherit `VndbModel`):
  - `UlistVN`: `id: str`, `title: str | None = None`
  - `UlistEntryLabel`: `id: int`, `label: str | None = None`, `private: bool | None = None`
  - `UlistEntry`: `id: str` (vn id), `added: int | None`, `voted: int | None`,
    `lastmod: int | None`, `vote: int | None`, `started: str | None`,
    `finished: str | None`, `notes: str | None`, `labels: list[UlistEntryLabel] | None`,
    `vn: UlistVN | None`

`field_spec(UlistEntry)` → `id,added,voted,lastmod,vote,started,finished,notes,labels.id,labels.label,labels.private,vn.id,vn.title`. Reading private labels needs a `listread` token (surfaced via existing auth handling).

## Write side (`PATCH`/`DELETE` `/ulist`, `/rlist`)

`entities/ulist.py` also defines:
- `UnsetType` + `UNSET = UnsetType()` (sentinel; `repr` → `"UNSET"`).
- `RListStatus(IntEnum)`: `UNKNOWN=0`, `PENDING=1`, `OBTAINED=2`, `ON_LOAN=3`, `DELETED=4`.

`client.py` private helper + 4 methods on each client:
```python
def _write(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> None:
    spec = core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)
    self._transport.send(spec)   # 204 → success; errors → raise_for_status; returns None
```

| Method | Endpoint | Body |
|--------|----------|------|
| `set_ulist(vn_id, *, vote=UNSET, notes=UNSET, started=UNSET, finished=UNSET, labels=None, labels_set=None, labels_unset=None)` | `PATCH /ulist/<vn_id>` | only fields ≠ `UNSET`; explicit `None` → `null` (unset); each label list included when not `None` |
| `delete_ulist(vn_id)` | `DELETE /ulist/<vn_id>` | — |
| `set_rlist(release_id, *, status)` | `PATCH /rlist/<release_id>` | `{"status": status}` (required) |
| `delete_rlist(release_id)` | `DELETE /rlist/<release_id>` | — |

All return `None`. All require a `listwrite` token; missing/invalid → `VndbAuthError`
(401) via existing transport mapping. Operations are idempotent, so the existing
429/5xx/network retry is safe.

`set_ulist` body construction: `if vote is not UNSET: body["vote"] = vote` (etc. for
notes/started/finished); `if labels is not None: body["labels"] = labels` (and
`labels_set`/`labels_unset`). So `set_ulist("v17", vote=None)` clears the vote;
`set_ulist("v17", notes="x")` touches only notes.

## Exports

`UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, `UNSET` from the package root.

## Testing (mocked httpx, capturing handler)

- `tests/test_entities_ulist.py` — parse a `/ulist` entry: scalars (incl. `None`),
  `labels[0]` is `UlistEntryLabel` (`id` int), `vn` is `UlistVN`; `field_spec(UlistEntry)`
  includes `labels.id`/`vn.title`, excludes `releases`.
- `tests/test_resource.py` (extend) — `client.ulist.query(user="u2", filters=...)` sends
  `"user": "u2"` in the body → `Page[UlistEntry]`; `user` omitted when not passed (other
  entity queries unaffected); async equivalent.
- `tests/test_ulist_writes.py` — mocked transport returning `204`, capturing method/path/body:
  - `set_ulist("v17", vote=80, notes="x")` → `PATCH /ulist/v17`, body `{"vote": 80, "notes": "x"}`; returns `None`.
  - `set_ulist("v17", vote=None)` → body `{"vote": None}`; `set_ulist("v17")` → body `{}`.
  - `set_ulist("v17", labels_set=[1, 2])` → body has `labels_set`.
  - `delete_ulist("v17")` → `DELETE /ulist/v17`.
  - `set_rlist("r5", status=2)` → `PATCH /rlist/r5`, body `{"status": 2}`; `RListStatus.OBTAINED == 2`.
  - `delete_rlist("r5")` → `DELETE /rlist/r5`.
  - a write hitting `401` raises `VndbAuthError`.
  - async equivalents via `asyncio.run`.
- `tests/test_public_api.py` (extend) — `UlistEntry`, `UlistEntryLabel`, `UlistVN`,
  `RListStatus`, `UNSET` exported and in `__all__`.

## Docs

- Add a usage snippet (read via `client.ulist.query(user=...)`, write via
  `client.set_ulist(...)`) + `::: vndb_client.entities.ulist` to `docs/modules.md`;
  verify `mkdocs build --strict`.

## Out of scope

- The `releases[]` array (with `list_status`) on ulist entries.
- Auto-pagination iterator.
