# Release & docs (V1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `vndb-client` release-ready as v1.0.0 — user-facing docs (guide set + split API reference), rewritten README, CHANGELOG, packaging metadata, and a coverage floor — without performing the actual publish.

**Architecture:** This is a documentation + packaging cycle. No `src/vndb_client/**` runtime behavior changes. Because there is no new code to test-drive, the usual TDD loop is adapted: each task pairs the exact content to write with a concrete verification command (`mkdocs build --strict`, `uv build`, `make check`, `make test`, or a targeted `grep`) that must pass before committing.

**Tech Stack:** mkdocs + mkdocs-material + mkdostrings[python]; hatchling build; uv; pytest-cov; ruff; mypy; deptry.

**Source of truth:** approved design `docs/2026-06-06_release_and_docs_design.md`; delta spec `openspec/changes/release-and-docs-v1/specs/{documentation,release-packaging}/spec.md`.

**Worktree note:** pre-commit hooks are NOT installed in this worktree. Before every commit, run `uv run ruff format .` and `uv run ruff check --fix .` and re-stage. Markdown is not linted by ruff, but `pyproject.toml` is (formatting/TOML validity).

---

## Verified API facts (use these verbatim in all examples)

- Construction: `Client(token=None, *, base_url=..., timeout=..., user_agent=..., retry=None, http_client=None)`; `AsyncClient(...)` mirrors it. Both are context managers (`with` / `async with`).
- Query resources on the client: `vn`, `release`, `producer`, `character`, `staff`, `tag`, `trait`, `quote`, `ulist`. Each has `.query(*, filters=None, fields=None, sort=None, reverse=None, results=None, page=None, count=None, user=None)` returning `Page[Model]`.
- `Page` fields: `results: list[T]`, `more: bool`, `count: int | None`, `compact_filters: str | None`, `normalized_filters: list | None`.
- GET helpers: `client.stats() -> Stats`, `client.authinfo() -> AuthInfo`, `client.get_user(q, *, fields=None) -> dict[str, User | None]`, `client.ulist_labels(user=None, *, fields=None) -> list[UlistLabel]`, `client.schema() -> dict`.
- Writes (require a listwrite token): `set_ulist(vn_id, *, vote=UNSET, notes=UNSET, started=UNSET, finished=UNSET, labels=None, labels_set=None, labels_unset=None) -> None`, `delete_ulist(vn_id) -> None`, `set_rlist(release_id, *, status) -> None`, `delete_rlist(release_id) -> None`.
- Filters: `from vndb_client.filters import vn_filters, release_filters, producer_filters, character_filters, staff_filters, tag_filters, trait_filters, quote_filters, field, Predicate`. Build with comparisons + `&`/`|`, e.g. `(vn_filters.rating >= 80) & (vn_filters.lang == "en")`. A raw list filter `["search", "=", "ever17"]` is also accepted by `query(filters=...)`.
- Exceptions: `VndbError` (base) → `VndbAPIError(status_code, message)` → `VndbBadRequestError` (400), `VndbAuthError` (401), `VndbNotFoundError` (404), `VndbRateLimitError` (429), `VndbServerError` (5xx); `VndbError` → `VndbNetworkError`, `VndbParseError`.
- `RetryConfig` is importable from `vndb_client`.
- `src/vndb_client/py.typed` exists.

---

## Task 1: Packaging metadata + coverage gate

**Files:**
- Modify: `pyproject.toml` (`[project]` table lines ~1-26; `[tool.coverage.report]` line ~117)

- [ ] **Step 1: Bump the version**

In `pyproject.toml`, change:

```toml
version = "0.0.1"
```

to:

```toml
version = "1.0.0"
```

- [ ] **Step 2: Add the license field and replace placeholder keywords**

Replace:

```toml
keywords = ['python']
```

with:

```toml
license = "MIT"
license-files = ["LICENSE"]
keywords = ["vndb", "visual-novel", "api-client", "httpx", "pydantic", "async"]
```

