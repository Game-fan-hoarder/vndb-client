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
