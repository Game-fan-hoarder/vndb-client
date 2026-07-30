# Entity Coverage — Design

**Date:** 2026-06-06
**Epic:** `vndb-client-m9k` — Entity coverage (Beta): release, producer, character, staff, tag, trait, quote
**Milestone:** Beta
**Workflow:** 2 (Feature Implementation), step 1 — brainstorm/design
**Next step:** `/opsx:propose` (delta spec) — NOT writing-plans
**Builds on:** VN flagship (`design/2026-06-06_vn_flagship_design.md`) — generic
`QueryResource`/`AsyncQueryResource`, `field_spec`, `VndbModel`, `Page[T]`, and
the `Image` sub-model.

## Purpose

Add the 7 remaining VNDB query entities as typed models + `client.<entity>`
surfaces, reusing the generic resource VN established. No resource/transport/core
changes — this epic is models + wiring + exports. Outcome: `client.release`,
`client.producer`, `client.character`, `client.staff`, `client.tag`,
`client.trait`, `client.quote` each expose `.query(...) -> Page[<Model>]`
(sync and async).

## Decisions

| Decision | Choice |
|----------|--------|
| Field scope per entity | Mirror VN: core scalars + key nested objects; **defer** cross-entity relational arrays and `extlinks`. |
| Shared sub-models | Hoist to `entities/common.py`. Split `ImageBase` (shared) vs `Image(ImageBase)` (+`thumbnail`/`thumbnail_dims`) so `/character` (no thumbnail) and `/vn` (thumbnail) both request only valid fields. |
| Resource | Reuse existing generic `QueryResource`/`AsyncQueryResource` unchanged; one instantiation per entity. |
| Closed-set strings | Fields stay `str | None`; provide mirror constants (`ProducerType`, `TagCategory`) for readability only (VN `DevStatus` precedent). |
| Dates / partial values | `released` and similar stay `str`. `resolution` typed `list[int] \| str \| None` (polymorphic; `field_spec` emits the bare key). |
| Quote nested refs | Model minimal `QuoteVN`(id,title) / `QuoteCharacter`(id,name) — quote's essential payload — rather than the full selectable VN/character objects (keeps derived `fields` bounded). |

## Module layout (`src/vndb_client/entities/`)

| Module | Contents |
|--------|----------|
| `common.py` (new) | `ImageBase` (`id`,`url`,`dims`,`sexual`,`violence`,`votecount`); `Image(ImageBase)` (+`thumbnail`,`thumbnail_dims`). |
| `vn.py` (edit) | Drop local `Image`; import it from `common`. `VN`/`Title` unchanged. |
| `release.py` (new) | `Release` + `ReleaseLang`, `ReleaseMedia`. |
| `producer.py` (new) | `Producer` (+ `ProducerType` mirror). |
| `character.py` (new) | `Character` (image typed `ImageBase`). |
| `staff.py` (new) | `Staff` + `StaffAlias`. |
| `tag.py` (new) | `Tag` (+ `TagCategory` mirror). |
| `trait.py` (new) | `Trait`. |
| `quote.py` (new) | `Quote` + `QuoteVN`, `QuoteCharacter`. |
| `entities/__init__.py` (edit) | Re-export all entity + shared symbols. |

Wiring: `Client.__init__`/`AsyncClient.__init__` add `self.release` … `self.quote`,
each `= QueryResource(self, "<endpoint>", Model)` (async variant for `AsyncClient`).
Endpoints map 1:1 to attribute names (`release`,`producer`,`character`,`staff`,
`tag`,`trait`,`quote`). `__init__.py` exports the new models + `ImageBase`;
`Image` export stays stable (sourced from `common`).

## Models

All inherit `VndbModel` (absent → `None`); `id: str` required on every model.

**common.py**
- `ImageBase`: `id:str`, `url:str|None`, `dims:list[int]|None`, `sexual:float|None`, `violence:float|None`, `votecount:int|None`
- `Image(ImageBase)`: +`thumbnail:str|None`, `thumbnail_dims:list[int]|None`

