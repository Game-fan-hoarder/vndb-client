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
