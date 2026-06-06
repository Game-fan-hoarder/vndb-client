## Context

The `QueryResource`/`AsyncQueryResource` (from VN) accept `filters` as a raw
nested list — VNDB's DSL: `[field, op, value]` predicates, `["and"|"or", …]`
compounds, operators `=`/`!=`/`>=`/`>`/`<=`/`<`, and nested relational filters
(a predicate value may be a sub-filter). This change adds a fluent builder that
produces that form. Full brainstorm: `docs/2026-06-06_query_builder_design.md`.
Per-entity filterable field sets come from the VNDB Kana API docs.

## Goals / Non-Goals

**Goals:**
- Ergonomic, discoverable, type-checked filter construction via operator overloading.
- Per-entity namespaces for all documented filterable fields + a generic escape hatch.
- Nested relational filters via recursive serialization.
- Graceful degradation: raw-list `filters` still work; builder output equals raw form.

**Non-Goals:**
- Per-field value type checking (values stay loosely typed; the API validates).
- A top-level NOT operator (VNDB has none; use `!=`).
- Changes to `core`/transport; auto-pagination; ulist.

## Decisions

**1. Operator overloading.** `Field` dunders return `Comparison`; `Predicate.__and__`/
`__or__` return `Compound`. *Alternative — explicit `.eq()/.gte()` + `and_()/or_()`:*
rejected as more verbose (operator style approved in brainstorm). `Field.__hash__`
is disabled because `__eq__` is overloaded.

**2. Recursive value serialization for nesting.** `Comparison.to_filter()` serializes a
`Predicate` value recursively; the builder does not hard-code which fields are
relational. *Alternative — typed relational fields:* rejected as over-engineering;
the API validates.

**3. Resolve at the resource boundary.** `query` calls `resolve_filters(filters)`;
`core` stays generic (no dependency on `filters`). The two resource classes share
the one helper.

**4. Explicit namespace classes** (class-attribute `Field`s) for mypy/IDE
discoverability, over dynamic `SimpleNamespace` generation.

**5. Loose value typing.** `Comparison` value is `Any` (scalar | list | `Predicate`).
Field-name discoverability is the win; value correctness is the API's job.

## Risks / Trade-offs

- **`__eq__` overload on `Field`** → fields are namespace attributes, never dict
  keys; `__hash__` disabled to avoid misuse. Standard query-builder pattern.
- **Operator precedence** (`&`/`|` bind looser than comparisons) → require
  parentheses around terms; documented with examples.
- **Namespace field-set drift vs API** → the generic `field()` escape hatch and
  raw-list passthrough cover undocumented/new filters.
- **Widening `query` filters type** → additive; raw lists and existing tests
  unaffected; covered by new + existing resource tests.

## Open Questions

- None. (Relational vs scalar field distinction is intentionally not encoded —
  recursive serialization handles both; the API validates.)
