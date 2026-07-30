## Context

`POST /ulist` is a query endpoint (like `/vn`) but requires a `user` param; the
write endpoints (`PATCH`/`DELETE /ulist/<id>`, `/rlist/<id>`) are the first
authenticated writes, returning `204 No Content`. The Foundation transport
already handles arbitrary methods + json bodies + 204 (status < 400 → returns
response). Full brainstorm + verified shapes: `design/2026-06-06_user_lists_design.md`.

## Goals / Non-Goals

**Goals:**
- Read a user's list as `Page[UlistEntry]` via the generic resource.
- Modify ulist/rlist entries with typed write methods; full fidelity (omit vs unset).

**Non-Goals:**
- The `releases[]` array on ulist entries; auto-pagination.
- Any change to `core`/transport.

## Decisions

**1. Reuse the generic resource for read.** `client.ulist = QueryResource(self,
"ulist", UlistEntry)`. Adds a `user` param to `query()` (forwarded to the
existing `build_query_request` `user` arg). *Alternative — a custom ulist
resource:* rejected (more code, no reuse).

**2. Direct write methods + a `_write` helper.** `set_ulist`/`delete_ulist`/
`set_rlist`/`delete_rlist` call `_write(method, path, json)` → `transport.send`
→ `None`. Mirrors the GET-endpoint direct-method pattern.

**3. `UNSET` sentinel for omit-vs-unset.** `set_ulist` nullable scalars default to
`UNSET`; only non-`UNSET` fields enter the PATCH body; explicit `None` → JSON
`null` (server unsets). *Alternative — `None` means omit:* rejected (cannot
clear a field; loses real capability).

**4. Minimal nested `UlistVN`** (`id`, `title`), consistent with quote refs;
overridable via explicit `fields`. Full VN data via `client.vn.query`.

**5. `RListStatus` IntEnum mirror; `status` stays `int`.** Consistent with
`DevStatus`/`VNLength`.

**6. Idempotent retries are safe.** PATCH sets absolute values; DELETE succeeds
even if absent — so the existing 429/5xx/network retry needs no change.

## Risks / Trade-offs

- **`user` param widening on `QueryResource`** → additive; other entities ignore
  it (omitted when `None`); covered by a regression test.
- **204 has no body** → `_write` returns `None` and never calls `.json()`; no
  decode attempt.
- **Auth/permission errors** → 401 maps to `VndbAuthError` via the existing
  transport; no special-casing.
- **`UNSET` is a new public sentinel** → small surface; exported and documented;
  label-list params use `None`=omit (null not meaningful for them).

## Open Questions

- None.
