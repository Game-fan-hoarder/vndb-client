# vndb-client — Feature Map

**Date:** 2026-06-05
**Scope:** Full VNDB Kana HTTP API client
**Status:** Feature map (Workflow 1)
**Companion:** `2026-06-05_full_api_client.md` (vision)

Feature areas are grouped into three milestones: **MVP**, **Beta**, **V1**.

## MVP — prove the full pipeline end-to-end on one flagship entity

- `transport` (sync + async): auth header, request execution, status→exception mapping
- exception hierarchy
- `core`: request serialization + response parsing
- `Page[T]` response envelope
- **VN entity**: Pydantic model + `vn` query resource (flagship — exercises every layer)
- field selection + filters accepted as raw lists (typed builder comes later)
- manual pagination (`page` / `results` + `more` flag)
- test harness (mocked httpx transport) + docs scaffolding

**Outcome:** `Client().vn.query(...)` and the async equivalent return typed VNs.
The end-to-end architecture is validated.

## Beta — full read coverage + ergonomics

- remaining query entities: release, producer, character, staff, tag, trait, quote
  (models + resources, same pattern as VN)
- fluent **query builder / filter DSL**: typed predicates, `and`/`or`, nested
  relational filters, per-entity field enums
- simple GET endpoints: `/stats`, `/user`, `/authinfo`, `/schema`, `/ulist_labels`
- **ulist read** (`POST /ulist`) + `UlistEntry` model
- auto-pagination iterator (sync generator / async generator)
- rate-limit-aware retry/backoff

## V1 — writes, polish, release-ready

- authenticated writes: `PATCH`/`DELETE /ulist/<id>`, `PATCH`/`DELETE /rlist/<id>`,
  with `listwrite` scope handling
- complete docs (mkdocs API pages + usage guides + examples), 90%+ coverage
- **Optional / stretch:**
  - schema-driven codegen helper (borrowing Approach C) to keep models in sync with `/schema`
  - compact ↔ normalized filter round-tripping
  - response caching

## Dependency map

```
transport + exceptions  ──┐ (foundation; everything depends on this)
core (sans-I/O)         ──┤
models: Page[T] + VN    ──┴──►  VN resource (MVP) ──► proves pipeline
                                      │
        ┌─────────────────────────────┴──────────────┐
        ▼ (Beta, parallelizable once VN sets pattern) ▼
  other entity models/resources        query builder + field enums
  simple GET endpoints (independent)    ulist read
                                      │
                                      ▼ (V1)
                              ulist/rlist writes ──► docs/polish/release
```

**Key ordering constraints:**

1. Foundation (`transport`, `core`, exceptions) before anything.
2. VN entity (MVP) proves the pipeline; other entities follow the same pattern.
3. Entity fan-out + query builder (Beta) are mostly parallelizable once VN
   establishes the pattern.
4. ulist **read** (Beta) before ulist **write** (V1).
5. Simple GET endpoints have no dependencies beyond `transport` — slot in anytime.

## Proposed Beads epics (Workflow 1, step 4)

One epic per milestone / feature area:

- **Epic: Foundation** — transport (sync+async), core sans-I/O, exceptions, `Page[T]`
- **Epic: VN flagship (MVP)** — VN model + query resource + manual pagination + test harness
- **Epic: Entity coverage (Beta)** — release, producer, character, staff, tag, trait, quote
- **Epic: Query builder (Beta)** — fluent filter DSL + per-entity field enums
- **Epic: Simple endpoints (Beta)** — /stats, /user, /authinfo, /schema, /ulist_labels
- **Epic: User lists (Beta→V1)** — ulist read (Beta), then ulist/rlist writes (V1)
- **Epic: Release & docs (V1)** — full docs, coverage, examples, PyPI release; optional codegen/caching
