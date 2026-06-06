## Why

The clients accept `filters` only as a raw nested list matching VNDB's filter
DSL — powerful but error-prone and undiscoverable. A fluent, typed builder makes
filtering ergonomic and IDE-discoverable while still producing the exact raw
form the API expects, and degrading gracefully to raw lists.

## What Changes

- Add a `vndb_client.filters` package with builder primitives:
  - `Field` (operator dunders `==`/`!=`/`>=`/`>`/`<=`/`<` → `Comparison`)
  - `Predicate` base, `Comparison`, `Compound` (`&`/`|`, flattening same-kind chains)
  - `resolve_filters(filters)` → list (serializes a `Predicate`, passes raw through)
- Add 8 per-entity filter namespaces (`vn_filters`, `release_filters`,
  `producer_filters`, `character_filters`, `staff_filters`, `tag_filters`,
  `trait_filters`, `quote_filters`) covering each entity's documented filterable
  fields, plus a generic `field(name)` escape hatch.
- Support nested relational filters: a comparison's value may itself be a
  `Predicate`, serialized recursively.
- Widen `QueryResource.query` / `AsyncQueryResource.query` `filters` parameter to
  `Predicate | list | None`, resolving a `Predicate` to its list form before
  forwarding (raw lists keep working unchanged; `core` is untouched).
- Add docs (filter-DSL usage snippet + API reference).

## Capabilities

### New Capabilities

- `query-builder`: Fluent, typed filter builder — field references, comparison
  operators, and/or composition, nested relational filters, per-entity
  namespaces, a generic escape hatch, and serialization to the VNDB raw filter
  form via the query resource.

### Modified Capabilities

<!-- query-resource is reused; its `query` signature widens `filters` to accept a
Predicate, which is additive (raw lists still valid). Treated as additive, not a
requirement change, so no delta to the query-resource spec. -->

## Impact

- **New package** `src/vndb_client/filters/` (`predicate.py`, `namespaces.py`,
  `__init__.py`).
- **Edited:** `src/vndb_client/resource.py` (widen `filters` type + call
  `resolve_filters`), `docs/modules.md`.
- **No new runtime dependencies; no breaking changes** (raw-list filters and the
  existing `core`/transport are unchanged; the `query` change is additive).
- **Out of scope** (later epics): auto-pagination, ulist, per-field value typing,
  a NOT operator (no API support).
