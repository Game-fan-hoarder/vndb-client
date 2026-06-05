## 1. Dependencies & scaffolding

- [x] 1.1 Add `httpx` and `pydantic>=2` to `[project].dependencies` in `pyproject.toml` and run `uv lock`
- [x] 1.2 Remove placeholder `src/vndb_client/foo.py` and its test (`tests/test_foo.py` if present)
- [x] 1.3 Confirm `make check` (ruff + mypy + deptry) passes on the empty scaffold after dependency changes

## 2. Exceptions (`exceptions.py`)

- [x] 2.1 Write tests asserting the hierarchy: `VndbError` base; `VndbAPIError` carries `status_code` + message; subclasses `VndbBadRequestError`, `VndbAuthError`, `VndbNotFoundError`, `VndbRateLimitError`, `VndbServerError`; `VndbNetworkError` wraps an original exception
- [x] 2.2 Implement `exceptions.py` to satisfy the tests

## 3. Response models (`models.py`)

- [x] 3.1 Write tests for `VndbModel` (populate from API keys via alias generator AND by Python field name) using a small dummy model
- [x] 3.2 Write tests for generic `Page[T]`: populated results as `T`, `more` flag, optional `count` (None when absent), optional `compact_filters`/`normalized_filters`
- [x] 3.3 Implement `VndbModel` base (`model_config`: `populate_by_name`, snake↔API-key alias generator) and `Page(BaseModel, Generic[T])`

## 4. Config (`config.py`)

- [x] 4.1 Add `PROD_BASE_URL`, `SANDBOX_BASE_URL`, default timeout, default user-agent constants
- [x] 4.2 Add `RetryConfig` (max attempts default 3, base/backoff, cap, retry-on status/exception set)

## 5. Sans-I/O core (`core.py`)

- [x] 5.1 Write tests for `build_query_request`: standard body params (`filters`, `fields`, `sort`, `reverse`, `results`, `page`, `count`) serialized into a `RequestSpec`
- [x] 5.2 Write tests for `raise_for_status`: 400/401/404/429/5xx → correct exception subclass with plain-text body as message
- [x] 5.3 Write tests for `RetryPolicy.next` decision table: 429 (with/without `Retry-After`), 502/503, network exc → retry; 400/401/404 → no retry; attempts exhausted → stop; verify returned delay (Retry-After honored, else capped exponential)
- [x] 5.4 Write tests for `parse_page` against sample envelopes (incl. `more`/`count` variants) with the dummy model
- [x] 5.5 Implement `RequestSpec`, `build_query_request`, `raise_for_status`, `RetryPolicy.next`, and `parse_page` (no httpx import in this module)

## 6. Transport (`_transport.py`)

- [x] 6.1 Add a patchable sleep indirection (e.g. module-level `_sleep`/`_asleep`) so retry tests never wait in real time
- [x] 6.2 Write `SyncTransport` tests with `httpx.MockTransport`: success path; 429-then-200 retries (sleep patched); exhaustion raises mapped error; network error wrapped in `VndbNetworkError`; `Authorization` header present only when token set
- [x] 6.3 Write equivalent `AsyncTransport` tests (async handlers, `_asleep` patched)
- [x] 6.4 Implement `SyncTransport` and `AsyncTransport`: build or adopt an injected httpx client, execute a `RequestSpec`, drive the retry loop via `RetryPolicy.next` + sleep, map failures via `core.raise_for_status`

## 7. Clients (`client.py`)

- [x] 7.1 Write tests for `Client`/`AsyncClient` construction (defaults, token, injected client), lifecycle (context manager + `close()`/`aclose()`, injected client left open), and the generic `_query` returning `Page[_Dummy]` via mocked transport
- [x] 7.2 Implement `Client` and `AsyncClient`: config kwargs + optional injected httpx client, context-manager lifecycle, `close()`/`aclose()`, internal generic `_query(endpoint, model, **params)` (and `_get` helper stub for later GET endpoints)

## 8. Public API & integration

- [x] 8.1 Export `Client`, `AsyncClient`, `Page`, exception types, and `RetryConfig` from `src/vndb_client/__init__.py`
- [x] 8.2 Resolve the open question: wrap Pydantic `ValidationError` from `parse_page` in a `VndbError` subclass (default) or propagate; reflect the decision in code + tests
- [x] 8.3 Run the full quality gate: `make check` and `make test` (with coverage) green; verify under the tox matrix (3.10–3.14) at least locally for the generics
- [x] 8.4 Update `docs/` API stubs only as needed for the new public symbols (full docs are a V1 epic)
