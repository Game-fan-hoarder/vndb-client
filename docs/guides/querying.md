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

Results are paged. Use `results` for page size and `page` for the page number,
and check `page.more` to decide whether to continue:

```python
from vndb_client import Client

with Client() as client:
    page_no = 1
    while True:
        page = client.vn.query(filters=["search", "=", "fate"], results=25, page=page_no)
        for vn in page.results:
            print(vn.id, vn.title)
        if not page.more:
            break
        page_no += 1
```

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
