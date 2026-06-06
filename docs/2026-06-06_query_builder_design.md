# Query Builder / Filter DSL — Design

**Date:** 2026-06-06
**Epic:** `vndb-client-642` — Query builder / filter DSL (Beta)
**Milestone:** Beta
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans
**Builds on:** VN flagship + Entity coverage — `QueryResource`/`AsyncQueryResource`
already accept `filters` (raw list); the entities expose the queryable endpoints.

## Purpose

Add a fluent, discoverable, type-checked builder for VNDB's filter DSL that
produces the raw nested-list form the API expects, with per-entity field
namespaces, and-or composition, nested relational filters, and graceful
degradation to raw lists.

## Decisions

| Decision | Choice |
|----------|--------|
| API style | Operator overloading: comparisons via `==`/`!=`/`>=`/`>`/`<=`/`<`, composition via `&`/`|`. Most ergonomic (SQLAlchemy/Django-Q style). |
| Field coverage | Per-entity namespaces covering **all documented filterable fields** for the 8 entities, PLUS a generic `field(name)` escape hatch and continued raw-list support. |
| Negation | None — VNDB's DSL has no top-level NOT; negate via `!=`. |
| Nested relational filters | A comparison's value may itself be a `Predicate`, serialized recursively. The builder does not hard-code which fields are relational. |
| Value typing | Loose (scalars/lists/`Predicate`). The builder gives field-name discoverability + ergonomics; the API validates values. Per-field value typing is out of scope. |
| Query integration | `query(filters=...)` accepts `Predicate | list | None`; the resource resolves a `Predicate` to its list form before forwarding. `core` stays generic. |

## Module layout

New package `src/vndb_client/filters/`:

| Module | Responsibility |
|--------|----------------|
| `predicate.py` | `Field`, `Predicate` (base), `Comparison`, `Compound`, and `resolve_filters`. |
| `namespaces.py` | The 8 per-entity namespace objects + the generic `field(name)` factory. |
| `__init__.py` | Exports: the 8 namespaces, `field`, `Predicate`. |

### Core types (`predicate.py`)

- **`Field`** — wraps an API filter name. Operator dunders return a `Comparison`:
  `__eq__`→`"="`, `__ne__`→`"!="`, `__ge__`→`">="`, `__gt__`→`">"`,
  `__le__`→`"<="`, `__lt__`→`"<"`. `__hash__ = None` (disabled — `__eq__` is
  overloaded; fields are namespace attributes, not dict keys).
- **`Predicate`** (base) — `to_filter() -> list[Any]`; `__and__`/`__or__` →
  `Compound`.
- **`Comparison(Predicate)`** — `(name, op, value)`; `to_filter()` →
  `[name, op, _serialize(value)]` where `_serialize` recurses if `value` is a
  `Predicate` (nested relational filters) and passes scalars/lists through.
- **`Compound(Predicate)`** — `kind` (`"and"`/`"or"`) + children;
  `to_filter()` → `["and"|"or", *[c.to_filter() for c in children]]`. `&`/`|`
  flatten same-kind chains (`a & b & c` → one `["and", a, b, c]`).
- **`resolve_filters(filters)`** — `filters.to_filter()` if a `Predicate`,
  else the value unchanged (raw list or `None`).

## Per-entity namespaces (`namespaces.py`)

Explicit classes (class-attribute `Field`s) so attributes are mypy-visible and
IDE-discoverable. Documented filterable fields per entity:

- `vn_filters`: id, search, lang, olang, platform, length, released, rating,
  votecount, has_description, has_anime, has_screenshot, has_review, devstatus,
  tag, dtag, anime_id, label, release, character, staff, developer
- `release_filters`: id, search, lang, platform, released, resolution,
  resolution_aspect, minage, medium, voiced, engine, rtype, extlink, drm, patch,
  freeware, uncensored, official, has_ero, vn, producer
- `producer_filters`: id, search, lang, type, extlink
- `character_filters`: id, search, role, blood_type, sex, sex_spoil, gender,
  gender_spoil, height, weight, bust, waist, hips, cup, age, trait, dtrait,
  birthday, seiyuu, vn
- `staff_filters`: id, aid, search, lang, gender, role, extlink, ismain
- `tag_filters`: id, search, category
- `trait_filters`: id, search
- `quote_filters`: id, vn, character, random

**Generic escape hatch:** `field(name) -> Field` for any filter name not in a
namespace; raw-list `filters=[...]` also still works.

## Usage

```python
from vndb_client.filters import vn_filters as F, character_filters as C, field

# scalar predicates + composition
q = (F.rating >= 80) & (F.lang == "en") & (F.olang == "ja")
client.vn.query(filters=q, fields="id,title,rating")
# → ["and", ["rating",">=",80], ["lang","=","en"], ["olang","=","ja"]]

# or / nested relational
q2 = (F.platform == "win") | (F.platform == "lin")
q3 = F.character == ((C.role == "main") & (C.trait == "i123"))
# → ["character","=",["and",["role","=","main"],["trait","=","i123"]]]

# escape hatch + raw still work
field("some_new_filter") >= 5
client.vn.query(filters=["search", "=", "ever17"])
```

## Query integration

`QueryResource.query` / `AsyncQueryResource.query` widen `filters` to
`Predicate | list | None` and call `resolve_filters(filters)` before forwarding
to `_query`. `core.build_query_request` is unchanged (still receives a list).
The two resource classes share the resolution via the `resolve_filters` helper.

## Testing (pure; mocked transport for resource)

- `tests/test_filters_predicate.py` — all 6 operators → correct
  `[name, op, value]`; `&`/`|` build and flatten `and`/`or`; recursive
  serialization of a `Predicate` value (nested + nested-compound); scalars/lists
  pass through; `Field.__hash__` disabled.
- `tests/test_filters_namespaces.py` — each of the 8 namespaces exposes its
  documented fields as `Field`s (spot-check names); `field("x")` works.
- `tests/test_resource.py` (extend) — `client.vn.query(filters=<Predicate>)`
  sends the serialized nested list in the request body; raw-list filters
  forwarded unchanged; async equivalent.
- `tests/test_public_api.py` (extend) — `vndb_client.filters` exports the 8
  namespaces, `field`, and `Predicate`.

## Docs

- Add a filter-DSL usage snippet + `::: vndb_client.filters` reference to
  `docs/modules.md`; verify `mkdocs build --strict`.

## Out of scope (later epics)

- Auto-pagination iterator; ulist read/write.
- Per-field value type checking (values stay loosely typed).
- A top-level NOT operator (no API support).