- [ ] **Step 3: Add release classifiers**

In the `classifiers = [ ... ]` list, add these four entries (keep the existing Python-version classifiers):

```toml
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: MIT License",
    "Typing :: Typed",
    "Topic :: Internet",
```

- [ ] **Step 4: Add the coverage floor**

Change the `[tool.coverage.report]` block from:

```toml
[tool.coverage.report]
skip_empty = true
```

to:

```toml
[tool.coverage.report]
skip_empty = true
fail_under = 90
```

- [ ] **Step 5: Verify metadata is valid and the gate passes**

Run: `uv run ruff format pyproject.toml && uv lock`
Expected: formatting OK; `uv lock` regenerates `uv.lock` — the only change is the project's own `version` going `0.0.1` → `1.0.0` (dependencies are unchanged). Confirm with `git diff uv.lock` that no dependency entries changed.

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml -q`
Expected: `147 passed`, and a coverage summary with `TOTAL ... 96%` and NO `Coverage failure: total of ... is less than fail-under=90` message.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(release): set v1.0.0 metadata + 90% coverage gate"
```

---

## Task 2: Rewrite README.md

**Files:**
- Modify (full replace): `README.md`

- [ ] **Step 1: Replace the entire README with the user-facing version**

Overwrite `README.md` with exactly this content:

````markdown
# vndb-client

