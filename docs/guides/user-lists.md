# User lists

Reading a list works without a token for public lists; private entries and all
writes require a token with the appropriate permission (see
[Authentication](authentication.md)).

## Reading a list

```python
from vndb_client import Client

with Client(token="your-token") as client:
    page = client.ulist.query(user="u2", fields="id,vote,vn.title")
    for entry in page.results:
        print(entry.id, entry.vote)
```

## Writing list entries

`set_ulist` patches a single VN's list entry. Every value argument defaults to
the `UNSET` sentinel, so omitted arguments are left untouched, while passing
`None` clears a field:

```python
from vndb_client import Client

with Client(token="your-token") as client:
    client.set_ulist("v17", vote=90, notes="Excellent")
    client.set_ulist("v17", labels_set=[1], labels_unset=[2])
    client.delete_ulist("v17")
```

## Release list (rlist)

```python
from vndb_client import Client

with Client(token="your-token") as client:
    client.set_rlist("r123", status=2)
    client.delete_rlist("r123")
```

`RListStatus` enumerates the documented status values and is importable from the
package root.
