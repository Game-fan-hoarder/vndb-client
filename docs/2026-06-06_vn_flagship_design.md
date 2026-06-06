# VN Flagship Entity — Design

**Date:** 2026-06-06
**Epic:** `vndb-client-wj7` — VN flagship entity (MVP)
**Milestone:** MVP
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans
**Builds on:** Foundation (`docs/2026-06-05_foundation_design.md`) — `Client`/`AsyncClient`
with internal generic `_query(endpoint, model, **params) -> Page[T]`, `VndbModel`,
`Page[T]`, exception hierarchy.

## Purpose

Prove the full request pipeline end-to-end on the flagship entity (VN) and
establish the reusable conventions that the remaining 7 query entities will
follow: a generic query resource, a "model → fields" derivation, typed entity
models with nested sub-models, and forward-compatible handling of closed-set
integer fields. Outcome: `Client().vn.query(...)` and `await
AsyncClient().vn.query(...)` return a typed `Page[VN]`.

## Decisions (this design)

| Decision | Choice |
|----------|--------|
| VN model scope | Core scalars + nested `image` + `titles[]`/`aliases[]`. Relational fields (tags/relations/developers/staff/va/screenshots/extlinks) deferred. |
| Field selection | `vn.query()` defaults `fields` to the model's full declared set (derived via `field_spec`), overridable by passing `fields=`. |
| Resource design | Generic `QueryResource`/`AsyncQueryResource` parameterized by `(client, endpoint, model)`; VN is an instantiation. Future entities instantiate the same base. |
| Closed-set ints | Typed as `int \| None`; readable `IntEnum` *mirror* constants (`DevStatus`, `VNLength`) provided for comparison but NOT used as field types (forward-compatible if VNDB adds values). |
| `released` | Kept as `str` (VNDB partial dates + sentinels like `"TBA"`/`"today"`). |
| `description` | Kept raw (VNDB markup; parsing out of scope). |

## Module layout (`src/vndb_client/`)

| Module | Responsibility |
|--------|----------------|
| `fields.py` | `field_spec(model: type[VndbModel]) -> str` — reflect over `model_fields`, use each field's alias-or-name, recurse into nested `VndbModel` sub-models with dotted paths (`image` → `image.id,image.url,…`; `titles` → `titles.lang,…`; list-of-scalar like `aliases` stays bare). The reusable "model → fields" convention. |
| `resource.py` | `QueryResource(Generic[ModelT])` (sync) and `AsyncQueryResource(Generic[ModelT])` (async), constructed with `(client, endpoint, model)`. Each exposes `query(*, filters=None, fields=None, sort=None, reverse=None, results=None, page=None, count=False) -> Page[ModelT]`; defaults `fields` to `field_spec(model)`, forwards the rest to `client._query`. Imports `Client`/`AsyncClient` only under `TYPE_CHECKING` to avoid a circular import. |
| `entities/vn.py` | `VN` model + `Title`, `Image` sub-models + `DevStatus`/`VNLength` IntEnum mirror constants. |
| `entities/__init__.py` | Re-export entity symbols. |

Wiring & exports:
- `Client.__init__` sets `self.vn = QueryResource(self, "vn", VN)`; `AsyncClient.__init__`
  sets `self.vn = AsyncQueryResource(self, "vn", VN)`. Both typed `Page[VN]` via the generic.
- `__init__.py` adds `VN`, `Title`, `Image`, `DevStatus`, `VNLength` to the public API and `__all__`.

## VN model (`entities/vn.py`)

All inherit `VndbModel` (`populate_by_name`, `extra="ignore"`; absent fields → `None`).

Mirror constants (not field types):
- `DevStatus(IntEnum)`: `FINISHED=0`, `IN_DEVELOPMENT=1`, `CANCELLED=2`.
- `VNLength(IntEnum)`: `VERY_SHORT=1`, `SHORT=2`, `MEDIUM=3`, `LONG=4`, `VERY_LONG=5`.

`Image` (nested `image`):
`id: str`, `url: str | None`, `dims: list[int] | None` (`[w, h]`), `sexual: float | None`,
`violence: float | None`, `votecount: int | None`, `thumbnail: str | None`,
`thumbnail_dims: list[int] | None`.

`Title` (items of `titles[]`):
`lang: str`, `title: str | None`, `latin: str | None`, `official: bool | None`, `main: bool | None`.

`VN`:
| field | type | notes |
|---|---|---|
| `id` | `str` | always present |
| `title` | `str \| None` | main display title |
| `alttitle` | `str \| None` | |
| `titles` | `list[Title] \| None` | nested → dotted fields |
| `aliases` | `list[str] \| None` | |
| `olang` | `str \| None` | original language |
| `devstatus` | `int \| None` | compare vs `DevStatus` |
| `released` | `str \| None` | partial date / `"TBA"` — kept as `str` |
| `languages` | `list[str] \| None` | |
| `platforms` | `list[str] \| None` | |
| `image` | `Image \| None` | nested → dotted fields |
| `length` | `int \| None` | compare vs `VNLength` |
| `length_minutes` | `int \| None` | |
| `length_votes` | `int \| None` | |
| `description` | `str \| None` | raw VNDB markup |
| `rating` | `float \| None` | bayesian 10–100 |
| `votecount` | `int \| None` | |
| `average` | `float \| None` | raw average |

## Data flow

Sync (async identical bar `await`):
```
client.vn.query(filters=["search", "=", "saya"], results=5)
  -> QueryResource.query: fields defaults to field_spec(VN)
  -> client._query("vn", VN, filters=..., fields=<derived>, results=5)   [Foundation]
  -> core.build_query_request -> transport.send (retry/errors) -> core.parse_page
  -> Page[VN]   (results: list[VN], more: bool, count: int | None)
```
Caller may override `fields="id,title"` to narrow, or pass `count=True` for the total.

## Testing (mocked httpx, same pattern as Foundation)

- `tests/test_fields.py` — `field_spec`: flat model → alias comma list; nested sub-model
  → dotted paths (`image.url`); list-of-submodel → dotted (`titles.lang`); list-of-scalar
  stays bare (`aliases`).
- `tests/test_entities_vn.py` — parse a realistic `/vn` payload into `VN`: nested `image`
  is `Image`, `titles` are `Title`, scalars populated, an absent field is `None`,
  `DevStatus.FINISHED == vn.devstatus` comparison works.
- `tests/test_resource.py` — injected `httpx.MockTransport`: `Client(http_client=mock).vn.query(...)`
  returns `Page[VN]`; default POST body `fields` equals `field_spec(VN)`; `filters`/`results`/
  `page`/`count` forwarded; explicit `fields=` overrides; async equivalent via `asyncio.run`.
  A capturing handler inspects the request body.

## Docs

- Add `::: vndb_client.entities.vn` to `docs/modules.md`.
- Add a short `Client().vn.query(...)` usage snippet (full guides are a V1 epic).

## Out of scope (later epics)

- Relational VN fields (tags/relations/developers/editions/staff/va/screenshots/extlinks).
- Fluent query builder / filter DSL (filters stay raw lists here).
- Auto-pagination iterator.
- The other 7 query entities (they instantiate the same `QueryResource`).
