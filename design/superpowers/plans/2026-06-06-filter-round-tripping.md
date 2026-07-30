# Compact↔normalized filter round-tripping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `query()` request VNDB's echoed filter forms (`compact_filters`/`normalized_filters` flags) and accept a returned compact `str` as `filters`, enabling the API-mediated round-trip.

**Architecture:** Three small, layered changes: add two boolean request flags to the sans-I/O request builder (`core.build_query_request`), widen `resolve_filters`'s input type to accept a compact `str` (pass-through, no logic change), and thread the flags + widened `filters` type through both `QueryResource.query` and `AsyncQueryResource.query`. Backward compatible — every new param defaults to `None`.

**Tech Stack:** Python 3.10+, Pydantic v2, httpx; pytest with `httpx.MockTransport` for request-body capture.

**Source of truth:** approved design `design/2026-06-06_filter_round_tripping_design.md`; delta spec `openspec/changes/filter-round-tripping/specs/query-resource/spec.md` (MODIFIED "Generic query resource").

**Worktree note:** pre-commit hooks are NOT installed here. Before each commit run `uv run ruff format .` and `uv run ruff check --fix .` and re-stage.

---

## Verified facts (use verbatim)

- `core.build_query_request(endpoint, *, filters=None, fields=None, sort=None, reverse=None, results=None, page=None, count=None, user=None)` builds the POST body, adding each param only when not `None`.
- `client._query(endpoint, model, **params)` forwards `**params` straight into `core.build_query_request`, so a new kwarg added to both `query()` and `build_query_request` flows through automatically.
- `resolve_filters(filters: Predicate | list[Any] | None) -> list[Any] | None` (in `src/vndb_client/filters/predicate.py`) returns `filters.to_filter()` for a `Predicate`, else passes the value through unchanged.
- `QueryResource.query` / `AsyncQueryResource.query` (in `src/vndb_client/resource.py`) currently type `filters: Predicate | list[Any] | None` and forward `filters=resolve_filters(filters)` plus the other params to `_query`.
- Test helper `_capture()` in `tests/test_resource.py` returns `(captured, handler)`; `captured["body"]` is the JSON request body. `_client(handler)` / `_aclient(handler)` build mock-transport clients. `VN_RESPONSE` is the canned response.

---

## Task 1: Request flags in `core.build_query_request`

**Files:**
- Modify: `src/vndb_client/core.py` (`build_query_request`)
- Test: `tests/test_core.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_core.py`:

```python
def test_build_query_request_includes_filter_echo_flags_when_set():
    spec = core.build_query_request("vn", compact_filters=True, normalized_filters=True)
    assert spec.json["compact_filters"] is True
    assert spec.json["normalized_filters"] is True


def test_build_query_request_omits_filter_echo_flags_when_unset():
    spec = core.build_query_request("vn", filters=["id", "=", "v1"])
    assert "compact_filters" not in spec.json
    assert "normalized_filters" not in spec.json
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_core.py -q -k filter_echo`
Expected: FAIL with `TypeError: build_query_request() got an unexpected keyword argument 'compact_filters'`.

- [ ] **Step 3: Write minimal implementation**

In `src/vndb_client/core.py`, add the two params to `build_query_request`'s signature (after `user: str | None = None,`):

```python
    compact_filters: bool | None = None,
    normalized_filters: bool | None = None,
```

And add the two body assignments (after the `if user is not None:` block, before `return`):

```python
    if compact_filters is not None:
        body["compact_filters"] = compact_filters
    if normalized_filters is not None:
        body["normalized_filters"] = normalized_filters
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_core.py -q -k filter_echo`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/core.py tests/test_core.py
uv run ruff check --fix src/vndb_client/core.py tests/test_core.py
git add src/vndb_client/core.py tests/test_core.py
git commit -m "feat(core): compact_filters/normalized_filters request flags"
```

---

## Task 2: Widen `resolve_filters` to accept a compact string

**Files:**
- Modify: `src/vndb_client/filters/predicate.py` (`resolve_filters`)
- Test: `tests/test_filters_predicate.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_filters_predicate.py`:

```python
def test_resolve_filters_passes_compact_string_through():
    assert resolve_filters("compact-opaque-string") == "compact-opaque-string"
```

- [ ] **Step 2: Run test to verify it fails (type-check level)**

Run: `uv run python -m pytest tests/test_filters_predicate.py -q -k compact_string`
Expected: PASS at runtime (the function already returns the value), but `uv run mypy` would currently reject a `str` argument at call sites. This task makes `str` a declared, type-checked input. Run `uv run mypy` after Step 3 to confirm.

- [ ] **Step 3: Widen the signature**

In `src/vndb_client/filters/predicate.py`, change `resolve_filters`:

```python
def resolve_filters(filters: Predicate | list[Any] | str | None) -> list[Any] | str | None:
    """Serialize a :class:`Predicate` to its list form; pass raw lists, compact
    strings, and ``None`` through unchanged."""
    if isinstance(filters, Predicate):
        return filters.to_filter()
    return filters
```

- [ ] **Step 4: Run test + mypy to verify**

Run: `uv run python -m pytest tests/test_filters_predicate.py -q -k compact_string`
Expected: PASS.
Run: `uv run mypy`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/filters/predicate.py tests/test_filters_predicate.py
uv run ruff check --fix src/vndb_client/filters/predicate.py tests/test_filters_predicate.py
git add src/vndb_client/filters/predicate.py tests/test_filters_predicate.py
git commit -m "feat(filters): resolve_filters accepts a compact filter string"
```

---

## Task 3: Thread flags + widened `filters` through the query resources