[![Release](https://img.shields.io/github/v/release/HOZHENWAI/vndb-client)](https://github.com/HOZHENWAI/vndb-client/releases)
[![Build status](https://img.shields.io/github/actions/workflow/status/HOZHENWAI/vndb-client/main.yml?branch=main)](https://github.com/HOZHENWAI/vndb-client/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/HOZHENWAI/vndb-client/branch/main/graph/badge.svg)](https://codecov.io/gh/HOZHENWAI/vndb-client)
[![License](https://img.shields.io/github/license/HOZHENWAI/vndb-client)](https://github.com/HOZHENWAI/vndb-client/blob/main/LICENSE)

A fully typed, HTTP-based Python client for the [VNDB](https://vndb.org) (Visual Novel Database) [Kana API](https://api.vndb.org/kana).

- **Documentation:** <https://HOZHENWAI.github.io/vndb-client/>
- **Source:** <https://github.com/HOZHENWAI/vndb-client/>

## Features

- Synchronous (`Client`) and asynchronous (`AsyncClient`) interfaces sharing one core.
- Typed Pydantic models for every entity: visual novels, releases, producers, characters, staff, tags, traits, quotes.
- A composable filter DSL — `(vn_filters.rating >= 80) & (vn_filters.lang == "en")`.
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
<https://HOZHENWAI.github.io/vndb-client/>.

## License

MIT — see [LICENSE](LICENSE).
````

- [ ] **Step 2: Verify no cookiecutter scaffolding remains**

Run: `grep -niE "create a new repository|getting started with your project|cookiecutter|git init" README.md`
Expected: no matches (exit code 1, empty output).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): rewrite as user-facing README"
```

---

## Task 3: Add CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Create the changelog**

Create `CHANGELOG.md` with exactly this content:

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-06

First stable release.

### Added

- Sans-I/O core with synchronous `Client` and asynchronous `AsyncClient`,
  sharing one request/transport layer.
- HTTP transport over `httpx` with configurable retries (`RetryConfig`),
  `Retry-After` handling, and a typed exception hierarchy (`VndbError` and
  subclasses).
- Typed query resources for `vn`, `release`, `producer`, `character`, `staff`,
  `tag`, `trait`, `quote`, and `ulist`, returning a typed `Page` envelope.
- Pydantic models for every supported entity, with field specs derived from the
  models.
- A composable filter DSL (`vn_filters`, `release_filters`, …) supporting
  comparisons and `&` / `|` composition, plus raw list filters.
- Simple GET endpoints: `stats`, `authinfo`, `get_user`, `ulist_labels`,
  `schema`.
- User-list read plus write operations: `set_ulist`, `delete_ulist`,
  `set_rlist`, `delete_rlist`, with an `UNSET` sentinel for omit-vs-null bodies.
- `py.typed` marker for downstream type checkers.

[1.0.0]: https://github.com/HOZHENWAI/vndb-client/releases/tag/1.0.0
```

- [ ] **Step 2: Verify it mentions the version**

Run: `grep -n "## \[1.0.0\]" CHANGELOG.md`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG with 1.0.0 entry"
```

---

## Task 4: Landing page (docs/index.md)

**Files:**
- Modify (full replace): `docs/index.md`

- [ ] **Step 1: Replace docs/index.md**

Overwrite `docs/index.md` with exactly this content:

````markdown
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
````

- [ ] **Step 2: Commit** (verification happens after the nav is wired, in Task 8)

```bash
git add docs/index.md
git commit -m "docs: rewrite landing page"
```

---

## Task 5: Guides — getting-started + authentication

**Files:**
- Create: `docs/guides/getting-started.md`
- Create: `docs/guides/authentication.md`

- [ ] **Step 1: Create docs/guides/getting-started.md**

````markdown
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
````

- [ ] **Step 2: Create docs/guides/authentication.md**

````markdown
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
````

- [ ] **Step 3: Commit**

```bash
git add docs/guides/getting-started.md docs/guides/authentication.md
git commit -m "docs(guides): add getting-started and authentication"
```

---

## Task 6: Guides — querying + filtering

**Files:**
- Create: `docs/guides/querying.md`
- Create: `docs/guides/filtering.md`

- [ ] **Step 1: Create docs/guides/querying.md**

````markdown
# Querying

Every entity resource exposes the same `query()` signature:

```python
client.vn.query(
    filters=None,   # Predicate, raw list, or None
    fields=None,    # comma-separated field string; defaults to the model's fields
    sort=None,      # field name to sort by
    reverse=None,   # reverse the sort order
    results=None,   # page size
    page=None,      # 1-based page number
    count=None,     # ask the API for the total count
    user=None,      # user id, for user-scoped endpoints like ulist
)
```

## Fields

By default the client requests the fields its model declares. Pass `fields` to
narrow or extend the selection:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "muv-luv"], fields="id,title,rating")
    print(page.results[0].title)
```

## Pagination

Results are paged. Use `results` for page size and `page` for the page number,
and check `page.more` to decide whether to continue:

```python
from vndb_client import Client

with Client() as client:
    page_no = 1
    while True:
        page = client.vn.query(filters=["search", "=", "fate"], results=25, page=page_no)
        for vn in page.results:
            print(vn.id, vn.title)
        if not page.more:
            break
        page_no += 1
```

## Counting

Pass `count=True` to populate `page.count` with the total number of matches:

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "fate"], results=1, count=True)
    print(page.count)
```

## Sorting

```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "key"], sort="rating", reverse=True)
    print([vn.title for vn in page.results])
```
````

- [ ] **Step 2: Create docs/guides/filtering.md**

````markdown
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
````

- [ ] **Step 3: Commit**

```bash
git add docs/guides/querying.md docs/guides/filtering.md
git commit -m "docs(guides): add querying and filtering"
```

---

## Task 7: Guides — entities + user-lists + error-handling

**Files:**
- Create: `docs/guides/entities.md`
- Create: `docs/guides/user-lists.md`
- Create: `docs/guides/error-handling.md`

- [ ] **Step 1: Create docs/guides/entities.md**

````markdown
# Entities

Each entity has a typed Pydantic model and a query resource on the client:

| Resource            | Model       | VNDB endpoint |
| ------------------- | ----------- | ------------- |
| `client.vn`         | `VN`        | `/vn`         |
| `client.release`    | `Release`   | `/release`    |
| `client.producer`   | `Producer`  | `/producer`   |
| `client.character`  | `Character` | `/character`  |
| `client.staff`      | `Staff`     | `/staff`      |
| `client.tag`        | `Tag`       | `/tag`        |
| `client.trait`      | `Trait`     | `/trait`      |
| `client.quote`      | `Quote`     | `/quote`      |
| `client.ulist`      | `UlistEntry`| `/ulist`      |

All models are importable from the package root:

```python
from vndb_client import VN, Release, Character

print(VN.model_fields.keys())
```

Models ignore unknown fields, so a response carrying extra keys will not raise.
See the [API reference](../reference/entities.md) for each model's fields.
````

- [ ] **Step 2: Create docs/guides/user-lists.md**

````markdown
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
````

- [ ] **Step 3: Create docs/guides/error-handling.md**

````markdown
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
````

- [ ] **Step 4: Commit**

```bash
git add docs/guides/entities.md docs/guides/user-lists.md docs/guides/error-handling.md
git commit -m "docs(guides): add entities, user-lists, error-handling"
```

---

## Task 8: Split API reference + wire mkdocs nav

**Files:**
- Create: `docs/reference/client.md`, `docs/reference/models.md`, `docs/reference/entities.md`, `docs/reference/filters.md`, `docs/reference/meta.md`, `docs/reference/config.md`, `docs/reference/exceptions.md`
- Delete: `docs/modules.md`
- Modify: `mkdocs.yml` (nav block, lines ~10-13)

- [ ] **Step 1: Create docs/reference/client.md**

```markdown
# Client

::: vndb_client.client
```

- [ ] **Step 2: Create docs/reference/models.md**

```markdown
# Models & resources

::: vndb_client.models

::: vndb_client.resource
```

- [ ] **Step 3: Create docs/reference/entities.md**

```markdown
# Entities

::: vndb_client.entities.vn

::: vndb_client.entities.common

::: vndb_client.entities.release

::: vndb_client.entities.producer

::: vndb_client.entities.character

::: vndb_client.entities.staff

::: vndb_client.entities.tag

::: vndb_client.entities.trait

::: vndb_client.entities.quote

::: vndb_client.entities.ulist
```

- [ ] **Step 4: Create docs/reference/filters.md**

```markdown
# Filters

::: vndb_client.filters.predicate

::: vndb_client.filters.namespaces
```

- [ ] **Step 5: Create docs/reference/meta.md**

```markdown
# GET endpoints

::: vndb_client.meta
```

- [ ] **Step 6: Create docs/reference/config.md**

```markdown
# Configuration

::: vndb_client.config
```

- [ ] **Step 7: Create docs/reference/exceptions.md**

```markdown
# Exceptions

::: vndb_client.exceptions
```

- [ ] **Step 8: Delete the old monolithic reference page**

```bash
git rm docs/modules.md
```

- [ ] **Step 9: Rewrite the mkdocs.yml nav**

Replace the existing `nav:` block:

```yaml
nav:
  - Home: index.md
  - Modules: modules.md
```

with:

```yaml
nav:
  - Home: index.md
  - Guides:
      - Getting started: guides/getting-started.md
      - Authentication: guides/authentication.md
      - Querying: guides/querying.md
      - Filtering: guides/filtering.md
      - Entities: guides/entities.md
      - User lists: guides/user-lists.md
      - Error handling: guides/error-handling.md
  - API Reference:
      - Client: reference/client.md
      - Models & resources: reference/models.md
      - Entities: reference/entities.md
      - Filters: reference/filters.md
      - GET endpoints: reference/meta.md
      - Configuration: reference/config.md
      - Exceptions: reference/exceptions.md
```

- [ ] **Step 10: Verify the strict docs build passes**

Run: `uv run mkdocs build --strict`
Expected: `INFO - Documentation built in ...`, exit code 0, and NO `WARNING` lines (strict mode turns warnings into failures). In particular there must be no "is not found in the documentation files" or "contains a link to ... which is not found" warnings.

- [ ] **Step 11: Commit**

```bash
git add docs/reference mkdocs.yml
git rm --cached docs/modules.md 2>/dev/null || true
git commit -m "docs: split API reference into per-area pages and restructure nav"
```

---

## Task 9: Final verification (build, wheel, workflow, quality gates)

**Files:** none modified (verification only; commit only if a fix is required).

- [ ] **Step 1: Confirm the wheel builds and ships py.typed**

Run: `uv build`
Expected: writes `dist/vndb_client-1.0.0-py3-none-any.whl` and `dist/vndb_client-1.0.0.tar.gz`.

Run: `python -c "import zipfile,glob; w=glob.glob('dist/vndb_client-1.0.0-py3-none-any.whl')[0]; names=zipfile.ZipFile(w).namelist(); print('py.typed' , any(n.endswith('vndb_client/py.typed') for n in names)); print('\n'.join(n for n in names if n.endswith('.dist-info/METADATA')))"`
Expected: prints `py.typed True` and the METADATA path. (`dist/` is gitignored — do not commit build artifacts.)

- [ ] **Step 2: Confirm METADATA carries the new fields**

Run: `python -c "import zipfile,glob; w=glob.glob('dist/vndb_client-1.0.0-py3-none-any.whl')[0]; z=zipfile.ZipFile(w); md=[n for n in z.namelist() if n.endswith('METADATA')][0]; t=z.read(md).decode(); print('Version 1.0.0' if 'Version: 1.0.0' in t else 'BAD VERSION'); print('MIT' if 'License' in t and 'MIT' in t else 'NO LICENSE'); print('Typed' if 'Typing :: Typed' in t else 'NO TYPED')"`
Expected: `Version 1.0.0`, `MIT`, `Typed`.

- [ ] **Step 3: Review the release workflow for consistency**

Read `.github/workflows/on-release-main.yml`. Confirm: it triggers on `release: published`; `set-version` rewrites `pyproject` version from the git tag (so the human must tag `1.0.0`); `publish` runs `uv build` + `uv publish` with `UV_PUBLISH_TOKEN`; `deploy-docs` runs `mkdocs build --clean` and deploys Pages. No change is expected — only edit if a concrete defect is found, and if so commit with message `ci: fix release workflow <detail>`.

- [ ] **Step 4: Run the full quality gate**

Run: `uv run mypy`
Expected: `Success: no issues found`.

Run: `uv run ruff format --check . && uv run ruff check .`
Expected: format check passes; `ruff check` reports `All checks passed!`.

Run: `uv run deptry src`
Expected: no missing/unused dependency violations.

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml -q`
Expected: `147 passed`; coverage `TOTAL ... 96%`; no fail-under message.

- [ ] **Step 5: Clean build artifacts**

```bash
rm -rf dist site
```

(Both are gitignored; this just keeps the worktree tidy. No commit needed if Steps 1–4 required no source edits.)

---

## Self-Review

**1. Spec coverage** (delta spec → task):

- `documentation` → Landing page: Task 4. Task-oriented guide set: Tasks 5-7 (all 7 guides). Split API reference: Task 8 (steps 1-8). Strict documentation build: Task 8 step 10. User-facing README: Task 2. Changelog: Task 3. ✓
- `release-packaging` → Release version: Task 1 step 1. License metadata: Task 1 steps 2-3. Discoverability metadata: Task 1 steps 2-3. Typed marker ships in wheel: Task 9 step 1. Coverage floor: Task 1 step 4 + verified step 5 & Task 9 step 4. Verified release workflow: Task 9 steps 1-3. ✓

No spec requirement is left without a task.

**2. Placeholder scan:** No "TBD"/"TODO"/"handle edge cases"/"similar to Task N". Every file's full content is given inline. ✓

**3. Type/name consistency:** Resource names, `query()` parameters, GET helper names, write-method signatures, exception class names, and filter namespace names all match the "Verified API facts" section, which was read directly from source. The reference `:::` module paths match the actual module layout (`vndb_client.entities.ulist` included in the entities page; `vndb_client.resource` paired with models). ✓
