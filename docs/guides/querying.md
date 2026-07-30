# Querying

Every entity resource exposes the same `query()` signature:

```python
client.vn.query(
    filters=None,   # Predicate, raw list, or None
    fields=None,    # comma-separated field string; defaults to the model's fields
    sort=None,      # field name to sort by
    reverse=None,   # reverse the sort order
    results=None,   # page size
    page=None,      # 1-based page number
    count=None,     # ask the API for the total count
    user=None,      # user id, for user-scoped endpoints like ulist
)
```

`query()` returns a single page. To walk a whole result set, use `iterate()` or
`pages()` instead — see [Pagination](#pagination).

## Fetch one entity by id

A by-id lookup is just a `query()` with an `id` equality filter. Every entity
id is a string with its type prefix (`v` for VNs, `r` for releases, `c` for
characters, …), e.g. `"v17"`:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["id", "=", "v17"])
    vn = page.results[0]
    print(vn.title)        # 'Ever17 -the out of infinity-'
    print(vn.rating)       # 84.3
    print(vn.released)     # '2002-08-29'
    print(vn.languages)    # ['en', 'ja', 'zh-Hans', ...]
```

### What you get back

`query()` always returns a `Page[VN]` envelope — even for a single id. Its
fields are:

| Field                | Type             | Meaning                                              |
| -------------------- | ---------------- | ---------------------------------------------------- |
| `results`            | `list[VN]`       | The matched models. Empty if the id does not exist.  |
| `more`               | `bool`           | Whether further pages exist (always `False` by id).  |
| `count`              | `int \| None`    | Total match count; populated only when `count=True`. |
| `compact_filters`    | `str \| None`    | Echoed compact filter string when requested.         |
| `normalized_filters` | `list \| None`   | Echoed normalised filter list when requested.        |

An unknown id is **not** an error — it returns an empty `results` list, so guard
with `page.results[0] if page.results else None`.

Each `VN` in `results` is a typed Pydantic model. The fields requested by
default include:

| Field                                | Type                | Notes                                  |
| ------------------------------------ | ------------------- | -------------------------------------- |
| `id`                                 | `str`               | Always present, e.g. `"v17"`.          |
| `title`                              | `str \| None`       | Main title in its original language.   |
| `alttitle`                           | `str \| None`       | Alternative (romanised) title.         |
| `titles`                             | `list[Title] \| None` | Per-language titles.                 |
| `aliases`                            | `list[str] \| None` | Known aliases.                         |
| `released`                           | `str \| None`       | Release date `YYYY-MM-DD`.             |
| `languages` / `platforms`            | `list[str] \| None` | Language and platform codes.           |
| `rating` / `average`                 | `float \| None`     | Bayesian rating / raw average (10–100).|
| `votecount`                          | `int \| None`       | Number of votes.                       |
| `length` / `length_minutes`          | `int \| None`       | Length bucket / play time in minutes.  |
| `description`                        | `str \| None`       | Description (may contain BBCode).      |
| `image`                              | `Image \| None`     | Cover image metadata.                  |

Pass `fields` to fetch more (e.g. nested relations); see below. Unknown keys in
the response are ignored, so a narrower or wider `fields` selection never raises.

## Fields

By default the client requests the fields its model declares. Pass `fields` to
narrow or extend the selection:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "muv-luv"], fields="id,title,rating")
    print(page.results[0].title)
```

## Pagination

Results are paged, but you rarely need to drive the paging yourself. Every
resource exposes `iterate()`, which walks the pages for you and yields records:

```python
from vndb_client import Client

with Client() as client:
    for vn in client.vn.iterate(filters=["search", "=", "fate"]):
        print(vn.id, vn.title)
```

Requests are issued lazily — one per page, as you consume it — so nothing is
sent until you start iterating. Each request asks for 100 records, the API's
maximum, so a full walk costs the fewest requests. Lower it with `results` if
you want smaller responses.

The async client mirrors this with `async for`:

```python
import asyncio
from vndb_client import AsyncClient

async def main() -> None:
    async with AsyncClient() as client:
        async for vn in client.vn.iterate(filters=["search", "=", "fate"]):
            print(vn.id, vn.title)

asyncio.run(main())
```

### Working with page envelopes

Use `pages()` instead when you need the envelope rather than bare records — for
example to report progress against the total:

```python
from vndb_client import Client

with Client() as client:
    seen = 0
    for page in client.vn.pages(filters=["search", "=", "fate"], count=True):
        seen += len(page.results)
        print(f"{seen} of {page.count}")
```

`iterate()` is the flattened form of `pages()` and delegates to it, so both share
the same walk, parameters, and stopping rules.

### Bounding a walk

Neither method stops on its own — an unfiltered `iterate()` will walk the whole
table. Pass `limit` to cap the walk. It counts **records, not pages**, and the
final page is truncated so the total is exact:

```python
with Client() as client:
    top = list(client.vn.iterate(sort="rating", reverse=True, limit=250))
    assert len(top) == 250
```

That truncated last page keeps whatever `more` value the API reported: `more`
answers "does the server hold further matches", which stays true even though
your iteration stopped.

### Resuming a long walk

Neither method accepts `page` — the walk owns the counter. What it does accept is
`start_page`, so a long walk that died part-way can resume instead of starting
over. Exceptions propagate unchanged mid-iteration, and the records already
yielded remain valid. For a walk long enough to hit rate limits, raise the retry
ceiling as well:

```python
from vndb_client import Client, RetryConfig

with Client(retry=RetryConfig(max_attempts=8)) as client:
    for vn in client.vn.iterate(filters=["search", "=", "fate"], start_page=137):
        print(vn.id)
```

### Three things to know

- **Long walks evict the response cache.** With `cache_ttl` set, every page is a
  distinct cache entry, and the cache holds `cache_maxsize` entries (default
  128). A several-hundred-page walk will therefore evict everything else in it.
- **`count` is returned on every page**, not just the first, when you request it.
  The walk passes the flag through unchanged rather than asking only once.
- **There is no snapshot consistency.** Paging is offset-based over live data, so
  if the database changes mid-walk a record can be skipped or seen twice. This is
  inherent to the API, not something the client can paper over.

If you do want the page counter yourself, `query()` still takes `results` and
`page` directly and returns a single `Page`.

## Counting

Pass `count=True` to populate `page.count` with the total number of matches:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "fate"], results=1, count=True)
    print(page.count)
```

## Sorting

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "key"], sort="rating", reverse=True)
    print([vn.title for vn in page.results])
```

## Response caching

Reads are not cached by default. Pass `cache_ttl` (seconds) to enable an
in-memory cache of read responses on a client; identical reads within the TTL are
served without a network call:

```python
from vndb_client import Client

with Client(cache_ttl=60.0) as client:
    client.vn.query(filters=["search", "=", "ever17"])  # network
    client.vn.query(filters=["search", "=", "ever17"])  # served from cache
```

The cache is per-client (not shared across clients or tokens), bounded by
`cache_maxsize` (default 128, least-recently-used eviction), and applies only to
reads — writes (`set_ulist`/`delete_ulist`/`set_rlist`/`delete_rlist`) always hit
the API. Staleness is bounded by `cache_ttl`.