**Files:**
- Modify: `src/vndb_client/resource.py` (`QueryResource.query`, `AsyncQueryResource.query`)
- Test: `tests/test_resource.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_resource.py`:

```python
def test_query_forwards_filter_echo_flags_and_compact_string():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters="compact-xyz", compact_filters=True, normalized_filters=True)
    assert captured["body"]["filters"] == "compact-xyz"
    assert captured["body"]["compact_filters"] is True
    assert captured["body"]["normalized_filters"] is True


def test_query_omits_filter_echo_flags_when_unset():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query()
    assert "compact_filters" not in captured["body"]
    assert "normalized_filters" not in captured["body"]


def test_async_query_forwards_filter_echo_flags_and_compact_string():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.vn.query(filters="compact-async", normalized_filters=True)

    asyncio.run(scenario())
    assert captured["body"]["filters"] == "compact-async"
    assert captured["body"]["normalized_filters"] is True
    assert "compact_filters" not in captured["body"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_resource.py -q -k "filter_echo or compact"`
Expected: FAIL with `TypeError: query() got an unexpected keyword argument 'compact_filters'`.

- [ ] **Step 3: Update both query methods**

In `src/vndb_client/resource.py`, for BOTH `QueryResource.query` and `AsyncQueryResource.query`:

(a) widen the `filters` parameter type and add the two flags to the signature — change:

```python
        filters: Predicate | list[Any] | None = None,
```
to:
```python
        filters: Predicate | list[Any] | str | None = None,
```
and add (after `user: str | None = None,`):
```python
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
```

(b) forward the two flags in the `_query` call — change the call's argument list (after `user=user,`) to also pass:

```python
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
```

(c) extend each method's docstring with one line: note that `compact_filters` / `normalized_filters` are *request* flags asking the API to echo those forms into the returned `Page`, and that `filters` accepts a compact `str` returned from a previous `Page`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_resource.py -q`
Expected: PASS (all resource tests, including the 3 new ones).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/resource.py tests/test_resource.py
uv run ruff check --fix src/vndb_client/resource.py tests/test_resource.py
git add src/vndb_client/resource.py tests/test_resource.py
git commit -m "feat(resource): filter-echo flags + compact-string filters on query()"
```

---

## Task 4: Document the round-trip

**Files:**
- Modify: `docs/guides/filtering.md`

- [ ] **Step 1: Append a round-trip section**

Add to the END of `docs/guides/filtering.md`:

````markdown
## Round-tripping compact and normalized filters

VNDB can echo your filters back in two forms — a compact, opaque string and the
explicit normalized list. Ask for them with the request flags, then reuse either
form as `filters` in a later query (the compact string cannot be decoded locally;
the conversion is done by the API):

```python
from vndb_client import Client
from vndb_client.filters import vn_filters

with Client() as client:
    page = client.vn.query(
        filters=(vn_filters.rating >= 80),
        compact_filters=True,
        normalized_filters=True,
    )
    print(page.compact_filters)     # opaque string
    print(page.normalized_filters)  # explicit nested list

    # Feed either form straight back into another query:
    more = client.vn.query(filters=page.compact_filters, results=25)
```
````

- [ ] **Step 2: Verify the docs build (strict)**

Run: `uv run mkdocs build --strict`
Expected: exit 0, no warnings. Then `rm -rf site`.

- [ ] **Step 3: Commit**

```bash
git add docs/guides/filtering.md
git commit -m "docs(guides): add filter round-tripping example"
```

---

## Task 5: Full verification

**Files:** none modified (verification only; commit only if a fix is required).

- [ ] **Step 1: Quality gate**

Run: `uv run mypy` → `Success: no issues found`.
Run: `uv run ruff format --check . && uv run ruff check .` → format check passes; `All checks passed!`.
Run: `uv run deptry src` → no violations.

- [ ] **Step 2: Full test suite + coverage gate**

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml -q`
Expected: all tests pass (165 prior + 6 new = 171), coverage `TOTAL` ≥ 90% with no fail-under message.

- [ ] **Step 3: Docs build**

Run: `uv run mkdocs build --strict` → exit 0, no warnings; then `rm -rf site`.

---

## Self-Review

**1. Spec coverage** (MODIFIED "Generic query resource" → task):

- Flags accepted on `query()` and sent only when set → Task 1 (builder) + Task 3 (resources); scenario "Filter-echo flags forwarded" → `test_query_forwards_filter_echo_flags_and_compact_string` + `test_query_omits_filter_echo_flags_when_unset`. ✓
- `filters` accepts Predicate / list / compact str / None → Task 2 (`resolve_filters`) + Task 3 (signature); scenario "Compact filter string fed back" → `test_query_forwards_filter_echo_flags_and_compact_string` (filters="compact-xyz"). ✓
- `True` populates the matching `Page` field → behavioral (the flags reach the body; `Page` already parses the response fields). Verified by the body-capture tests. ✓
- Async parity → `test_async_query_forwards_filter_echo_flags_and_compact_string`. ✓
- Existing params (`fields`/`sort`/`reverse`/`results`/`page`/`count`/`user`) unchanged → untouched in the signature; existing tests still pass (Task 5 Step 2). ✓

**2. Placeholder scan:** No "TBD"/"handle edge cases". Every code step shows the exact change; every command has expected output. ✓

**3. Type/name consistency:** `compact_filters`/`normalized_filters` (bool|None) and the widened `filters: Predicate | list[Any] | str | None` are used identically in `build_query_request`, `resolve_filters`, and both `query()` methods. The `_query(**params)` pass-through means no intermediate signature needs the new kwargs. ✓
