## Context

The approved brainstorm for this change is `design/2026-07-30_auto_pagination_design.md`;
this document records the technical decisions and their alternatives.

Current state:

- `core.build_query_request` (`core.py:40`) omits any parameter that is `None`, so
  nothing imposes a page size client-side. VNDB's own default is 10 results per
  page and its maximum is 100.
- `core.RetryPolicy` (`core.py:99`) is the established precedent for pure
  decision logic in this codebase — *"Pure retry decision: no I/O, no clock"* —
  with the I/O loop living in `_transport.py`.
- `resource.py` holds two near-identical ~50-line classes, `QueryResource` and
  `AsyncQueryResource`, each exposing a single `query` method. The sync/async
  duplication pattern is used consistently across `resource.py`, `client.py`, and
  `_transport.py`.
- The transport retries 429/502/503 honouring `Retry-After` (`_transport.py:35`)
  with `RetryConfig.max_attempts = 3` (`config.py:16`).
- `ResponseCache` keys on the full request spec including the JSON body
  (`_cache.py:20`) and holds `cache_maxsize` entries, default 128.

## Goals / Non-Goals

**Goals:**

- Remove the hand-rolled `page`/`more` loop from every consumer's code.
- Keep the pagination decision logic single-sourced and testable without HTTP.
- Make a full walk cheap by default, and make a bounded walk exact.
- Preserve `query()` exactly as it is; this change is purely additive.

**Non-Goals:**

- Client-side rate-limit throttling. The transport already reacts to 429 with
  `Retry-After`; proactive pacing is a transport-level concern that benefits every
  request, not just pagination, and needs the real VNDB limits verified first.
- Snapshot-consistent iteration. Offset paging over live data can skip or
  duplicate records mid-walk; this is inherent to the API and will be documented,
  not worked around.
- Concurrent or prefetched page requests. Sequential walking keeps ordering
  predictable and rate-limit pressure low.
- Reusing `Page.compact_filters` for pages 2..N to shrink the request body.
  Considered and rejected: no measured benefit, and it would silently change what
  is transmitted after the first page.

## Decisions

### Expose both `pages()` and `iterate()`

`pages()` yields `Page` envelopes and performs the walk; `iterate()` flattens it
to records and is a thin wrapper. The envelope loop has to exist internally
whichever surface is published, so exposing it costs almost nothing and keeps
`count` and progress reporting reachable.

*Alternatives:* `iterate()` only — smallest surface, but callers needing
`page.count` fall back to the manual loop this change exists to remove.
`pages()` only — leaves the common case two lines longer at every call site.

### Pagination decisions live in a pure `core` helper

A frozen dataclass in `core.py` beside `RetryPolicy` answers two questions —
how many of this page's records to keep given the record budget, and whether to
request another page. It performs no I/O and knows nothing about HTTP.

This matters because the alternative is four copies of the same branching (sync
and async × `pages` and `iterate`). Putting the arithmetic and the three
termination conditions in one pure object means they are unit-testable without a
mocked transport and cannot drift between the four generator bodies, which are
then reduced to request-and-yield scaffolding.

*Alternative considered:* inline the logic in the generators, as the simplest
possible diff. Rejected — the empty-page termination guard and the budget
truncation are exactly the kind of subtle conditions that rot when duplicated.

### Unbounded by default, with an opt-in record cap

The cap defaults to absent. A full walk is a legitimate operation, and silently
returning a truncated result set is the harder failure to notice — the caller
receives N records with no signal that more existed.

*Alternative considered:* a default cap such as 1000. Rejected for the silent
truncation. *Alternative considered:* making the cap a required keyword. Rejected
because it diverges from `query()`'s all-optional signature and adds boilerplate
to every call.

### The cap counts records, and truncates the final page

One meaning across both methods: `sum(len(p.results) for p in pages(limit=n)) == n`.
Truncation yields a `model_copy` of the page with a sliced `results` list.

The truncated copy keeps the `more` value the API returned rather than forcing it
to `false`. `more` answers "does the server hold further matches", which remains
true; rewriting it would make the envelope lie about the server in order to
describe the local iteration.

### Default the page size to 100

For a walk the largest page is always wanted; inheriting VNDB's default of 10
would make a full VN-table walk cost roughly 4000 requests instead of roughly 400.

The maximum is deliberately **not** validated client-side. Defaulting to 100
encodes today's maximum as a choice; validating it would encode it as a rule this
client must keep in sync with the API, and an out-of-range value already produces
a clear 400 from the server.

### `start_page` instead of `page`

Neither method accepts `page` — a caller driving the page counter would be
fighting the component that owns it. `start_page` covers the legitimate use,
resuming a long walk that died, without handing back control of the increment.
Combined with a raised `RetryConfig.max_attempts`, this is the answer to
rate-limit interruption on long walks, in place of new throttling machinery.

## Risks / Trade-offs

- **Four generator bodies remain duplicated (sync/async × pages/iterate)** → the
  pure helper single-sources every decision, leaving only `for`/`async for`
  scaffolding. This matches the sync/async symmetry already present throughout
  the codebase, so it introduces no new pattern.
- **A long walk with caching enabled thrashes the response cache.** Each page is a
  distinct cache key and `cache_maxsize` defaults to 128, so a 400-page walk
  evicts every entry including unrelated ones → documented in the querying guide;
  not altered, since bounding pagination's cache use would mean special-casing
  reads inside a general-purpose cache.
- **`results=100` is the only place this client hard-codes a VNDB quantitative
  limit** → recorded in the design notes as the single line to revisit if the API
  maximum changes, and deliberately paired with no validation so there is only one
  such place rather than two.
- **A cap that lands exactly on a page boundary emits a final page whose `more` is
  `true`** → intended and specified; the scenario is covered so it cannot be
  "fixed" into a lie later.
- **An unbounded `iterate()` on an unfiltered query walks an entire table** →
  accepted deliberately per the cap decision above; the guide documents the cost
  and the cap.

## Open Questions

None. The three decisions that were open at brainstorm — yield shape, unbounded
default, and rate-limit handling — were resolved before this document was written.
