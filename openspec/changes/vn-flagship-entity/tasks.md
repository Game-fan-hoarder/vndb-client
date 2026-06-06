## 1. Model→fields derivation (`fields.py`)

- [ ] 1.1 Write tests (`tests/test_fields.py`) for `field_spec`: a flat model with an aliased field emits alias-or-name comma list; a field whose type is a nested `VndbModel` emits dotted paths (`image.id`,`image.url`); a `list[VndbModel]` field emits dotted paths (`titles.lang`); a `list[str]` field emits a bare name (`aliases`)
- [ ] 1.2 Implement `src/vndb_client/fields.py` `field_spec(model: type[VndbModel]) -> str`: iterate `model.model_fields`, use `field_info.alias or name`, unwrap `Optional`/`list`, recurse when the inner type is a `VndbModel` subclass prefixing `"<key>."`, join with commas

## 2. VN entity model (`entities/vn.py`)

- [ ] 2.1 Write tests (`tests/test_entities_vn.py`): parse a realistic `/vn` payload into `VN` (scalars populated, `image` is `Image`, `titles` are `Title`); an omitted field parses as `None`; `DevStatus.FINISHED == vn.devstatus` when devstatus is 0; an unknown `devstatus`/`length` int still parses
- [ ] 2.2 Implement `src/vndb_client/entities/vn.py`: `DevStatus`/`VNLength` IntEnum mirror constants; `Image` and `Title` sub-models; `VN` model (fields per the design table; `devstatus`/`length` typed `int | None`; `released` typed `str | None`)
- [ ] 2.3 Create `src/vndb_client/entities/__init__.py` re-exporting `VN`, `Title`, `Image`, `DevStatus`, `VNLength`

## 3. Generic query resource (`resource.py`)

- [ ] 3.1 Write tests (`tests/test_resource.py`) using `httpx.MockTransport` with a capturing handler: `Client(http_client=mock).vn.query()` issues a POST whose body `fields` equals `field_spec(VN)`; an explicit `fields=` overrides it; `filters`/`results`/`page`/`count` are forwarded into the body; the result is a `Page[VN]` with `VN` results; async equivalent via `asyncio.run`
- [ ] 3.2 Implement `src/vndb_client/resource.py`: `QueryResource(Generic[ModelT])` and `AsyncQueryResource(Generic[ModelT])` with `__init__(self, client, endpoint, model)` (import `Client`/`AsyncClient` under `TYPE_CHECKING`) and `query(*, filters=None, fields=None, sort=None, reverse=None, results=None, page=None, count=False) -> Page[ModelT]` defaulting `fields` to `field_spec(model)` and forwarding to `client._query`; async version awaits

## 4. Wire client surface & public exports

- [ ] 4.1 Write tests (`tests/test_client.py` additions or `tests/test_resource.py`): `Client().vn` is a `QueryResource` and `AsyncClient().vn` is an `AsyncQueryResource`; `VN`, `Title`, `Image`, `DevStatus`, `VNLength` are importable from `vndb_client` and present in `__all__`
- [ ] 4.2 Wire `self.vn = QueryResource(self, "vn", VN)` in `Client.__init__` and `self.vn = AsyncQueryResource(self, "vn", VN)` in `AsyncClient.__init__` (import VN + resources in `client.py`)
- [ ] 4.3 Add `VN`, `Title`, `Image`, `DevStatus`, `VNLength` to `src/vndb_client/__init__.py` imports and `__all__`

## 5. Docs & quality gate

- [ ] 5.1 Add `::: vndb_client.entities.vn` to `docs/modules.md` and a short `Client().vn.query(...)` usage snippet; verify `uv run mkdocs build --strict` passes
- [ ] 5.2 Run the full gate green: `uv run python -m pytest`, `uv run mypy`, `uv run ruff format`/`check`, `uv run deptry src`, and `tox` (py310–py314)
