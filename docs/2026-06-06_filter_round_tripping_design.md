# Compact↔normalized filter round-tripping (l33) — Design

**Status:** Approved 2026-06-06
**Beads task:** `vndb-client-l33` (post-V1 stretch, deferred from epic 6lp)

## Goal

Let users obtain the compact and normalized filter forms VNDB echoes back, and
feed either form straight into a later query — enabling the round-trip without
any local decoding (the compact form is an opaque, server-encoded string).

## Background

- `Page` already parses `compact_filters: str | None` and
  `normalized_filters: list | None` from responses.
- `core.build_query_request` and `QueryResource.query` / `AsyncQueryResource.query`
  do NOT currently support the request-side flags that ask the API to echo those
  forms.
- The compact form cannot be decoded client-side; converting between compact and
  normalized is API-mediated (submit one form with the opposite flag set, read
  the echoed field).

## Scope decision (from brainstorm)

Minimal: request flags + type-widening + docs. No dedicated converter methods
(`client.normalize_filters()` / `compact_filters()`) and no `Page.refine()`
helper — those larger options are deferred.

## Components

### 1. Request flags — `core.build_query_request` + `query()`

Add two optional boolean request flags, named to match the VNDB API and the
existing `Page` response fields:

- `compact_filters: bool | None = None`
- `normalized_filters: bool | None = None`

`build_query_request` includes each in the request body only when not `None`
(the same omit-when-`None` pattern as the other params). `QueryResource.query`
and `AsyncQueryResource.query` gain the two params and forward them. Setting
`normalized_filters=True` makes the response populate `Page.normalized_filters`;
`compact_filters=True` populates `Page.compact_filters`.

Docstrings must make clear that on `query()` these are *request* booleans
(distinct from the same-named `Page` response fields).

### 2. Accept a compact string as `filters`

Widen the `filters` parameter type from `Predicate | list[Any] | None` to
`Predicate | list[Any] | str | None` on `query()` (both clients) and on
`resolve_filters`. `resolve_filters` already passes non-`Predicate` values
through unchanged, so a compact `str` (or a normalized `list`) flows into the
request body as-is — no logic change, only the type widening so it is a
supported, type-checked input. This is the "feed them back" half of the
round-trip.

### 3. Round-trip, end to end

```python
# Ask the API to echo both forms
page = client.vn.query(
    filters=(vn_filters.rating >= 80),
    compact_filters=True,
    normalized_filters=True,
)
page.compact_filters     # -> opaque str
page.normalized_filters  # -> explicit nested list

# Reuse either form directly in a later query (round-trip; API-mediated)
later = client.vn.query(filters=page.compact_filters, results=25)
```

## Testing

- `core.build_query_request`: each flag is included in the body only when set;
  absent when `None`.
- `resolve_filters`: a `str` passes through unchanged (alongside the existing
  list / `Predicate` / `None` cases).
- `query()` (sync + async): a compact-string `filters` value and the two flags
  reach the request spec body (using the existing fake-transport / spec-capture
  test pattern).

## Out of scope

- `client.normalize_filters()` / `client.compact_filters()` converter methods and
  `Page.refine()` helpers (larger deferred options).
- Any client-side decoding of the compact string (impossible — it is opaque).

## Spec placement

This extends existing query behavior rather than adding a capability. The delta
will MODIFY the `query-resource` capability (the `query()` signature: two new
request flags and the widened `filters` type). Exact placement confirmed at
`/opsx:propose`.

## Notes / risk

- The flag names intentionally collide with the `Page` response field names —
  deliberate (same VNDB concept on request and response) and discoverable;
  docstrings disambiguate request vs response usage.
