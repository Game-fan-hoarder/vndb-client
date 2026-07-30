## Context

VN (archived `2026-06-06-vn-flagship-entity`) established the reusable
`QueryResource`/`AsyncQueryResource`, `field_spec` model→fields derivation, and
the `VndbModel` + nested-sub-model conventions. This change adds the 7 remaining
query entities on that foundation. Full brainstorm:
`design/2026-06-06_entity_coverage_design.md`. Field sets are taken from the VNDB
Kana API's documented selectable response fields per endpoint.

## Goals / Non-Goals

**Goals:**
- Typed models for release, producer, character, staff, tag, trait, quote.
- `client.<entity>.query(...) -> Page[<Model>]` (sync + async) for each.
- Shared image sub-models that keep every endpoint's `fields` request valid.

**Non-Goals:**
- Relational arrays (`character.vns`/`traits`, `release.vns`/`producers`/`images`, `*.extlinks`).
- Fluent query builder, auto-pagination, ulist.
- Any change to `QueryResource`, transport, or core.

## Decisions

**1. `ImageBase` vs `Image` split.** `/character` images lack `thumbnail`, while
`/vn` images have it. A single `Image` would make `field_spec(Character)` request
`image.thumbnail` and risk a 400. So `common.ImageBase` holds the shared fields
and `common.Image(ImageBase)` adds `thumbnail`/`thumbnail_dims`. `VN` uses
`Image`; `Character` uses `ImageBase`. `Image` moves from `vn.py` to `common.py`;
`vn.py` imports it; the public `vndb_client.Image` export is unchanged.

**2. Mirror VN scope.** Core scalars + key nested objects; defer relational arrays
and `extlinks`. Closed-set strings stay `str | None` with mirror constants
(`ProducerType`, `TagCategory`) for readability only.

**3. Reuse the generic resource.** Each entity is one `QueryResource(self,
"<endpoint>", Model)` instantiation; no new resource code. Endpoint names map 1:1
to attribute names.

**4. Quote minimal nested refs.** VNDB allows all VN/character fields under
`quote.vn`/`quote.character`; we model minimal `QuoteVN`(id,title) /
`QuoteCharacter`(id,name) — quote's essential payload — to keep the derived
`fields` bounded. *Alternative — reuse full `VN`/`Character`:* rejected (would
request the entire VN/character field set nested under every quote).

**5. Polymorphic `resolution`.** `release.resolution` is `null | "non-standard" |
[w,h]`, typed `list[int] | str | None`; `field_spec` emits the bare key (not a
`VndbModel`), which is correct.

## Risks / Trade-offs

- **Requesting an unsupported nested field → 400** → mitigated by the
  `ImageBase`/`Image` split; per-entity model fields taken from the documented
  selectable fields; resource tests assert the derived `fields` per entity.
- **Field-set drift vs the live API** → `VndbModel`'s `extra="ignore"` tolerates
  new server fields; missing fields parse as `None`. Models can be extended later.
- **`vn.py` Image move** → keep a stable public `Image` export and unchanged VN
  behavior; covered by the existing VN + public-API tests.

## Open Questions

- None outstanding. (Per-entity field choices follow the documented API; ordering
  within `field_spec` is not API-significant.)
