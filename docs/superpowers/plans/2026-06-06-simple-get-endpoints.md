# Simple GET Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 5 simple GET endpoints (`/stats`, `/authinfo`, `/user`, `/ulist_labels`, `/schema`) as direct client methods returning typed `meta` models (raw dict for `/schema`).

**Architecture:** A private `_get(path, *, params=None)` on each client builds a GET `RequestSpec`, drops `None` params, calls `transport.send`, and returns parsed JSON. Five thin methods wrap it and parse into `Stats`/`AuthInfo`/`User`/`UlistLabel` (in `meta.py`). `core`/transport unchanged.

**Tech Stack:** Python 3.10–3.14, httpx, Pydantic v2, pytest, uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/simple-get-endpoints/` (capability `simple-get-endpoints`). **Design:** `docs/2026-06-06_simple_get_endpoints_design.md`. **Reuses:** `core.RequestSpec`, `transport.send`, `VndbModel`, `VndbParseError`.

**Conventions for every commit:**
- Run from the worktree root `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\simple-get-endpoints`; use `uv run ...`.
- Pre-commit hooks NOT installed: before each commit run `uv run ruff format`, `uv run ruff check --fix`, `uv run ruff format --check`, `uv run mypy`, and re-stage.
- New modules start with `from __future__ import annotations`.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

**httpx note:** with `base_url=".../kana"`, a request path `"/stats"` is concatenated by httpx to `".../kana/stats"` (httpx joins base path + relative path), so `request.url.path` is `"/kana/stats"` — tests assert `.path.endswith("/stats")`.

---

## Task 1: Meta models (`meta.py`)

**Files:**
- Create: `src/vndb_client/meta.py`
- Test: `tests/test_meta.py`

- [ ] **Step 1: Write the failing test** `tests/test_meta.py`:
```python
from __future__ import annotations

from vndb_client.meta import AuthInfo, Stats, UlistLabel, User


def test_stats_parses():
    s = Stats.model_validate(
        {"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7}
    )
    assert s.vn == 7
    assert s.chars == 1


def test_authinfo_parses():
    a = AuthInfo.model_validate({"id": "u1", "username": "Nemo", "permissions": ["listread", "listwrite"]})
    assert a.id == "u1"
    assert a.permissions == ["listread", "listwrite"]


def test_user_parses_and_optional_none():
    u = User.model_validate({"id": "u1", "username": "Nemo"})
    assert u.id == "u1"
    assert u.lengthvotes is None
    u2 = User.model_validate({"id": "u2", "username": "X", "lengthvotes": 10, "lengthvotes_sum": 200})
    assert u2.lengthvotes == 10
    assert u2.lengthvotes_sum == 200


def test_ulist_label_id_is_int():
    label = UlistLabel.model_validate({"id": 7, "label": "Wishlist", "private": False, "count": 42})
    assert label.id == 7
    assert isinstance(label.id, int)
    assert label.private is False
    assert label.count == 42
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_meta.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.meta'`.

- [ ] **Step 3: Implement** `src/vndb_client/meta.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class Stats(VndbModel):
    """Database-wide counts from ``GET /stats``."""

    chars: int
    producers: int
    releases: int
    staff: int
    tags: int
    traits: int
    vn: int


class AuthInfo(VndbModel):
    """Token info from ``GET /authinfo``."""

    id: str
    username: str | None = None
    permissions: list[str] | None = None


class User(VndbModel):
    """A user record from ``GET /user``."""

    id: str
    username: str | None = None
    lengthvotes: int | None = None
    lengthvotes_sum: int | None = None


class UlistLabel(VndbModel):
    """A list label from ``GET /ulist_labels`` (``id`` is an integer)."""

    id: int
    label: str | None = None
    private: bool | None = None
    count: int | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_meta.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run ruff format --check && uv run mypy
git add src/vndb_client/meta.py tests/test_meta.py
git commit -m "feat(meta): add Stats/AuthInfo/User/UlistLabel models

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: GET helper + client methods (`client.py`)

**Files:**
- Modify: `src/vndb_client/client.py`
- Test: `tests/test_get_endpoints.py`

`client.py` already imports `core` (use `core.RequestSpec`), `Any`, and `VndbParseError`. Add `cast` to the typing import and import the meta models.

- [ ] **Step 1: Write the failing test** `tests/test_get_endpoints.py`:
```python
from __future__ import annotations

import asyncio

import httpx

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.meta import AuthInfo, Stats, UlistLabel, User


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def test_stats():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7})

    with Client(http_client=_client(handler)) as client:
        result = client.stats()
    assert seen["method"] == "GET"
    assert seen["path"].endswith("/stats")
    assert isinstance(result, Stats)
    assert result.vn == 7


