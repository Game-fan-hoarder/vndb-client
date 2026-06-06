# User Lists Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ulist read (`POST /ulist` → `Page[UlistEntry]` via the generic resource) and ulist/rlist writes (`PATCH`/`DELETE`, the first authenticated write path).

**Architecture:** Read reuses `QueryResource` (gaining a `user` param) with a new `UlistEntry` model. Writes are direct client methods (`set_ulist`/`delete_ulist`/`set_rlist`/`delete_rlist`) backed by a `_write(method, path, json) -> None` helper over the existing transport (handles PATCH/DELETE + json + 204). An `UNSET` sentinel distinguishes omit from unset.

**Tech Stack:** Python 3.10–3.14, httpx, Pydantic v2, pytest, uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/user-lists/` (capability `user-lists`). **Design:** `docs/2026-06-06_user_lists_design.md`. **Reuses:** `QueryResource`/`AsyncQueryResource.query`, `core.RequestSpec`, `transport.send`, `VndbModel`.

**Conventions for every commit:**
- Run from the worktree root `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\user-lists`; use `uv run ...`.
- Pre-commit hooks NOT installed: before each commit run `uv run ruff format`, `uv run ruff check --fix`, `uv run ruff format --check`, `uv run mypy`, and re-stage.
- New modules start with `from __future__ import annotations`.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

---

## Task 1: Ulist read models (`entities/ulist.py`)

**Files:** Create `src/vndb_client/entities/ulist.py`; Test `tests/test_entities_ulist.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_ulist.py`:
```python
from __future__ import annotations

from vndb_client.entities.ulist import UlistEntry, UlistEntryLabel, UlistVN
from vndb_client.fields import field_spec

SAMPLE = {
    "id": "v17",
    "added": 1600000000,
    "voted": None,
    "lastmod": 1600000100,
    "vote": 85,
    "started": "2020-01-01",
    "finished": None,
    "notes": "great",
    "labels": [{"id": 1, "label": "Finished", "private": False}],
    "vn": {"id": "v17", "title": "Ever17"},
}


def test_ulist_entry_parses():
    e = UlistEntry.model_validate(SAMPLE)
    assert e.id == "v17"
    assert e.vote == 85
    assert e.voted is None
    assert isinstance(e.labels[0], UlistEntryLabel)
    assert e.labels[0].id == 1
    assert isinstance(e.vn, UlistVN)
    assert e.vn.title == "Ever17"


def test_ulist_entry_absent_fields_none():
    e = UlistEntry.model_validate({"id": "v1"})
    assert e.vote is None
    assert e.labels is None
    assert e.vn is None


def test_field_spec_includes_nested_excludes_releases():
    parts = field_spec(UlistEntry).split(",")
    assert "labels.id" in parts
    assert "vn.title" in parts
    assert "releases" not in parts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_ulist.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.entities.ulist'`.

- [ ] **Step 3: Implement** `src/vndb_client/entities/ulist.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class UlistVN(VndbModel):
    """Minimal VN reference inside a ulist entry."""

    id: str
    title: str | None = None


class UlistEntryLabel(VndbModel):
    """A label on a ulist entry."""

    id: int
    label: str | None = None
    private: bool | None = None


class UlistEntry(VndbModel):
    """A user's list entry from ``POST /ulist``."""

    id: str
    added: int | None = None
    voted: int | None = None
    lastmod: int | None = None
    vote: int | None = None
    started: str | None = None
    finished: str | None = None
    notes: str | None = None
    labels: list[UlistEntryLabel] | None = None
    vn: UlistVN | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_ulist.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run ruff format --check && uv run mypy
git add src/vndb_client/entities/ulist.py tests/test_entities_ulist.py
git commit -m "feat(ulist): add UlistEntry read models

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: QueryResource `user` parameter (`resource.py`)

**Files:** Modify `src/vndb_client/resource.py`; Test `tests/test_resource.py` (extend).

- [ ] **Step 1: Write the failing test** — append to `tests/test_resource.py` (helpers `_client`, `_capture`, `Client`, `httpx`, `vn_filters`/`VF` already present):
```python
def test_query_forwards_user_param():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(user="u2")
    assert captured["body"]["user"] == "u2"


