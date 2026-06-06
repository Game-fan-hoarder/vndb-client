# VN Flagship Entity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the flagship VN entity — a typed `VN` model and a `client.vn.query(...)` surface returning `Page[VN]` — on top of the Foundation, establishing the generic query-resource and model→fields conventions every future entity reuses.

**Architecture:** A reflective `field_spec(model)` derives the VNDB `fields` string from a `VndbModel`. A generic `QueryResource`/`AsyncQueryResource` binds `(client, endpoint, model)` and wraps the Foundation's internal `_query`, defaulting `fields` to `field_spec(model)`. `VN` (+ `Title`/`Image` sub-models, `DevStatus`/`VNLength` mirror constants) is the first model; `client.vn` instantiates the resource.

**Tech Stack:** Python 3.10–3.14, httpx, Pydantic v2, pytest (async via `asyncio.run`), uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/vn-flagship-entity/` (capabilities `query-resource`, `vn-entity`). **Design:** `docs/2026-06-06_vn_flagship_design.md`. **Foundation:** `Client`/`AsyncClient._query(endpoint, model, **params) -> Page[T]`, `VndbModel`, `Page[T]`.

**Conventions for every commit:**
- Run from the worktree root `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\vn-flagship-entity`; use `uv run ...`.
- Pre-commit hooks are NOT installed: before each commit run `uv run ruff format`, `uv run ruff check --fix`, `uv run ruff format --check`, `uv run mypy`, and re-stage.
- New modules start with `from __future__ import annotations`.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

---

## Task 1: Model→fields derivation (`fields.py`)

**Files:**
- Create: `src/vndb_client/fields.py`
- Test: `tests/test_fields.py`

- [ ] **Step 1: Write the failing test**

`tests/test_fields.py`:
```python
from __future__ import annotations

from pydantic import Field

from vndb_client.fields import field_spec
from vndb_client.models import VndbModel


class _Sub(VndbModel):
    a: str
    b: int | None = None


class _M(VndbModel):
    id: str
    dev_status: int | None = Field(default=None, alias="devstatus")
    tags: list[str] | None = None
    sub: _Sub | None = None
    subs: list[_Sub] | None = None


def test_flat_fields_use_alias_or_name():
    parts = field_spec(_M).split(",")
    assert "id" in parts
    assert "devstatus" in parts          # alias is used
    assert "dev_status" not in parts     # not the python name


def test_list_of_scalar_is_bare():
    assert "tags" in field_spec(_M).split(",")


def test_single_submodel_is_dotted():
    parts = field_spec(_M).split(",")
    assert "sub.a" in parts
    assert "sub.b" in parts
    assert "sub" not in parts            # the bare parent key is not emitted


def test_list_of_submodel_is_dotted():
    parts = field_spec(_M).split(",")
    assert "subs.a" in parts
    assert "subs.b" in parts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_fields.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.fields'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/fields.py`:
```python
from __future__ import annotations

from types import UnionType
from typing import Any, Union, get_args, get_origin

from vndb_client.models import VndbModel


def _core_type(annotation: Any) -> Any:
    """Strip Optional/Union[..., None] and list/set/tuple wrappers to the core type."""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        return _core_type(non_none[0]) if len(non_none) == 1 else annotation
    if origin in (list, set, frozenset, tuple):
        args = get_args(annotation)
        return _core_type(args[0]) if args else annotation
    return annotation


def field_spec(model: type[VndbModel]) -> str:
    """Derive the VNDB ``fields`` request string from a model.

    Uses each field's alias (or name), and recurses into nested ``VndbModel``
    sub-models with dotted paths. List-of-scalar fields stay bare.
    """
    parts: list[str] = []
    for name, info in model.model_fields.items():
        key = info.alias or name
        inner = _core_type(info.annotation)
        if isinstance(inner, type) and issubclass(inner, VndbModel):
            parts.extend(f"{key}.{nested}" for nested in field_spec(inner).split(","))
        else:
            parts.append(key)
    return ",".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_fields.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/fields.py tests/test_fields.py
git commit -m "feat(vn): add field_spec model->fields derivation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: VN entity model (`entities/vn.py`)

**Files:**
- Create: `src/vndb_client/entities/__init__.py`, `src/vndb_client/entities/vn.py`
- Test: `tests/test_entities_vn.py`

- [ ] **Step 1: Write the failing test**

`tests/test_entities_vn.py`:
```python
from __future__ import annotations

