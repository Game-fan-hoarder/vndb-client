## Why

Paging is currently the caller's job: `query()` exposes `page`/`results` and a
`more` flag, and `docs/guides/querying.md` teaches a hand-rolled `while True`
loop as the supported way to walk a result set. Every consumer rewrites that
loop, and it has two easy failure modes — forgetting to check `more`, and
mismanaging the 1-based `page` counter. Auto-pagination was scoped as a Beta
item in the original feature map and is the only item that never shipped; the
backlog closed at 91/91 issues without it.

## What Changes

- Add `pages()` to the synchronous and asynchronous query resources: a generator
  yielding successive `Page` envelopes for a query, requesting each page lazily.
- Add `iterate()` to both resources: a generator flattening the same walk to
  individual model records. It delegates to `pages()` rather than duplicating the
  walk.
- Add an optional record cap (`limit`) and a resumption point (`start_page`) to
  both methods. `limit` counts records, not pages, and the final page is
  truncated so the emitted record total equals `limit` exactly.
- Default the per-request page size to the API maximum (100) for both methods,
  rather than inheriting VNDB's default of 10, so a full walk costs the fewest
  requests. Callers may still lower it.
- Neither method accepts `page`; `start_page` replaces it, so a caller cannot
  fight the component that owns paging.
- Add a pure pagination-decision helper to `core` (no I/O, no transport),
  following the existing `RetryPolicy` precedent, so the stop/continue and
  budget arithmetic is single-sourced across the four generator bodies.
- Terminate a walk on `more == false`, on an exhausted record budget, **or** on a
  page that returns zero records while claiming `more == true` — the last guard
  prevents an infinite request loop.
- Rewrite the pagination section of `docs/guides/querying.md` to present
  `iterate()` as the default, keeping a `pages()` example for envelope access and
  documenting three interactions: response-cache eviction during long walks,
  `count` being returned per page, and the absence of snapshot consistency.

Not breaking: `query()` keeps its current signature and behaviour; both new
methods are additive.

## Capabilities

### New Capabilities

None. The behaviour belongs to the existing query-resource contract.

### Modified Capabilities

- `query-resource`: adds an auto-pagination requirement covering `pages()` and
  `iterate()` on both resources — lazy page-by-page requests, the record cap and
  its truncation semantics, the resumption point, the default page size, and the
  three termination conditions.

`documentation` is deliberately not listed: its requirements already mandate a
querying guide with runnable examples, and rewriting a section of that guide
changes content rather than spec-level behaviour.

## Impact

- `src/vndb_client/core.py` — new pure pagination-decision helper alongside
  `RetryPolicy`.
- `src/vndb_client/resource.py` — `pages()` and `iterate()` on both
  `QueryResource` and `AsyncQueryResource`.
- `src/vndb_client/__init__.py` — export the new helper if it is part of the
  public surface.
- `docs/guides/querying.md` — pagination section rewritten. Reference pages pick
  up the new methods automatically via mkdocstrings.
- `tests/` — new coverage for the walk helper (no HTTP) and for both resources,
  sync and async, using the existing mocked-httpx harness.
- No new dependencies. No change to the transport, retry, or cache layers; the
  interaction with `cache_maxsize` during long walks is documented, not altered.
