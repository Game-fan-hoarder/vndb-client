## 1. Ulist read models (`entities/ulist.py`)

- [x] 1.1 Write tests (`tests/test_entities_ulist.py`): parse a realistic `/ulist` entry into `UlistEntry` — scalars populate (with `None` where the API returns null); `labels[0]` is `UlistEntryLabel` (`id` is `int`); `vn` is `UlistVN` (id/title); `field_spec(UlistEntry)` contains `labels.id` and `vn.title` and does NOT contain `releases`
- [x] 1.2 Implement `src/vndb_client/entities/ulist.py`: `UlistVN(VndbModel)` (`id: str`, `title: str | None`), `UlistEntryLabel(VndbModel)` (`id: int`, `label`/`private` optional), `UlistEntry(VndbModel)` (`id: str`, `added`/`voted`/`lastmod`/`vote: int | None`, `started`/`finished`/`notes: str | None`, `labels: list[UlistEntryLabel] | None`, `vn: UlistVN | None`)

## 2. QueryResource `user` parameter (`resource.py`)

- [x] 2.1 Write tests (extend `tests/test_resource.py`): `client.vn.query(user="u2")` puts `"user": "u2"` in the request body; `client.vn.query()` (no user) puts no `user` key in the body (regression — other params still work)
- [x] 2.2 Edit `src/vndb_client/resource.py`: add `user: str | None = None` (keyword-only) to `QueryResource.query` and `AsyncQueryResource.query`, and pass `user=user` through to `client._query(...)` (which forwards to `core.build_query_request`, already accepting `user`)

## 3. Wire ulist read (`client.py`)

- [x] 3.1 Write tests (extend `tests/test_resource.py`, mocked transport): `Client().ulist` is a `QueryResource` and `AsyncClient().ulist` is an `AsyncQueryResource`; `client.ulist.query(user="u2")` POSTs to `/ulist` with `"user": "u2"` and returns a `Page[UlistEntry]` whose results are `UlistEntry`; default `fields` equals `field_spec(UlistEntry)`; async equivalent
- [x] 3.2 Edit `src/vndb_client/client.py`: import `UlistEntry`; wire `self.ulist: QueryResource[UlistEntry] = QueryResource(self, "ulist", UlistEntry)` in `Client.__init__` and the `AsyncQueryResource[UlistEntry]` variant in `AsyncClient.__init__`

## 4. Write support: sentinel, RListStatus, `_write` + 4 methods

- [x] 4.1 Write tests (`tests/test_ulist_writes.py`, injected `httpx.MockTransport` returning `204`, capturing method/path/body): `set_ulist("v17", vote=80, notes="x")` → `PATCH` to `/ulist/v17` body `{"vote": 80, "notes": "x"}`, returns `None`; `set_ulist("v17", vote=None)` → body `{"vote": None}`; `set_ulist("v17")` → body `{}`; `set_ulist("v17", labels_set=[1, 2])` → body has `labels_set`; `delete_ulist("v17")` → `DELETE /ulist/v17`; `set_rlist("r5", status=2)` → `PATCH /rlist/r5` body `{"status": 2}` and `RListStatus.OBTAINED == 2`; `delete_rlist("r5")` → `DELETE /rlist/r5`; a write receiving `401` raises `VndbAuthError`; async equivalents via `asyncio.run`
- [x] 4.2 Add to `src/vndb_client/entities/ulist.py`: `class UnsetType` (with `__repr__` → `"UNSET"`) and `UNSET = UnsetType()`; `class RListStatus(IntEnum)` (`UNKNOWN=0`,`PENDING=1`,`OBTAINED=2`,`ON_LOAN=3`,`DELETED=4`)
- [x] 4.3 Implement on `Client` and `AsyncClient` (`client.py`): a private `_write(self, method, path, *, json=None) -> None` building `core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)`, calling `self._transport.send(spec)` (async: `await`), returning `None`; then `set_ulist(vn_id, *, vote=UNSET, notes=UNSET, started=UNSET, finished=UNSET, labels=None, labels_set=None, labels_unset=None)` (build body: include each scalar when `is not UNSET`, include each label list when `is not None`; `PATCH /ulist/<vn_id>`), `delete_ulist(vn_id)` (`DELETE`), `set_rlist(release_id, *, status)` (`PATCH /rlist/<release_id>` body `{"status": status}`), `delete_rlist(release_id)` (`DELETE`). Import `UNSET`, `UnsetType` for the signatures.

## 5. Public exports

- [x] 5.1 Write tests (extend `tests/test_public_api.py`): `UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, `UNSET` importable from `vndb_client` and in `__all__`
- [x] 5.2 Edit `src/vndb_client/__init__.py` to import and export `UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, `UNSET` (add to `__all__`; let `ruff check --fix` order it)

## 6. Docs & quality gate

- [x] 6.1 Add a read+write usage snippet (`client.ulist.query(user="u2")`, `client.set_ulist("v17", vote=90)`) and `::: vndb_client.entities.ulist` to `docs/modules.md`; verify `uv run mkdocs build --strict`
- [x] 6.2 Run the full gate green: `uv run python -m pytest`, `uv run mypy`, `uv run ruff format`/`check`, `uv run deptry src`, and `tox` (py310–py314)