from vndb_client.entities.vn import VN, DevStatus, Image, Title, VNLength

SAMPLE = {
    "id": "v17",
    "title": "Ever17",
    "alttitle": "Ever17 -The Out of Infinity-",
    "titles": [{"lang": "en", "title": "Ever17", "official": True, "main": True}],
    "aliases": ["E17"],
    "olang": "ja",
    "devstatus": 0,
    "released": "2002-08-29",
    "languages": ["ja", "en"],
    "platforms": ["win"],
    "image": {
        "id": "cv123", "url": "https://t.vndb.org/cv/123.jpg", "dims": [800, 600],
        "sexual": 0.0, "violence": 0.1, "votecount": 10,
        "thumbnail": "https://t.vndb.org/st/123.jpg", "thumbnail_dims": [256, 192],
    },
    "length": 3, "length_minutes": 3000, "length_votes": 5,
    "description": "A sci-fi mystery.", "rating": 85.0, "votecount": 1200, "average": 83.2,
}


def test_vn_parses_scalars_and_nested():
    vn = VN.model_validate(SAMPLE)
    assert vn.id == "v17"
    assert vn.rating == 85.0
    assert isinstance(vn.image, Image)
    assert vn.image.dims == [800, 600]
    assert vn.titles is not None
    assert isinstance(vn.titles[0], Title)
    assert vn.titles[0].lang == "en"


def test_vn_absent_fields_are_none():
    vn = VN.model_validate({"id": "v1"})
    assert vn.title is None
    assert vn.image is None
    assert vn.titles is None


def test_mirror_constants_compare_to_int_fields():
    vn = VN.model_validate({"id": "v1", "devstatus": 0, "length": 1})
    assert vn.devstatus == DevStatus.FINISHED
    assert vn.length == VNLength.VERY_SHORT


def test_unknown_closed_set_value_still_parses():
    vn = VN.model_validate({"id": "v1", "devstatus": 9, "length": 99})
    assert vn.devstatus == 9
    assert vn.length == 99
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_vn.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.entities'`.

- [ ] **Step 3: Write the implementation**

`src/vndb_client/entities/vn.py`:
```python
from __future__ import annotations

from enum import IntEnum

from vndb_client.models import VndbModel


class DevStatus(IntEnum):
    """Mirror of VNDB ``devstatus`` values (for comparison; not a field type)."""

    FINISHED = 0
    IN_DEVELOPMENT = 1
    CANCELLED = 2


class VNLength(IntEnum):
    """Mirror of VNDB ``length`` values (for comparison; not a field type)."""

    VERY_SHORT = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    VERY_LONG = 5


class Image(VndbModel):
    id: str
    url: str | None = None
    dims: list[int] | None = None
    sexual: float | None = None
    violence: float | None = None
    votecount: int | None = None
    thumbnail: str | None = None
    thumbnail_dims: list[int] | None = None


class Title(VndbModel):
    lang: str
    title: str | None = None
    latin: str | None = None
    official: bool | None = None
    main: bool | None = None


class VN(VndbModel):
    id: str
    title: str | None = None
    alttitle: str | None = None
    titles: list[Title] | None = None
    aliases: list[str] | None = None
    olang: str | None = None
    devstatus: int | None = None
    released: str | None = None
    languages: list[str] | None = None
    platforms: list[str] | None = None
    image: Image | None = None
    length: int | None = None
    length_minutes: int | None = None
    length_votes: int | None = None
    description: str | None = None
    rating: float | None = None
    votecount: int | None = None
    average: float | None = None
```

