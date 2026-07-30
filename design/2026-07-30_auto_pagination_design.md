# Auto-pagination iterator — Design

**Status:** Approved 2026-07-30
**Beads task:** none yet — issues are created after `/opsx:propose`, mirroring the
delta spec's `tasks.md` (project convention).

## Goal

Give `QueryResource` and `AsyncQueryResource` generator methods that walk every
page of a query, so callers stop hand-rolling the `page`/`more` loop.

## Background

This is the one item from the original feature map that never shipped.
`design/2026-06-05_full_api_client_feature_map.md:33` lists it under Beta:
*"auto-pagination iterator (sync generator / async generator)"*. There is no
`yield`, `Iterator`, or `Generator` anywhere in `src/` — the backlog closed at
91/91 issues without it.

Consequently `docs/guides/querying.md:91-103` teaches the manual loop as the
supported way to page:

```python
page_no = 1
while True:
    page = client.vn.query(filters=..., results=25, page=page_no)
    ...
    if not page.more:
        break
    page_no += 1
```

Every consumer writes this, and it has two easy failure modes: forgetting to
check `more`, and mismanaging the 1-based `page` counter.

Relevant current state:

- `core.build_query_request` (`core.py:40`) omits any param that is `None`, so
  nothing imposes a page size client-side; VNDB's own default is 10 and its
  maximum is 100.
- `core.RetryPolicy` (`core.py:99`) establishes the codebase's pure-decision
  pattern: *"Pure retry decision: no I/O, no clock."*
- The transport retries 429 honoring `Retry-After` (`_transport.py:35-44`) with
  `RetryConfig.max_attempts = 3` (`config.py:16`).

## Decisions from brainstorm

1. **Expose both `pages()` and `iterate()`.** `pages()` yields `Page[T]`
   envelopes and does the real work; `iterate()` is a thin wrapper flattening to
   records. The envelope loop must exist internally regardless, so publishing it
   costs almost nothing and keeps `count`/progress reporting reachable.
2. **`limit=None` by default; opt-in cap.** A full walk is a legitimate thing to
   want, and silent truncation is the worse failure mode. Default `results` to
   100 so a full walk costs the fewest possible requests.
3. **No new throttling machinery.** `RetryConfig` is already tunable; document
   raising `max_attempts` for long walks, and add `start_page` so a walk that
   dies can resume instead of restarting. A client-side token-bucket throttle
   stays a separate transport-level feature.

## Components

### 1. `core.PageWalk` — pure pagination decision

A frozen dataclass beside `RetryPolicy`, with no I/O and no HTTP awareness:

```python
@dataclass(frozen=True)
class PageWalk:
    """Pure pagination decision: no I/O, no transport."""

    start_page: int = 1
    limit: int | None = None

    def take(self, yielded: int, available: int) -> int:
        """How many of this page's records to keep, given the record budget."""

    def should_continue(self, *, more: bool, yielded: int, available: int) -> bool:
        """Whether to request another page."""
```

In both methods `yielded` is the record count already emitted by this walk, and
`available` is `len(page.results)` **as returned by the API, before any
truncation**.

`__post_init__` raises `ValueError` for `start_page < 1` or `limit <= 0`, so
misuse fails at call time rather than on first `next()`.

Keeping the branching here means it is unit-testable without HTTP and is not
duplicated across the four generator bodies (sync/async × pages/iterate).

### 2. `pages()` / `iterate()` on both resources

```python
def pages(self, *, filters=None, fields=None, sort=None, reverse=None,
          results=100, start_page=1, limit=None, count=None, user=None,
          compact_filters=None, normalized_filters=None) -> Iterator[Page[ModelT]]

def iterate(self, ...same...) -> Iterator[ModelT]
```

`AsyncQueryResource` mirrors both as async generators returning
`AsyncIterator[...]`. `iterate()` delegates to `pages()` — it does not
re-implement the walk. Both are lazy: no request is issued until first
iteration.

Deliberate differences from `query()`:

- **No `page` parameter.** `start_page` replaces it. A caller passing `page=`
  would be fighting the component that owns paging, so the signature does not
  offer it.
- **`results` defaults to 100**, not `None`. `query()` inherits VNDB's default of
  10; for a walk the largest page is always wanted, which cuts a full VN-table
  walk from roughly 4000 requests to roughly 400. Callers may still lower it.