def test_authinfo_sends_token():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id": "u1", "username": "Nemo", "permissions": ["listread"]})

    with Client(token="tok", http_client=_client(handler)) as client:
        result = client.authinfo()
    assert seen["path"].endswith("/authinfo")
    assert seen["auth"] == "Token tok"
    assert isinstance(result, AuthInfo)
    assert result.permissions == ["listread"]


def test_get_user_multiple_and_null():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["q"] = request.url.params.get_list("q")
        seen["fields"] = request.url.params.get("fields")
        return httpx.Response(200, json={"u1": {"id": "u1", "username": "Nemo", "lengthvotes": 5}, "Ghost": None})

    with Client(http_client=_client(handler)) as client:
        result = client.get_user(["u1", "Ghost"], fields="lengthvotes")
    assert seen["path"].endswith("/user")
    assert seen["q"] == ["u1", "Ghost"]
    assert seen["fields"] == "lengthvotes"
    assert isinstance(result["u1"], User)
    assert result["u1"].lengthvotes == 5
    assert result["Ghost"] is None


def test_ulist_labels_unwraps_list():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["user"] = request.url.params.get("user")
        return httpx.Response(200, json={"labels": [{"id": 1, "label": "Playing", "private": False}, {"id": 2, "label": "Wishlist", "private": True}]})

    with Client(http_client=_client(handler)) as client:
        result = client.ulist_labels(user="u1", fields="count")
    assert seen["path"].endswith("/ulist_labels")
    assert seen["user"] == "u1"
    assert [label.id for label in result] == [1, 2]
    assert all(isinstance(label, UlistLabel) for label in result)


def test_ulist_labels_omits_none_params():
    seen = {}

    def handler(request):
        seen["query"] = str(request.url.query)
        return httpx.Response(200, json={"labels": []})

    with Client(http_client=_client(handler)) as client:
        client.ulist_labels()
    assert "user" not in seen["query"]
    assert "fields" not in seen["query"]


def test_schema_returns_raw_dict():
    def handler(request):
        return httpx.Response(200, json={"api_fields": {"vn": ["id", "title"]}, "enums": {}})

    with Client(http_client=_client(handler)) as client:
        result = client.schema()
    assert result == {"api_fields": {"vn": ["id", "title"]}, "enums": {}}


