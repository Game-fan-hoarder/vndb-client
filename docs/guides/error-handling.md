# Error handling

All errors derive from `VndbError`, so a single `except` clause can catch
everything the client raises:

```python
from vndb_client import Client, VndbError

with Client() as client:
    try:
        page = client.vn.query(filters=["search", "=", "ever17"])
    except VndbError as exc:
        print("request failed:", exc)
```

## Exception hierarchy

- `VndbError` — base class.
  - `VndbAPIError` — the API returned an error status; carries `status_code`
    and `message`.
    - `VndbBadRequestError` — HTTP 400.
    - `VndbAuthError` — HTTP 401 (missing or invalid token).
    - `VndbNotFoundError` — HTTP 404.
    - `VndbRateLimitError` — HTTP 429.
    - `VndbServerError` — HTTP 5xx.
  - `VndbNetworkError` — the underlying transport failed (connect/read/timeout).
  - `VndbParseError` — a response could not be parsed into the expected model.

Catch a specific subclass when you want to react to one case:

```python
from vndb_client import Client, VndbAuthError

with Client(token="bad-token") as client:
    try:
        client.authinfo()
    except VndbAuthError:
        print("token is missing or invalid")
```

## Retries

Transient failures and rate limits are retried automatically according to the
`RetryConfig` passed to the client; `Retry-After` headers are honored. Construct
a client with a custom policy:

```python
from vndb_client import Client, RetryConfig

with Client(retry=RetryConfig()) as client:
    client.stats()
```
