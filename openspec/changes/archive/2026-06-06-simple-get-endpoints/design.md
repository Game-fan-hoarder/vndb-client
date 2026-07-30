## Context

The Foundation transport (`transport.send(RequestSpec)`) already supports GET via
`RequestSpec.method`/`params`, with retry, error mapping, and the
`Authorization: Token` header applied. The clients only expose POST query
resources so far. This change adds the 5 simple GET endpoints as direct client
methods with typed models. Full brainstorm + verified field shapes:
`design/2026-06-06_simple_get_endpoints_design.md`.

## Goals / Non-Goals

**Goals:**
- Typed access to `/stats`, `/authinfo`, `/user`, `/ulist_labels`; raw access to `/schema`.
- A small reusable GET helper on the clients.

**Non-Goals:**
- ulist read/write (`04j` epic); auto-pagination; modeling `/schema`.
- Any change to `core` or transport.

## Decisions

**1. Direct client methods.** `stats`/`authinfo`/`get_user`/`ulist_labels`/`schema`
are one-shot GETs, so plain (async) methods fit better than a query-resource
namespace. *Alternative — a `client.meta.*` namespace:* rejected as heavier for
non-query calls.

**2. `_get` helper at the client layer.** Builds a GET `RequestSpec`, filters out
`None` params, calls `transport.send`, returns `response.json()` (decode failure
→ `VndbParseError`). `core.build_query_request` (POST-only) is untouched; `core`
stays generic.

**3. Typed models for the 4 structured endpoints; raw `/schema`.** `Stats`,
`AuthInfo`, `User`, `UlistLabel` are `VndbModel`s. `/schema` is huge, deeply
nested, and evolves with the API — returned as `dict[str, Any]`.

**4. Endpoint-specific return shapes.** `get_user` → `dict[str, User | None]`
(VNDB returns a map keyed by each `q`, `null` for unknown); `ulist_labels` →
`list[UlistLabel]` (unwrapped from `{"labels": [...]}`).

**5. `UlistLabel.id` is an `int`** (the ulist_labels API uses integer label ids,
not vndbid strings) — unlike every entity `id`.

## Risks / Trade-offs

- **`None` params leaking into the query string** → `_get` filters `None` values
  so optional params are omitted; covered by a test.
- **`Stats` required ints vs evolving API** → `/stats` always returns the full
  aggregate (no field selection); `extra="ignore"` tolerates added fields.
  Acceptable; revisit only if VNDB removes a count.
- **`get_user` map values can be `null`** → modeled as `User | None` and tested.
- **`authinfo` without a token** → returns the API's 401, surfaced as
  `VndbAuthError` via the existing transport mapping (no special handling needed).

## Open Questions

- None.
