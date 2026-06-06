## Why

The VN flagship proved the typed-entity pipeline and established the generic
`QueryResource` + `field_spec` conventions. The VNDB API exposes 7 more query
entities with the identical request/response shape. Implementing them completes
read coverage of the database query endpoints and is now cheap — models + wiring
on top of the existing resource.

## What Changes

- Add typed models for the 7 remaining query entities, each inheriting
  `VndbModel`, scoped like VN (core scalars + key nested objects; relational
  arrays deferred):
  - `Release` (+ `ReleaseLang`, `ReleaseMedia`)
  - `Producer` (+ `ProducerType` mirror)
  - `Character` (image typed `ImageBase`)
  - `Staff` (+ `StaffAlias`)
  - `Tag` (+ `TagCategory` mirror)
  - `Trait`
  - `Quote` (+ minimal `QuoteVN`, `QuoteCharacter` refs)
- Add `entities/common.py` with `ImageBase` (shared image fields) and
  `Image(ImageBase)` (adds `thumbnail`/`thumbnail_dims`); move `Image` out of
  `entities/vn.py` to `common` (VN imports it from there). The split keeps
  `/character` (no thumbnail) and `/vn` (thumbnail) requesting only valid fields.
- Wire `client.release`, `client.producer`, `client.character`, `client.staff`,
  `client.tag`, `client.trait`, `client.quote` on both `Client` and `AsyncClient`
  as instances of the existing generic resource — no resource/transport/core
  changes.
- Export the new models and `ImageBase` from the package root; keep `Image`
  export stable.
- Add docs API reference blocks for the new entity modules and `common`.

## Capabilities

### New Capabilities

- `entity-coverage`: Typed models + `client.<entity>` query surfaces for release,
  producer, character, staff, tag, trait, and quote, plus the shared
  `ImageBase`/`Image` sub-models.

### Modified Capabilities

<!-- None at the requirement level. `query-resource`, `response-envelope`,
`http-transport`, `request-retry`, `error-handling`, and `vn-entity` are reused
unchanged. (vn.py's internal `Image` import source moves to `common`, but the
`vn-entity` requirements and the public `Image` export are unchanged.) -->

## Impact

- **New modules:** `entities/common.py`, `entities/release.py`,
  `entities/producer.py`, `entities/character.py`, `entities/staff.py`,
  `entities/tag.py`, `entities/trait.py`, `entities/quote.py`.
- **Edited:** `entities/vn.py` (import `Image` from `common`), `entities/__init__.py`,
  `client.py` (wire 7 attributes), `__init__.py` (exports), `docs/modules.md`.
- **No new runtime dependencies; no breaking changes** (purely additive; `Image`
  export and `vndb_client.VN` behavior unchanged).
- **Out of scope** (later epics): relational arrays, fluent query builder,
  auto-pagination, ulist.
