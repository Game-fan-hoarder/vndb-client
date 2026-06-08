# Getting started

## Install

```bash
pip install vndb-client
```

The only runtime dependencies are `httpx` and `pydantic`.

## Your first query

`Client` is a context manager. Each entity is exposed as a query resource
(`client.vn`, `client.release`, …) with a `query()` method returning a typed
page of results.

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "ever17"], results=5)
    for vn in page.results:
        print(vn.id, vn.title)
```

`page.results` is a list of typed models; `page.more` tells you whether another
page exists; `page.count` is populated when you pass `count=True`.

## Fetch a single VN by id

There is no dedicated `get(id)` method — the VNDB API models a by-id lookup as
a filter on the `id` field. Query with an `id` equality filter and take the
first result:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["id", "=", "v17"])
    vn = page.results[0] if page.results else None
    if vn is not None:
        print(vn.id, vn.title, vn.rating)  # v17 Ever17 -the out of infinity- 84.3
```

The same works with the typed filter DSL:

```python
from vndb_client import Client
from vndb_client.filters import vn_filters

with Client() as client:
    page = client.vn.query(filters=(vn_filters.id == "v17"))
```

See [Querying](querying.md#fetch-one-entity-by-id) for the exact shape of the
returned data.

## Sync vs async

Every synchronous call has an asynchronous twin on `AsyncClient`:

```python
import asyncio
from vndb_client import AsyncClient

async def main() -> None:
    async with AsyncClient() as client:
        page = await client.vn.query(filters=["search", "=", "ever17"], results=5)
        print([vn.title for vn in page.results])

asyncio.run(main())
```

The two clients share the same parameters, models, and exceptions — only the
`await` differs.

## Next steps

- [Querying](querying.md) — fields, pagination, sorting.
- [Filtering](filtering.md) — the filter DSL.
- [Authentication](authentication.md) — when you need a token.
