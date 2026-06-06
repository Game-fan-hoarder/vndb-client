# Simple GET Endpoints — Design

**Date:** 2026-06-06
**Epic:** `vndb-client-5sh` — Simple GET endpoints (Beta): /stats /user /authinfo /schema /ulist_labels
**Milestone:** Beta
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans
**Builds on:** Foundation transport (`transport.send(RequestSpec)` already supports
GET via method/params), `VndbModel`, exception hierarchy. No query-resource involvement.

## Purpose

Round out non-query API coverage with the 5 simple GET endpoints, exposed as
direct client methods returning typed models (raw dict for `/schema`).

## Decisions

| Decision | Choice |
|----------|--------|
| Client surface | Direct methods on `Client`/`AsyncClient` (`stats`, `authinfo`, `get_user`, `ulist_labels`, `schema`) — these are one-shot GETs, not query resources. |
| GET plumbing | A private `_get(path, *, params=None) -> Any` builds a GET `RequestSpec`, calls `transport.send` (retry/errors/auth header apply), returns `response.json()` (decode failure → `VndbParseError`). `core` stays generic. |
| Response models | Typed `VndbModel`s for the 4 structured endpoints (`Stats`, `AuthInfo`, `User`, `UlistLabel`); `/schema` returned as `dict[str, Any]` (huge, arbitrary, evolving metadata — modeling it is impractical and low-value). |
| Module | New `src/vndb_client/meta.py` (these are not query entities). |
| `get_user` shape | Returns `dict[str, User | None]` keyed by each `q` (VNDB returns `null` for unknown lookups). |
| `ulist_labels` shape | Unwraps the `{"labels": [...]}` envelope → `list[UlistLabel]`. |
| Param handling | `_get` filters out `None`-valued params so optional params are omitted from the query string. |

## GET plumbing

`Client._get` / `AsyncClient._get`:
```
spec = RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=<params without None values>)
response = (await) self._transport.send(spec)
try: return response.json()
except ValueError as exc: raise VndbParseError(str(exc)) from exc
```
`RequestSpec` and `transport.send` already exist; `core.build_query_request`
(POST-only) is not used.

## Client methods (sync on `Client`, async on `AsyncClient`)

| Method | Endpoint | Params | Returns |
|--------|----------|--------|---------|
| `stats()` | `GET /stats` | — | `Stats` |
| `authinfo()` | `GET /authinfo` | (token required) | `AuthInfo` |
| `get_user(q, *, fields=None)` | `GET /user` | `q: str \| list[str]` (repeatable), `fields: str \| None` | `dict[str, User \| None]` |
| `ulist_labels(user=None, *, fields=None)` | `GET /ulist_labels` | `user: str \| None`, `fields: str \| None` | `list[UlistLabel]` |
| `schema()` | `GET /schema` | — | `dict[str, Any]` |

`get_user` parses each value of the response map into `User` (or `None`).
`ulist_labels` parses `response["labels"]` into `list[UlistLabel]`.

## Models (`meta.py`, inheriting `VndbModel`)

- **`Stats`**: `chars: int`, `producers: int`, `releases: int`, `staff: int`,
  `tags: int`, `traits: int`, `vn: int` (always-complete aggregate; required).
- **`AuthInfo`**: `id: str`, `username: str | None = None`,
  `permissions: list[str] | None = None`.
- **`User`**: `id: str`, `username: str | None = None`,
  `lengthvotes: int | None = None`, `lengthvotes_sum: int | None = None`.
- **`UlistLabel`**: `id: int` (integer, NOT a vndbid string),
  `label: str | None = None`, `private: bool | None = None`,
  `count: int | None = None`.

All four models + the 5 methods are available from the package root
(`Stats`, `AuthInfo`, `User`, `UlistLabel` exported from `vndb_client`).

## Testing (mocked httpx, capturing handler)

- `tests/test_meta.py` — parse sample payloads into `Stats`/`AuthInfo`/`User`/
  `UlistLabel`; `UlistLabel.id` is `int`; omitted optional (e.g. `User.lengthvotes`)
  → `None`.
- `tests/test_get_endpoints.py` — injected `httpx.MockTransport` + a handler
  capturing method/path/params:
  - `stats()` GETs `/stats` → `Stats`.
  - `authinfo()` GETs `/authinfo`, sends `Authorization: Token <token>` when set → `AuthInfo`.
  - `get_user(["u1", "Nemo"], fields="lengthvotes")` GETs `/user` with repeated
    `q` + `fields`, returns `dict[str, User | None]`; a `null` value → `None`.
  - `ulist_labels(user="u1", fields="count")` GETs `/ulist_labels`, returns
    `list[UlistLabel]` unwrapped from `{"labels": [...]}`.
  - `schema()` returns the raw dict unchanged.
  - `None` params omitted from the query string (e.g. `ulist_labels()` sends no `user`/`fields`).
  - async equivalents via `asyncio.run`.
- `tests/test_public_api.py` (extend) — `Stats`/`AuthInfo`/`User`/`UlistLabel`
  exported and in `__all__`.

## Docs

- Add a usage snippet (`client.stats()`, `client.get_user(...)`) + `::: vndb_client.meta`
  to `docs/modules.md`; verify `mkdocs build --strict`.

## Out of scope (later epics)

- ulist read/write (the `04j` epic).
- Auto-pagination; modeling `/schema`.
