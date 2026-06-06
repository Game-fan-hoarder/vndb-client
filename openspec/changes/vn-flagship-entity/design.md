## Context

The Foundation (archived `2026-06-05-foundation-transport-core`) gives us
`Client`/`AsyncClient` with an internal generic `_query(endpoint, model,
**params) -> Page[T]`, the `VndbModel` base, `Page[T]`, and the exception
hierarchy. This change adds the first public, typed entity surface on top of
that primitive. The full brainstorm is in `docs/2026-06-06_vn_flagship_design.md`.

VNDB `/vn` constraints that shape the design: an explicit `fields` parameter is
required (unrequested fields are omitted from the response); nested fields use
dotted paths (`image.url`); `released` is a partial-date string with sentinels
(`"TBA"`, `"today"`); `devstatus` (0/1/2) and `length` (1–5) are closed-set ints
that VNDB may extend.

## Goals / Non-Goals

**Goals:**
- A generic, typed query resource reused by every future entity.
- A model→fields derivation so callers get fully-populated entities by default.
- A faithful VN model (core scalars + `image` + `titles[]`/`aliases[]`).
- `Client().vn.query(...)` / `await AsyncClient().vn.query(...)` → `Page[VN]`.

**Non-Goals:**
- Relational VN fields (tags/relations/developers/editions/staff/va/screenshots/extlinks).
- The fluent query builder (filters stay raw lists, per Foundation).
- Auto-pagination iterator.
- The other 7 query entities (they instantiate the same resource later).

## Decisions

**1. Generic resource base, VN instantiates it.**
`QueryResource(Generic[ModelT])` / `AsyncQueryResource(Generic[ModelT])` take
`(client, endpoint, model)` and expose `query(...) -> Page[ModelT]`. Wired as
`self.vn = QueryResource(self, "vn", VN)`. *Alternative — VN-specific resource,
generalize later:* rejected because all 8 VNDB query endpoints share one shape
and 7 more entities are imminent, so the abstraction is well-informed, not
speculative.

**2. Default `fields` to the model's full set, overridable.**
`field_spec(model)` reflects over `model_fields`, emits each field's alias-or-name,
and recurses into nested `VndbModel` sub-models with dotted paths. `query()`
uses it when `fields` is omitted. *Alternatives — require explicit fields / small
default set:* rejected for poor DX and sparse/arbitrary results.

**3. Closed-set ints stay `int | None` with IntEnum mirror constants.**
`DevStatus`/`VNLength` are provided for readable comparison but are NOT field
types. *Alternative — strict IntEnum fields:* rejected because a new VNDB value
would fail validation on otherwise-valid responses.

**4. `released` stays `str`; `description` kept raw.** VNDB partial dates /
sentinels and VNDB markup are not parsed (YAGNI).

**5. Avoid circular import.** `resource.py` imports `Client`/`AsyncClient` only
under `TYPE_CHECKING` (it calls `client._query`); `client.py` imports the
resources at runtime to instantiate them.

## Risks / Trade-offs

- **`field_spec` reflection across Pydantic v2 + Python 3.10–3.14** → unwrap
  `Optional`/`list` and detect `VndbModel` subclasses via `model_fields`
  annotations; covered by unit tests and the tox matrix.
- **Default fields request the full set (larger payloads)** → acceptable for an
  MVP; callers can pass `fields=` to narrow. Documented.
- **Mirror constants can drift from VNDB** → low risk (stable sets); they are
  comparison helpers only, so drift never breaks parsing.
- **`_query` is underscore-internal but called by the resource** → same package,
  intended; keeps the public surface the typed `.vn.query`.

## Open Questions

- None outstanding. (`field_spec` field ordering is not significant to the API;
  tests assert set membership / dotted-path correctness, not order.)