`src/vndb_client/entities/__init__.py`:
```python
from __future__ import annotations

from vndb_client.entities.vn import VN, DevStatus, Image, Title, VNLength

__all__ = ["VN", "DevStatus", "Image", "Title", "VNLength"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_vn.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/ tests/test_entities_vn.py
git commit -m "feat(vn): add VN model with Title/Image sub-models and mirror constants

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Generic query resource (`resource.py`)

**Files:**
- Create: `src/vndb_client/resource.py`
- Test: `tests/test_resource.py`

- [ ] **Step 1: Write the failing test**

`tests/test_resource.py`:
```python
from __future__ import annotations

import asyncio
import json

import httpx

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.entities.vn import VN
from vndb_client.fields import field_spec
from vndb_client.models import Page
from vndb_client.resource import AsyncQueryResource, QueryResource

VN_RESPONSE = {"results": [{"id": "v17", "title": "Ever17"}], "more": False, "count": 1}


def _capture():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=VN_RESPONSE)

    return captured, handler


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def test_vn_attr_is_query_resource():
    client = Client(http_client=_client(lambda r: httpx.Response(200, json=VN_RESPONSE)))
    assert isinstance(client.vn, QueryResource)


def test_query_defaults_fields_and_forwards_params():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        page = client.vn.query(filters=["search", "=", "ever"], results=5, count=True)
    assert captured["body"]["fields"] == field_spec(VN)
    assert captured["body"]["filters"] == ["search", "=", "ever"]
    assert captured["body"]["results"] == 5
    assert captured["body"]["count"] is True
    assert isinstance(page, Page)
    assert isinstance(page.results[0], VN)
    assert page.results[0].id == "v17"


def test_query_explicit_fields_override():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(fields="id,title")
    assert captured["body"]["fields"] == "id,title"