**Release** (defer `vns`,`producers`,`images`)
- scalars: `id`, `title:str|None`, `alttitle:str|None`, `released:str|None`, `platforms:list[str]|None`, `minage:int|None`, `patch:bool|None`, `freeware:bool|None`, `uncensored:bool|None`, `official:bool|None`, `has_ero:bool|None`, `resolution:list[int]|str|None`, `engine:str|None`, `voiced:int|None`, `notes:str|None`, `gtin:str|None`, `catalog:str|None`
- `languages:list[ReleaseLang]|None` → `ReleaseLang{lang:str, title:str|None, latin:str|None, mtl:bool|None, main:bool|None}`
- `media:list[ReleaseMedia]|None` → `ReleaseMedia{medium:str|None, qty:int|None}`

**Producer** (defer `extlinks`)
- `id`, `name:str|None`, `original:str|None`, `aliases:list[str]|None`, `lang:str|None`, `type:str|None` (`ProducerType`: `co`/`in`/`ng`), `description:str|None`

**Character** (defer `vns`,`traits`)
- `id`, `name:str|None`, `original:str|None`, `aliases:list[str]|None`, `description:str|None`, `blood_type:str|None`, `height:int|None`, `weight:int|None`, `bust:int|None`, `waist:int|None`, `hips:int|None`, `cup:str|None`, `age:int|None`, `birthday:list[int]|None`, `sex:list[str|None]|None`, `gender:list[str|None]|None`, `image:ImageBase|None`

**Staff** (defer `extlinks`)
- `id`, `aid:int|None`, `ismain:bool|None`, `name:str|None`, `original:str|None`, `lang:str|None`, `gender:str|None`, `description:str|None`
- `aliases:list[StaffAlias]|None` → `StaffAlias{aid:int|None, name:str|None, latin:str|None, ismain:bool|None}`

**Tag**
- `id`, `name:str|None`, `aliases:list[str]|None`, `description:str|None`, `category:str|None` (`TagCategory`: `cont`/`ero`/`tech`), `searchable:bool|None`, `applicable:bool|None`, `vn_count:int|None`

**Trait**
- `id`, `name:str|None`, `aliases:list[str]|None`, `description:str|None`, `searchable:bool|None`, `applicable:bool|None`, `sexual:bool|None`, `group_id:str|None`, `group_name:str|None`, `char_count:int|None`

**Quote**
- `id`, `quote:str|None`, `score:int|None`
- `vn:QuoteVN|None` → `QuoteVN{id:str, title:str|None}`
- `character:QuoteCharacter|None` → `QuoteCharacter{id:str, name:str|None}`

## Data flow

Unchanged from VN: `client.<entity>.query(...)` → `field_spec(<Model>)` default →
`_query("<endpoint>", <Model>, ...)` → `Page[<Model>]`. Sync and async via the
existing two resource classes.

## Testing (mocked httpx, VN pattern)

- `tests/test_common.py` — `ImageBase` parses a character-style image; `Image`
  parses a VN-style image with `thumbnail`; `field_spec(Character)` excludes
  `image.thumbnail` while `field_spec(VN)` includes it.
- `tests/test_entities_<name>.py` per entity — parse a realistic payload: scalars
  populated; sub-models are the right types (`release.languages[0]` →
  `ReleaseLang`, `character.image` → `ImageBase`, `staff.aliases[0]` →
  `StaffAlias`, `quote.vn` → `QuoteVN`); absent field → `None`; mirror-constant
  comparison works.
- `tests/test_resource.py` (extend) — for each entity: `Client().<attr>` is a
  `QueryResource`, `AsyncClient().<attr>` is an `AsyncQueryResource`; a
  representative `.query()` against a mock returns `Page[<Model>]`; the derived
  `fields` contains expected dotted nesting (`quote.vn.title`,
  `release.languages.lang`) and excludes deferred relational fields.
- `tests/test_public_api.py` (extend) — new models + `ImageBase` exported and in
  `__all__`.

## Docs

- Add `::: vndb_client.entities.<name>` and `::: vndb_client.entities.common`
  blocks to `docs/modules.md`; verify `mkdocs build --strict`.

## Out of scope (later epics)

- Relational arrays (`character.vns`/`traits`, `release.vns`/`producers`/`images`,
  `*.extlinks`).
- Fluent query builder / filter DSL (filters stay raw lists).
- Auto-pagination iterator; ulist read/write.
