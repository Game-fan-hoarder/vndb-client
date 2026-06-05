# vndb-client — Product Vision

**Date:** 2026-06-05
**Scope:** Full VNDB Kana HTTP API client (Python library)
**Status:** Vision (Workflow 1)

## Vision

`vndb-client` is a faithful, fully-typed Python client for the **entire VNDB Kana
HTTP API**. It offers both **synchronous and asynchronous** clients over a shared
core, **rich Pydantic v2 models** for every entity, and a **fluent, type-checked
query builder** for VNDB's filter DSL.

**Definition of done:** every documented endpoint is reachable through an
idiomatic, well-documented, well-tested API, published to PyPI with generated
MkDocs documentation.

## Locked-in decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API target | VNDB Kana HTTP API (`https://api.vndb.org/kana`) | Project is "Http based"; Kana is the current API. |
| Coverage | Full API surface (query + simple GETs + auth + list writes) | General-purpose library others can depend on. |
| Concurrency | Both sync **and** async | Hardest to retrofit; maximally general-purpose. |
| Abstraction | Rich typed models + fluent query builder | Best DX; aligns with strict typing + full coverage. |
| Stack | `httpx` + Pydantic v2 | httpx gives sync+async from one API; Pydantic v2 gives validation, JSON parsing, camelCase→snake aliasing, editor DX. |
| Architecture | Sans-I/O core + two thin clients (Approach A) | Pure, testable core; idiomatic, debuggable sync/async wrappers; no logic duplication. |

## Architecture

Single package `vndb_client`, layered:

- **`transport`** — owns the httpx client lifecycle, base URL, `Authorization: Token`
  injection, and request execution. Two implementations (sync `httpx.Client` /
  async `httpx.AsyncClient`) behind one shared protocol. Maps HTTP status codes to
  exceptions and handles rate-limit/429 backoff respecting VNDB's limits.
- **`core` (sans-I/O)** — pure functions: serialize a query (filters/fields/sort/
  paging) into a request body, and parse a raw JSON response into typed models. No
  network, no async — fully unit-testable in isolation. The heart of Approach A.
- **`models`** — Pydantic v2 models per entity (VN, Release, Producer, Character,
  Staff, Tag, Trait, Quote, plus UlistEntry, User, Stats, AuthInfo, Schema) and a
  generic response envelope `Page[T]` (`results`, `more`, `count`). camelCase→snake
  aliasing handled here.
- **`filters`** — the fluent query builder: typed predicates (`=`, `!=`, `>=`, `>`,
  `<=`, `<`), `and`/`or` composition, nested relational filters, and per-entity
  field enums. Degrades gracefully to raw list/dict filters for power users.
- **`resources`** — per-entity query methods + simple GET endpoints (`/stats`,
  `/user`, `/authinfo`, `/schema`, `/ulist_labels`) + ulist read and the
  authenticated ulist/rlist writes.
- **`client`** — `Client` (sync) and `AsyncClient` (async), each exposing the
  resources; the only public entry points most users touch.
- **Cross-cutting** — an exception hierarchy (auth, rate-limit, bad-request,
  server) and a pagination helper that auto-iterates pages as a (sync/async)
  generator.

## API surface reference (VNDB Kana)

- **Auth:** `Authorization: Token <token>` header. Permission scopes: `listread`,
  `listwrite`.
- **Rate limits:** 200 requests / 5 minutes; max 1s execution time per minute;
  3s request timeout.
- **Simple GET endpoints:** `/schema`, `/stats`, `/user`, `/authinfo`,
  `/ulist_labels`.
- **POST query endpoints (shared request/response shape):** `/vn`, `/release`,
  `/producer`, `/character`, `/staff`, `/tag`, `/trait`, `/quote`.
  - Request body: `filters`, `fields`, `sort`, `reverse`, `results` (≤100),
    `page` (≥1), `user`, `count`, `compact_filters`, `normalized_filters`.
  - Response envelope: `results`, `more`, `count`, `compact_filters`,
    `normalized_filters`.
- **Filter DSL:** predicate `["field", "op", value]`; compound
  `["and"|"or", pred, ...]`; operators `=`, `!=`, `>=`, `>`, `<=`, `<`; nested
  relational filters (e.g. `release`, `character`, `staff`); max 1000 predicates.
- **List write endpoints:** `PATCH`/`DELETE /ulist/<id>`, `PATCH`/`DELETE
  /rlist/<id>` (require `listwrite`).

## Non-goals (this product)

- The legacy TCP/SSL query API (superseded by Kana).
- A CLI or GUI — this is a library; downstream apps build those.

## Related documents

- Feature map & milestones: `2026-06-05_full_api_client_feature_map.md`
