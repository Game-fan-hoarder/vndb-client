# API Reference

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "ever17"], results=5)
    for vn in page.results:
        print(vn.id, vn.title)
```

::: vndb_client.client

::: vndb_client.models

::: vndb_client.entities.vn

::: vndb_client.entities.common

::: vndb_client.entities.release

::: vndb_client.entities.producer

::: vndb_client.entities.character

::: vndb_client.entities.staff

::: vndb_client.entities.tag

::: vndb_client.entities.trait

::: vndb_client.entities.quote

::: vndb_client.config

::: vndb_client.exceptions