def test_async_stats_and_get_user():
    def handler(request):
        if request.url.path.endswith("/stats"):
            return httpx.Response(200, json={"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7})
        return httpx.Response(200, json={"u1": {"id": "u1", "username": "Nemo"}})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return await client.stats(), await client.get_user("u1")

    stats, users = asyncio.run(scenario())
    assert isinstance(stats, Stats)
    assert isinstance(users["u1"], User)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_get_endpoints.py -v`
Expected: FAIL — `Client` has no `stats`/etc.

- [ ] **Step 3: Edit `src/vndb_client/client.py`**

Update the typing import to include `cast`:
```python
from typing import Any, TypeVar, cast
```
Add the meta import near the other entity imports:
```python
from vndb_client.meta import AuthInfo, Stats, UlistLabel, User
```

Add these methods to `Client` (after the existing `_query` method, inside the class):
```python
    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = self._transport.send(spec)
        try:
            return response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc

    def stats(self) -> Stats:
        return Stats.model_validate(self._get("stats"))

    def authinfo(self) -> AuthInfo:
        return AuthInfo.model_validate(self._get("authinfo"))

    def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        raw = self._get("user", params={"q": q, "fields": fields})
        result: dict[str, User | None] = {}
        for key, value in raw.items():
            result[key] = User.model_validate(value) if value is not None else None
        return result

    def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        raw = self._get("ulist_labels", params={"user": user, "fields": fields})
        return [UlistLabel.model_validate(item) for item in raw["labels"]]

    def schema(self) -> dict[str, Any]:
        return cast("dict[str, Any]", self._get("schema"))
```

Add the async equivalents to `AsyncClient` (after its `_query`):
```python
    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = await self._transport.send(spec)
        try:
            return response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc

    async def stats(self) -> Stats:
        return Stats.model_validate(await self._get("stats"))

    async def authinfo(self) -> AuthInfo:
        return AuthInfo.model_validate(await self._get("authinfo"))

    async def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        raw = await self._get("user", params={"q": q, "fields": fields})
        result: dict[str, User | None] = {}
        for key, value in raw.items():
            result[key] = User.model_validate(value) if value is not None else None
        return result

    async def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        raw = await self._get("ulist_labels", params={"user": user, "fields": fields})
        return [UlistLabel.model_validate(item) for item in raw["labels"]]

    async def schema(self) -> dict[str, Any]:
        return cast("dict[str, Any]", await self._get("schema"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_get_endpoints.py -v`
Expected: PASS (all sync + async).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run ruff format --check && uv run mypy
git add src/vndb_client/client.py tests/test_get_endpoints.py
git commit -m "feat(meta): add _get helper and stats/authinfo/get_user/ulist_labels/schema methods

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Public exports

**Files:**
- Modify: `src/vndb_client/__init__.py`
- Test: `tests/test_public_api.py` (extend)

- [ ] **Step 1: Append the failing test** to `tests/test_public_api.py`:
```python
def test_meta_exports_present():
    import vndb_client

    for name in ("Stats", "AuthInfo", "User", "UlistLabel"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_public_api.py::test_meta_exports_present -v`
Expected: FAIL — names not exported.

- [ ] **Step 3: Edit `src/vndb_client/__init__.py`**

Add the import (alongside the other imports):
```python
from vndb_client.meta import AuthInfo, Stats, UlistLabel, User
```
Add `"AuthInfo"`, `"Stats"`, `"UlistLabel"`, `"User"` to `__all__` (let `ruff check --fix` apply RUF022 ordering).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/__init__.py tests/test_public_api.py
git commit -m "feat(meta): export Stats/AuthInfo/User/UlistLabel from package root

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Docs & quality gate

**Files:** Modify `docs/modules.md`.

- [ ] **Step 1: Add a usage snippet + reference block**

Append to `docs/modules.md`:
````markdown

## Simple GET endpoints

```python
from vndb_client import Client

with Client() as client:
    print(client.stats().vn)                 # total visual novels
    users = client.get_user(["u1", "Nemo"])  # {"u1": User|None, "Nemo": User|None}
```

::: vndb_client.meta
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
git commit -m "docs(meta): add simple GET endpoints usage and API reference

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Skip if nothing remains to commit.)

---

## Self-Review

**Spec coverage:**

| Capability requirement | Task |
|---|---|
| GET request helper (omit None params, wrap decode error) | Task 2 (`_get`) |
| Stats endpoint | Tasks 1, 2 |
| Authinfo endpoint (sends token) | Tasks 1, 2 |
| User lookup endpoint (repeated q, map → User\|None) | Tasks 1, 2 |
| Ulist labels endpoint (unwrap labels, int id) | Tasks 1, 2 |
| Schema endpoint (raw dict) | Task 2 |
| Public exports | Task 3 |
| Docs | Task 4 |

No gaps.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N" — every code step is complete.

**Type consistency:** `Stats`/`AuthInfo`/`User`/`UlistLabel` defined in Task 1 are imported and used identically in Tasks 2–3. `_get(path, *, params=None) -> Any` is consistent between sync and async, and between definition and the method call sites. `get_user` returns `dict[str, User | None]` and `ulist_labels` returns `list[UlistLabel]` in both clients. `core.RequestSpec(method=, path=, params=)` matches the Foundation's `RequestSpec` dataclass fields. `cast` is imported in Task 2 where `schema()` uses it.