def test_async_vn_attr_and_query():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            assert isinstance(client.vn, AsyncQueryResource)
            return await client.vn.query(page=2)

    page = asyncio.run(scenario())
    assert isinstance(page.results[0], VN)
    assert captured["body"]["page"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_resource.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.resource'` (and `Client` has no `vn`).

- [ ] **Step 3: Write the implementation**

`src/vndb_client/resource.py`:
```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from vndb_client.fields import field_spec
from vndb_client.models import Page, VndbModel

if TYPE_CHECKING:
    from vndb_client.client import AsyncClient, Client

ModelT = TypeVar("ModelT", bound=VndbModel)


class QueryResource(Generic[ModelT]):
    """A typed, synchronous query resource bound to one VNDB endpoint + model."""

    def __init__(self, client: Client, endpoint: str, model: type[ModelT]) -> None:
        self._client = client
        self._endpoint = endpoint
        self._model = model

    def query(
        self,
        *,
        filters: Any = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool = False,
    ) -> Page[ModelT]:
        return self._client._query(
            self._endpoint,
            self._model,
            filters=filters,
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
        )


class AsyncQueryResource(Generic[ModelT]):
    """A typed, asynchronous query resource bound to one VNDB endpoint + model."""

    def __init__(self, client: AsyncClient, endpoint: str, model: type[ModelT]) -> None:
        self._client = client
        self._endpoint = endpoint
        self._model = model

    async def query(
        self,
        *,
        filters: Any = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool = False,
    ) -> Page[ModelT]:
        return await self._client._query(
            self._endpoint,
            self._model,
            filters=filters,
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
        )
```

- [ ] **Step 4: Wire `client.vn` in `src/vndb_client/client.py`**

Add imports near the top of `client.py` (after the existing imports):
```python
from vndb_client.entities.vn import VN
from vndb_client.resource import AsyncQueryResource, QueryResource
```

In `Client.__init__`, after `self._transport = SyncTransport(...)` assignment, add:
```python
        self.vn: QueryResource[VN] = QueryResource(self, "vn", VN)
```

In `AsyncClient.__init__`, after `self._transport = AsyncTransport(...)` assignment, add:
```python
        self.vn: AsyncQueryResource[VN] = AsyncQueryResource(self, "vn", VN)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_resource.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/resource.py src/vndb_client/client.py tests/test_resource.py
git commit -m "feat(vn): add generic QueryResource/AsyncQueryResource and wire client.vn

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Public API exports

**Files:**
- Modify: `src/vndb_client/__init__.py`
- Modify: `tests/test_public_api.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_public_api.py` a check for the new entity exports (mirror the existing `test_public_exports_present` structure):
```python
def test_vn_entity_exports_present():
    import vndb_client

    for name in ("VN", "Title", "Image", "DevStatus", "VNLength"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_public_api.py::test_vn_entity_exports_present -v`
Expected: FAIL — names not exported.

- [ ] **Step 3: Add the exports to `src/vndb_client/__init__.py`**

Add this import (alphabetically among the existing imports):
```python
from vndb_client.entities.vn import VN, DevStatus, Image, Title, VNLength
```
And add `"VN"`, `"DevStatus"`, `"Image"`, `"Title"`, `"VNLength"` to `__all__` (keep it sorted).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/__init__.py tests/test_public_api.py
git commit -m "feat(vn): export VN entity types from package root

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Docs & quality gate

**Files:**
- Modify: `docs/modules.md`

- [ ] **Step 1: Add the VN entity to the API reference**

Append to `docs/modules.md`:
```markdown

::: vndb_client.entities.vn
```
And add a short usage snippet near the top of `docs/modules.md` (after the `# API Reference` heading):
````markdown
```python
from vndb_client import Client

with Client() as client:
    page = client.vn.query(filters=["search", "=", "ever17"], results=5)
    for vn in page.results:
        print(vn.id, vn.title)
```
````

- [ ] **Step 2: Verify the strict docs build**

Run: `uv run mkdocs build --strict`
Expected: builds successfully (no broken references).

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

- [ ] **Step 4: Commit any docs/formatting changes**

```bash
git add docs/modules.md
git commit -m "docs(vn): add VN entity API reference and usage snippet

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Skip if no changes remain to commit.)

---

## Self-Review

**Spec coverage:**

| Capability / requirement | Task |
|---|---|
| `query-resource`: Model-to-fields derivation (flat/nested/list scenarios) | Task 1 (`field_spec` + tests) |
| `query-resource`: Generic query resource (default fields, override, forward params, async) | Task 3 (`QueryResource`/`AsyncQueryResource` + tests) |
| `vn-entity`: VN model (parse, absent→None, mirror compare, unknown value parses) | Task 2 |
| `vn-entity`: VN query surface (`client.vn` sync/async → `Page[VN]`) | Task 3 (wiring + tests) |
| `vn-entity`: Public exports (`VN`/`Title`/`Image`/`DevStatus`/`VNLength`) | Task 4 |
| Proposal: docs API reference + usage snippet | Task 5 |

No gaps.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N" — every code step contains complete code.

**Type consistency:** `field_spec(model: type[VndbModel]) -> str` is defined in Task 1 and called in Task 3's resource (whose `ModelT` is bound to `VndbModel`, satisfying the call). `QueryResource(client, endpoint, model)` / `AsyncQueryResource(...)` signatures and `query(*, filters, fields, sort, reverse, results, page, count)` match between Task 3's implementation, the `client.vn` wiring, and the tests. `VN`/`Title`/`Image`/`DevStatus`/`VNLength` names are consistent across Tasks 2, 4, and the tests. The resource forwards exactly the kwargs the Foundation's `build_query_request` accepts.
