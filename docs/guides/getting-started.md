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
