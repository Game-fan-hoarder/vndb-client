## Context

VNDB's `/query` echoes filters back as `compact_filters` (opaque server-encoded
string) and `normalized_filters` (explicit nested list) when the request asks.
`Page` parses both, but `query()`/`build_query_request` lack the request flags
and `filters` is not typed to accept a compact string. The full approved design
is at `docs/2026-06-06_filter_round_tripping_design.md`; this records decisions.

## Goals / Non-Goals

**Goals:**

- Enable requesting the echoed filter forms (`compact_filters`,
  `normalized_filters` flags) through `query()`.
- Accept a returned compact `str` (or normalized `list`) as `filters` so it can
  be fed back into a later query.

**Non-Goals:**

- Dedicated converter methods or `Page.refine()` helpers (deferred larger scope).
- Client-side decoding of the opaque compact string (impossible).
- New runtime behavior beyond passing the flags through and widening a type.

## Decisions

- **Reuse the VNDB API names for the flags.** `compact_filters` /
  `normalized_filters` match the API request fields and the `Page` response
  fields. Same concept on both sides; docstrings disambiguate request booleans
  from response data. Alternative names (`want_compact`) were rejected as less
  discoverable.
- **Omit-when-`None`, like the other params.** `build_query_request` only adds a
  flag to the body when not `None`, so existing calls are byte-identical and
  backward compatible.
- **Widen the type, don't branch.** `resolve_filters` already passes
  non-`Predicate` values through, so accepting a compact `str` is purely a type
  widening (`Predicate | list[Any] | str | None`) — no runtime change, just a
  type-checked, documented input.
- **Modify `query-resource`, don't add a capability.** This is an extension of
  the existing `query()` contract, not a new behavior area.

## Risks / Trade-offs

- **Flag/field name collision** → mitigated by clear docstrings (request boolean
  vs response value).
- **Compact string is opaque** → we never parse it; we only carry it through.
  Documented so users don't expect local conversion.
- **Spec already omits `user` from the listed params** (added in the user-lists
  cycle without a spec update) → when writing the MODIFIED requirement, include
  the currently-implemented param set so the spec re-converges with reality.
