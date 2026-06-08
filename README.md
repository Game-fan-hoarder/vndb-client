# vndb-client

[![Release](https://img.shields.io/github/v/release/Game-fan-hoarder/vndb-client)](https://github.com/Game-fan-hoarder/vndb-client/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/Game-fan-hoarder/vndb-client/main.yml?branch=main)](https://github.com/Game-fan-hoarder/vndb-client/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/Game-fan-hoarder/vndb-client/branch/main/graph/badge.svg)](https://codecov.io/gh/Game-fan-hoarder/vndb-client)
[![License](https://img.shields.io/github/license/Game-fan-hoarder/vndb-client)](https://github.com/Game-fan-hoarder/vndb-client/blob/main/LICENSE)

A fully typed, HTTP-based Python client for the [VNDB](https://vndb.org) (Visual Novel Database) [Kana API](https://api.vndb.org/kana).

- **Documentation:** <https://game-fan-hoarder.github.io/vndb-client/>
- **Source:** <https://github.com/Game-fan-hoarder/vndb-client/>

## Features

- Synchronous (`Client`) and asynchronous (`AsyncClient`) interfaces sharing one core.
- Typed Pydantic models for every entity: visual novels, releases, producers, characters, staff, tags, traits, quotes.
- A composable filter DSL (`from vndb_client.filters import vn_filters`) — `(vn_filters.rating >= 80) & (vn_filters.lang == "en")`.
- Simple GET endpoints: `stats`, `authinfo`, `get_user`, `ulist_labels`, `schema`.
- User-list read and write: query a user's list, then `set_ulist` / `delete_ulist` / `set_rlist` / `delete_rlist`.
- Ships `py.typed`; strict mypy-clean.

## Installation

```bash
pip install vndb-client
```

## Quickstart

Synchronous:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "ever17"], results=5)
    for vn in page.results:
        print(vn.id, vn.title)
```

Asynchronous:

```python
import asyncio
from vndb_client import AsyncClient

async def main() -> None:
    async with AsyncClient() as client:
        page = await client.vn.query(filters=["search", "=", "ever17"], results=5)
        for vn in page.results:
            print(vn.id, vn.title)

asyncio.run(main())
```

## Authentication

Read-only endpoints work without a token. User-list writes and `authinfo`
require a [VNDB API token](https://vndb.org/u/tokens):

```python
from vndb_client import Client

with Client(token="your-token") as client:
    client.set_ulist("v17", vote=90)
```

## Documentation

Full guides and the API reference live at
<https://game-fan-hoarder.github.io/vndb-client/>.

## License

MIT — see [LICENSE](https://github.com/Game-fan-hoarder/vndb-client/blob/main/LICENSE).
