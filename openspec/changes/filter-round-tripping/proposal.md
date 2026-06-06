## Why

VNDB can echo a query's filters back in two forms — a compact, opaque
server-encoded string (`compact_filters`) and an explicit nested list
(`normalized_filters`) — when the request asks for them. `Page` already parses
both, but `query()` cannot request them, and `filters` is not typed to accept a
returned compact string. So users cannot complete the round-trip (obtain a form,
feed it back). Converting between the two forms is API-mediated; this change
exposes the request-side controls that make it possible.

## What Changes

- Add two optional boolean request flags to `core.build_query_request` and to
  `QueryResource.query` / `AsyncQueryResource.query`: `compact_filters` and
  `normalized_filters` (named to match the VNDB API and the `Page` response
  fields). Each is included in the request body only when not `None`; setting it
  `True` makes the response populate the matching `Page` field.
- Widen the `filters` parameter type on `query()` (both clients) and on
  `filters.resolve_filters` from `Predicate | list[Any] | None` to
  `Predicate | list[Any] | str | None`, so a returned compact string (or a
  normalized list) can be fed straight back as `filters`. `resolve_filters`
  already passes non-`Predicate` values through unchanged — no logic change.
- Document the end-to-end round-trip (request the forms, reuse either as
  `filters` in a later query).

Out of scope: dedicated converter methods (`client.normalize_filters()` /
`compact_filters()`), `Page.refine()` helpers, and any client-side decoding of
the opaque compact string.

## Capabilities

### New Capabilities

<!-- None. This extends existing query behavior. -->

### Modified Capabilities

- `query-resource`: the "Generic query resource" requirement — `query()` gains
  the `compact_filters` and `normalized_filters` request flags and accepts a
  compact `str` as `filters`.

## Impact

- **Code:** `src/vndb_client/core.py` (`build_query_request`),
  `src/vndb_client/resource.py` (`QueryResource.query`, `AsyncQueryResource.query`),
  `src/vndb_client/filters/predicate.py` (`resolve_filters` signature).
- **Tests:** `tests/test_core.py`, `tests/test_resource.py`,
  `tests/test_filters_predicate.py`.
- **Docs:** the filtering guide gains a round-trip example.
- **Backward compatible:** all new params default to `None`; existing calls are
  unaffected.