- **`limit` counts records, not pages**, in both methods. With `limit=250,
  results=100`, `pages()` yields pages of 100, 100, and a final page truncated to
  50 — one meaning across both methods rather than two.

Truncation yields a `model_copy` of the page with a sliced `results` list, so
`sum(len(p.results) for p in pages(limit=n)) == n`. The copy's `more` flag is
left exactly as the API reported it: `more` answers "does the server hold further
matches", which stays true even though iteration stopped.

`results` is **not** validated against 100 client-side. Defaulting to 100 encodes
today's maximum as a choice; validating it would encode it as a rule this client
must keep in sync with the API.

### 3. Usage

```python
# common case
for vn in client.vn.iterate(filters=pred):
    print(vn.title)

# envelope access — progress against the total
for page in client.vn.pages(filters=pred, count=True):
    print(f"{len(page.results)} of {page.count}")

# bounded
for vn in client.vn.iterate(filters=pred, limit=500):
    ...

# long walk: raise the retry ceiling, resume if it still dies
client = Client(retry=RetryConfig(max_attempts=8))
for vn in client.vn.iterate(filters=pred, start_page=137):
    ...

# async
async for vn in aclient.vn.iterate(filters=pred):
    ...
```

## Stopping conditions

Stop when any of:

1. `page.more` is false.
2. The record budget (`limit`) is spent.
3. **A page returns zero results despite `more=True`.** Without this guard a
   server bug or an out-of-range `start_page` produces an infinite request loop.

## Error handling

Exceptions propagate unchanged mid-iteration — `VndbRateLimitError`,
`VndbNetworkError`, and the rest surface to the caller as they do from `query()`.
Records already yielded remain valid, and `start_page` is the documented way to
resume. No exception is wrapped or swallowed by the paginator.

## Interactions to document

- **Cache thrash.** With `cache_ttl` set, each page is a distinct cache key
  (`_cache.py:20`) and `cache_maxsize` defaults to 128, so a 400-page walk
  evicts the whole LRU including unrelated entries. Not a defect, but surprising
  enough to warrant a note in the guide.
- **`count` passes through untouched.** If requested, VNDB returns it on every
  page; the paginator does not get clever about asking only once.
- **No snapshot consistency.** Offset paging over live data can skip or duplicate
  records if the database changes mid-walk. Inherent to the API; state it plainly.

## Testing

Existing mocked-httpx harness and spec-capture patterns (`tests/test_resource.py`).

- `PageWalk` unit tests, no HTTP: budget arithmetic, the three stop conditions,
  `ValueError` on invalid `start_page`/`limit`.
- Multi-page walk terminates on `more=False`; requests carry the expected
  incrementing `page` and the `results=100` default.
- `limit` truncates mid-page and the record total equals `limit`.
- `start_page` resumption begins at the requested page.
- Empty-results-with-`more=True` guard stops instead of looping.
- Laziness: constructing the generator issues no request.
- Async equivalents of each behavioural case.

## Documentation

Rewrite the pagination section of `docs/guides/querying.md` so `iterate()` is the
recommended default, keeping a `pages()` example for the envelope case and the
three interaction notes above. `docs/reference/models.md` covers resources via
mkdocstrings, so the new methods appear there once docstrings exist.

## Out of scope

- Client-side rate-limit throttling — separate transport-level feature.
- Reusing `page.compact_filters` for pages 2..N to shrink the request body:
  considered and rejected. No measured benefit, and it silently changes what is
  transmitted after the first page.

## Spec placement

This extends the existing generic query resource rather than adding a new
capability, so the delta will MODIFY `query-resource` (new `pages()`/`iterate()`
methods) and touch `documentation` for the guide rewrite. `PageWalk` lands in
`core`. Exact placement confirmed at `/opsx:propose`.

## Notes / risk

- Four generator bodies (sync/async × pages/iterate) is real duplication, but it
  matches the sync/async symmetry already used throughout `resource.py`,
  `client.py`, and `_transport.py`. `PageWalk` keeps the *decisions* single-sourced;
  only the `for`/`async for` scaffolding is repeated.
- `results=100` as a default is the only place this client hard-codes a VNDB
  quantitative limit. If the API's maximum changes, this default is the one line
  to revisit — hence no matching validation.
