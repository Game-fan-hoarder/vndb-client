## 1. Meta models (`meta.py`)

- [x] 1.1 Write tests (`tests/test_meta.py`): parse sample payloads into `Stats` (7 int counts), `AuthInfo` (id/username/permissions), `User` (id/username/lengthvotes/lengthvotes_sum), `UlistLabel` (id is `int`, label/private/count); an omitted optional (e.g. `User.lengthvotes`) is `None`
- [x] 1.2 Implement `src/vndb_client/meta.py`: `Stats` (`chars`/`producers`/`releases`/`staff`/`tags`/`traits`/`vn`: `int`), `AuthInfo` (`id: str`, `username`/`permissions` optional), `User` (`id: str`, `username`/`lengthvotes`/`lengthvotes_sum` optional), `UlistLabel` (`id: int`, `label`/`private`/`count` optional) — all `VndbModel`

## 2. GET helper + client methods (`client.py`)

- [x] 2.1 Write tests (`tests/test_get_endpoints.py`, injected `httpx.MockTransport` + a handler capturing method/path/query): `stats()` GETs `/stats` → `Stats`; `authinfo()` GETs `/authinfo` and sends `Authorization: Token <tok>` when a token is set → `AuthInfo`; `get_user(["u1","Nemo"], fields="lengthvotes")` GETs `/user` with repeated `q` + `fields`, returns `dict[str, User|None]` with a `null` value → `None`; `ulist_labels(user="u1", fields="count")` GETs `/ulist_labels` → `list[UlistLabel]` (unwrapped from `labels`); `schema()` returns the raw dict; `ulist_labels()` (no args) sends no `user`/`fields` params; async equivalents via `asyncio.run`
- [x] 2.2 Implement on `Client` and `AsyncClient` in `src/vndb_client/client.py`: a private `_get(self, path, *, params=None)` building `RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=<params with None values dropped>)`, calling `self._transport.send(spec)`, returning `response.json()` (wrap `ValueError` → `VndbParseError`); then `stats()`, `authinfo()`, `get_user(q, *, fields=None)`, `ulist_labels(user=None, *, fields=None)`, `schema()` — sync versions on `Client`, async (awaiting `_get`) on `AsyncClient`. `get_user` builds `params={"q": q, "fields": fields}` and parses the response map values into `User | None`; `ulist_labels` builds `params={"user": user, "fields": fields}` and parses `response["labels"]` into `list[UlistLabel]`

## 3. Public exports

- [x] 3.1 Write tests (extend `tests/test_public_api.py`): `Stats`, `AuthInfo`, `User`, `UlistLabel` importable from `vndb_client` and in `__all__`
- [x] 3.2 Edit `src/vndb_client/__init__.py` to import and export `Stats`, `AuthInfo`, `User`, `UlistLabel` (add to `__all__`)

## 4. Docs & quality gate

- [x] 4.1 Add a usage snippet (`client.stats()`, `client.get_user(...)`) and `::: vndb_client.meta` to `docs/modules.md`; verify `uv run mkdocs build --strict`
- [x] 4.2 Run the full gate green: `uv run python -m pytest`, `uv run mypy`, `uv run ruff format`/`check`, `uv run deptry src`, and `tox` (py310–py314)
