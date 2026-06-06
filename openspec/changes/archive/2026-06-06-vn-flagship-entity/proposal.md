## Why

The Foundation provides a generic, internal `_query` primitive but no public,
typed way to query a database entity. The VN (visual novel) entity is the
flagship: implementing it end-to-end proves the full pipeline and establishes
the reusable conventions — a generic query resource, a model→fields derivation,
and typed entity models — that the remaining 7 query entities will follow.

## What Changes

- Add a generic `QueryResource` (sync) and `AsyncQueryResource` (async),
  parameterized by `(client, endpoint, model)`, each exposing
  `query(*, filters, fields, sort, reverse, results, page, count) -> Page[model]`.
- Add `field_spec(model)`: derive the VNDB `fields` request string from a
  `VndbModel` by reflecting over its fields (alias-or-name) and recursing into
  nested sub-models with dotted paths. `query()` defaults `fields` to this when
  the caller omits it, and the caller may override it.
- Add the `VN` entity model (core scalars + nested `image` + `titles[]` /
  `aliases[]`), with `Title` and `Image` sub-models and `DevStatus` / `VNLength`
  IntEnum mirror constants (the closed-set int fields stay `int | None`).
- Wire `client.vn` on both `Client` and `AsyncClient` so `Client().vn.query(...)`
  and `await AsyncClient().vn.query(...)` return a typed `Page[VN]`.
- Export `VN`, `Title`, `Image`, `DevStatus`, `VNLength` from the package root.
- Add docs API reference for the VN entity and a short usage snippet.

## Capabilities

### New Capabilities

- `query-resource`: The generic, reusable query resource (sync + async) and the
  model→fields derivation / field-selection behavior shared by all query
  entities.
- `vn-entity`: The `VN` model (and its sub-models / mirror constants) and the
  `client.vn` query surface returning `Page[VN]`.

### Modified Capabilities

<!-- None. The Foundation capabilities (http-transport, request-retry,
error-handling, response-envelope) are reused unchanged. -->

## Impact

- **New modules** under `src/vndb_client/`: `fields.py`, `resource.py`,
  `entities/__init__.py`, `entities/vn.py`; modifications to `client.py`
  (wire `self.vn`) and `__init__.py` (exports).
- **No new runtime dependencies.**
- **Public API surface grows:** `VN`, `Title`, `Image`, `DevStatus`, `VNLength`,
  and the `.vn` resource attribute on clients.
- **No breaking changes** (purely additive; the internal `_query` primitive is
  unchanged).
- **Out of scope** (later epics): relational VN fields, the fluent query builder,
  auto-pagination, and the other 7 query entities.
