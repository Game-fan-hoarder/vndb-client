# Filtering

`query(filters=...)` accepts either a raw VNDB filter list or a `Predicate`
built from the filter DSL.

## Raw filters

The simplest filter is a raw list, exactly as the VNDB API documents it:

```python
client.vn.query(filters=["search", "=", "ever17"])
```

## The filter DSL

Each entity has a filter namespace. Import the ones you need:

```python
from vndb_client.filters import vn_filters, release_filters
```

Build predicates with comparison operators, and compose them with `&` (and) and
`|` (or):

```python
from vndb_client import Client
from vndb_client.filters import vn_filters

with Client() as client:
    predicate = (vn_filters.rating >= 80) & (vn_filters.lang == "en")
    page = client.vn.query(filters=predicate, fields="id,title,rating")
    for vn in page.results:
        print(vn.title, vn.rating)
```

Available namespaces: `vn_filters`, `release_filters`, `producer_filters`,
`character_filters`, `staff_filters`, `tag_filters`, `trait_filters`,
`quote_filters`.

## Arbitrary fields

For a field without a namespace attribute, use `field`:

```python
from vndb_client.filters import field

predicate = field("released") >= "2010-01-01"
```
