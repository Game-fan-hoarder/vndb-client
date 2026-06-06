# vndb-client

A fully typed, HTTP-based Python client for the [VNDB](https://vndb.org) (Visual
Novel Database) [Kana API](https://api.vndb.org/kana).

## Install

```bash
pip install vndb-client
```

## Quickstart

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "ever17"], results=5)
    for vn in page.results:
        print(vn.id, vn.title)
```

## Highlights

- **Sync and async** — `Client` and `AsyncClient` share one core.
- **Typed models** — Pydantic models for VNs, releases, producers, characters,
  staff, tags, traits, quotes.
- **Filter DSL** — `(vn_filters.rating >= 80) & (vn_filters.lang == "en")`.
- **User lists** — read a list, then write votes, notes, labels, and rlist state.

## Where to next

- New here? Start with [Getting started](guides/getting-started.md).
- Need a token? See [Authentication](guides/authentication.md).
- Looking for a symbol? Browse the [API reference](reference/client.md).
