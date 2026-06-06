# Authentication

Read-only endpoints (entity queries, `stats`, `get_user`, `schema`) work
without authentication. A token is required for `authinfo` and for all
user-list writes.

## Getting a token

Create a token from your VNDB account at <https://vndb.org/u/tokens>. Grant the
`listread` permission to read private list entries, and `listwrite` to modify
lists.

## Using a token

Pass the token when constructing the client:

```python
from vndb_client import Client

with Client(token="your-token") as client:
    info = client.authinfo()
    print(info)
    client.set_ulist("v17", vote=90)
```

The same `token=` argument works on `AsyncClient`.

## Checking permissions

`authinfo()` returns the token's identity and granted permissions, which is the
quickest way to confirm a token is valid before issuing writes.