def test_query_omits_user_when_absent():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query()
    assert "user" not in captured["body"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_resource.py -k user -v`
Expected: FAIL — `query()` got an unexpected keyword argument `user`.

- [ ] **Step 3: Edit `src/vndb_client/resource.py`**

In BOTH `QueryResource.query` and `AsyncQueryResource.query`: add a keyword-only parameter `user: str | None = None` to the signature (place it after `count`), and add `user=user,` to the `self._client._query(...)` call's keyword arguments. For example, `QueryResource.query` becomes:
```python
    def query(
        self,
        *,
        filters: Predicate | list[Any] | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool | None = None,
        user: str | None = None,
    ) -> Page[ModelT]:
        return self._client._query(
            self._endpoint,
            self._model,
            filters=resolve_filters(filters),
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
            user=user,
        )
```
Apply the identical change (with `await`) to `AsyncQueryResource.query`. (`core.build_query_request` already accepts a `user` keyword.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_resource.py -k user -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/resource.py tests/test_resource.py
git commit -m "feat(ulist): add user param to query resources

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Wire ulist read (`client.py`)

**Files:** Modify `src/vndb_client/client.py`; Test `tests/test_resource.py` (extend).

- [ ] **Step 1: Write the failing test** — append to `tests/test_resource.py`:
```python
def test_ulist_resource_query():
    from vndb_client.entities.ulist import UlistEntry
    from vndb_client.fields import field_spec

    captured, handler = _capture()

    def ulist_handler(request):
        captured["body"] = __import__("json").loads(request.content)
        return httpx.Response(200, json={"results": [{"id": "v17", "vote": 85}], "more": False})

    with Client(http_client=_client(ulist_handler)) as client:
        assert isinstance(client.ulist, QueryResource)
        page = client.ulist.query(user="u2")
    assert captured["body"]["user"] == "u2"
    assert captured["body"]["fields"] == field_spec(UlistEntry)
    assert page.results[0].id == "v17"
    assert isinstance(page.results[0], UlistEntry)


def test_async_ulist_resource():
    from vndb_client.entities.ulist import UlistEntry

    def handler(request):
        return httpx.Response(200, json={"results": [{"id": "v17"}], "more": False})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            assert isinstance(client.ulist, AsyncQueryResource)
            return await client.ulist.query(user="u2")

    page = asyncio.run(scenario())
    assert isinstance(page.results[0], UlistEntry)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_resource.py -k ulist -v`
Expected: FAIL — `Client` has no `ulist`.

- [ ] **Step 3: Edit `src/vndb_client/client.py`**

Add the import (near the other entity imports):
```python
from vndb_client.entities.ulist import UlistEntry
```
In `Client.__init__`, after the existing entity resource wirings (e.g. after `self.quote = ...`), add:
```python
        self.ulist: QueryResource[UlistEntry] = QueryResource(self, "ulist", UlistEntry)
```
In `AsyncClient.__init__`, similarly add:
```python
        self.ulist: AsyncQueryResource[UlistEntry] = AsyncQueryResource(self, "ulist", UlistEntry)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_resource.py -k ulist -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/client.py tests/test_resource.py
git commit -m "feat(ulist): wire client.ulist read resource

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Write support — sentinel, RListStatus, `_write` + 4 methods

**Files:** Modify `src/vndb_client/entities/ulist.py`, `src/vndb_client/client.py`; Test `tests/test_ulist_writes.py`.

- [ ] **Step 1: Write the failing test** `tests/test_ulist_writes.py`:
```python
from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.entities.ulist import RListStatus
from vndb_client.exceptions import VndbAuthError


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _capture():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content) if request.content else None
        return httpx.Response(204)

    return seen, handler


def test_set_ulist_partial_body():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        result = client.set_ulist("v17", vote=80, notes="x")
    assert result is None
    assert seen["method"] == "PATCH"
    assert seen["path"].endswith("/ulist/v17")
    assert seen["body"] == {"vote": 80, "notes": "x"}


def test_set_ulist_none_unsets():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17", vote=None)
    assert seen["body"] == {"vote": None}


def test_set_ulist_empty_body():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17")
    assert seen["body"] == {}


def test_set_ulist_labels_set():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17", labels_set=[1, 2])
    assert seen["body"] == {"labels_set": [1, 2]}


def test_delete_ulist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.delete_ulist("v17")
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/ulist/v17")


def test_set_rlist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_rlist("r5", status=2)
    assert seen["method"] == "PATCH"
    assert seen["path"].endswith("/rlist/r5")
    assert seen["body"] == {"status": 2}
    assert RListStatus.OBTAINED == 2


def test_delete_rlist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.delete_rlist("r5")
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/rlist/r5")


def test_write_auth_error():
    def handler(request):
        return httpx.Response(401, text="Invalid token")

    with Client(http_client=_client(handler)) as client, pytest.raises(VndbAuthError):
        client.delete_ulist("v17")


def test_async_set_ulist_and_delete():
    seen, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.set_ulist("v17", vote=90)
            await client.delete_rlist("r5")

    asyncio.run(scenario())
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/rlist/r5")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_ulist_writes.py -v`
Expected: FAIL — `RListStatus` not defined / `Client` has no `set_ulist`.

- [ ] **Step 3: Add sentinel + enum to `src/vndb_client/entities/ulist.py`**

Add at the top imports: `from enum import IntEnum`. Append to the module:
```python
class UnsetType:
    """Sentinel marking a PATCH field as 'not provided' (distinct from None=unset)."""

    def __repr__(self) -> str:
        return "UNSET"


UNSET = UnsetType()


class RListStatus(IntEnum):
    """Mirror of VNDB rlist ``status`` values (for comparison; not a field type)."""

    UNKNOWN = 0
    PENDING = 1
    OBTAINED = 2
    ON_LOAN = 3
    DELETED = 4
```

- [ ] **Step 4: Add `_write` + write methods to `src/vndb_client/client.py`**

Add the import (with the ulist read import from Task 3):
```python
from vndb_client.entities.ulist import UNSET, UlistEntry, UnsetType
```
Add to `Client` (after the GET methods / before `close`):
```python
    def _write(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> None:
        spec = core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)
        self._transport.send(spec)

    def set_ulist(
        self,
        vn_id: str,
        *,
        vote: int | None | UnsetType = UNSET,
        notes: str | None | UnsetType = UNSET,
        started: str | None | UnsetType = UNSET,
        finished: str | None | UnsetType = UNSET,
        labels: list[int] | None = None,
        labels_set: list[int] | None = None,
        labels_unset: list[int] | None = None,
    ) -> None:
        body: dict[str, Any] = {}
        if vote is not UNSET:
            body["vote"] = vote
        if notes is not UNSET:
            body["notes"] = notes
        if started is not UNSET:
            body["started"] = started
        if finished is not UNSET:
            body["finished"] = finished
        if labels is not None:
            body["labels"] = labels
        if labels_set is not None:
            body["labels_set"] = labels_set
        if labels_unset is not None:
            body["labels_unset"] = labels_unset
        self._write("PATCH", f"ulist/{vn_id}", json=body)

    def delete_ulist(self, vn_id: str) -> None:
        self._write("DELETE", f"ulist/{vn_id}")

    def set_rlist(self, release_id: str, *, status: int) -> None:
        self._write("PATCH", f"rlist/{release_id}", json={"status": status})

    def delete_rlist(self, release_id: str) -> None:
        self._write("DELETE", f"rlist/{release_id}")
```
Add the async mirror to `AsyncClient` (identical bodies; `async def`, `await self._transport.send(spec)` in `_write`, and `await self._write(...)` in each method):
```python
    async def _write(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> None:
        spec = core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)
        await self._transport.send(spec)

    async def set_ulist(
        self,
        vn_id: str,
        *,
        vote: int | None | UnsetType = UNSET,
        notes: str | None | UnsetType = UNSET,
        started: str | None | UnsetType = UNSET,
        finished: str | None | UnsetType = UNSET,
        labels: list[int] | None = None,
        labels_set: list[int] | None = None,
        labels_unset: list[int] | None = None,
    ) -> None:
        body: dict[str, Any] = {}
        if vote is not UNSET:
            body["vote"] = vote
        if notes is not UNSET:
            body["notes"] = notes
        if started is not UNSET:
            body["started"] = started
        if finished is not UNSET:
            body["finished"] = finished
        if labels is not None:
            body["labels"] = labels
        if labels_set is not None:
            body["labels_set"] = labels_set
        if labels_unset is not None:
            body["labels_unset"] = labels_unset
        await self._write("PATCH", f"ulist/{vn_id}", json=body)

    async def delete_ulist(self, vn_id: str) -> None:
        await self._write("DELETE", f"ulist/{vn_id}")

    async def set_rlist(self, release_id: str, *, status: int) -> None:
        await self._write("PATCH", f"rlist/{release_id}", json={"status": status})

    async def delete_rlist(self, release_id: str) -> None:
        await self._write("DELETE", f"rlist/{release_id}")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_ulist_writes.py -v`
Expected: PASS (all sync + async).

- [ ] **Step 6: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/ulist.py src/vndb_client/client.py tests/test_ulist_writes.py
git commit -m "feat(ulist): add ulist/rlist write methods with UNSET sentinel

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Public exports

**Files:** Modify `src/vndb_client/__init__.py`; Test `tests/test_public_api.py` (extend).

- [ ] **Step 1: Append the failing test** to `tests/test_public_api.py`:
```python
def test_user_list_exports_present():
    import vndb_client

    for name in ("UlistEntry", "UlistEntryLabel", "UlistVN", "RListStatus", "UNSET"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_public_api.py::test_user_list_exports_present -v`
Expected: FAIL — names not exported.

- [ ] **Step 3: Edit `src/vndb_client/__init__.py`**

Add the import (alongside the others):
```python
from vndb_client.entities.ulist import UNSET, RListStatus, UlistEntry, UlistEntryLabel, UlistVN
```
Add `"RListStatus"`, `"UNSET"`, `"UlistEntry"`, `"UlistEntryLabel"`, `"UlistVN"` to `__all__` (let `ruff check --fix` apply RUF022 ordering).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/__init__.py tests/test_public_api.py
git commit -m "feat(ulist): export user-list symbols from package root

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Docs & quality gate

**Files:** Modify `docs/modules.md`.

- [ ] **Step 1: Add a usage snippet + reference block**

Append to `docs/modules.md`:
````markdown

## User lists

```python
from vndb_client import Client

with Client(token="...") as client:        # listread/listwrite token
    page = client.ulist.query(user="u2", fields="id,vote,vn.title")
    client.set_ulist("v17", vote=90)        # rate/notes/etc.
    client.delete_ulist("v17")
```

::: vndb_client.entities.ulist
````

- [ ] **Step 2: Verify the strict docs build**

Run: `uv run mkdocs build --strict`
Expected: builds successfully.

- [ ] **Step 3: Run the full quality gate**

Run, expecting all green:
```bash
uv run python -m pytest
uv run mypy
uv run ruff check
uv run ruff format --check
uv run deptry src
tox
```
Expected: pytest all pass; mypy clean; ruff clean; deptry clean; tox OK on py310–py314.

- [ ] **Step 4: Commit docs/any fixups**

```bash
git add docs/modules.md
git commit -m "docs(ulist): add user lists usage and API reference

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Skip if nothing remains to commit.)

---

## Self-Review

**Spec coverage:**

| Capability requirement | Task |
|---|---|
| Query resource `user` parameter | Task 2 |
| UlistEntry model | Task 1 |
| Read a user's list | Task 3 |
| Write helper and 204 handling | Task 4 (`_write`, 401 test) |
| Modify ulist entries (UNSET omit/unset, labels) | Task 4 |
| Modify rlist entries (RListStatus) | Task 4 |
| Public exports | Task 5 |
| Docs | Task 6 |

No gaps.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N" — every code step is complete. (Task 2's edit is described as exact added lines with the full method shown; Task 4's async block is given in full.)

**Type consistency:** `UlistEntry`/`UlistEntryLabel`/`UlistVN` (Task 1) are used in Tasks 3, 5 and tests. `UNSET`/`UnsetType`/`RListStatus` (Task 4) are used in `client.py` signatures and exports (Task 5). `_write(method, path, *, json=None) -> None` is consistent sync/async and matches `core.RequestSpec(method, path, json, params)`. `set_ulist`/`delete_ulist`/`set_rlist`/`delete_rlist` signatures match between sync/async and the tests. `client.ulist` is a `QueryResource[UlistEntry]` consistent with the read tests. The `user` param added in Task 2 is exercised by Task 3's ulist query.
