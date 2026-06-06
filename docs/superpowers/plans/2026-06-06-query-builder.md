# Query Builder / Filter DSL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fluent, typed filter builder (`vndb_client.filters`) that produces VNDB's raw filter DSL via operator overloading, with per-entity namespaces, nested relational filters, and graceful degradation to raw lists.

**Architecture:** `Field` operator dunders build `Comparison` predicates; `Predicate.__and__`/`__or__` build `Compound` (flattening same-kind chains); `to_filter()` serializes to the raw nested list (recursing on `Predicate` values for nesting). Per-entity namespaces expose `Field`s; `field()` is a generic escape hatch. The query resource resolves a `Predicate` to its list form before forwarding; `core` is untouched.

**Tech Stack:** Python 3.10–3.14, Pydantic v2 (existing models), httpx, pytest, uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/query-builder/` (capability `query-builder`). **Design:** `docs/2026-06-06_query_builder_design.md`. **Reuses:** `QueryResource`/`AsyncQueryResource.query` (currently `filters: Any = None`).

**Conventions for every commit:**
- Run from the worktree root `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\query-builder`; use `uv run ...`.
- Pre-commit hooks are NOT installed: before each commit run `uv run ruff format`, `uv run ruff check --fix`, `uv run ruff format --check`, `uv run mypy`, and re-stage.
- New modules start with `from __future__ import annotations`.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

**Note on `Field` hashability:** defining `__eq__` on a class makes its instances unhashable automatically (Python sets `__hash__ = None`), so no explicit `__hash__` is needed. Only `__eq__`/`__ne__` need `# type: ignore[override]` (they return `Comparison`, not `bool`, conflicting with `object`); `__ge__/__gt__/__le__/__lt__` are not defined on `object`, so they need no ignore.

---

## Task 1: Builder primitives (`filters/predicate.py`)

**Files:**
- Create: `src/vndb_client/filters/__init__.py` (empty for now — package marker), `src/vndb_client/filters/predicate.py`
- Test: `tests/test_filters_predicate.py`

- [ ] **Step 1: Write the failing test** `tests/test_filters_predicate.py`:
```python
from __future__ import annotations

import pytest

from vndb_client.filters.predicate import Comparison, Compound, Field, Predicate, resolve_filters


def test_each_operator_maps_to_symbol():
    f = Field("rating")
    assert (f == 80).to_filter() == ["rating", "=", 80]
    assert (f != 80).to_filter() == ["rating", "!=", 80]
    assert (f >= 80).to_filter() == ["rating", ">=", 80]
    assert (f > 80).to_filter() == ["rating", ">", 80]
    assert (f <= 80).to_filter() == ["rating", "<=", 80]
    assert (f < 80).to_filter() == ["rating", "<", 80]


def test_field_is_unhashable():
    with pytest.raises(TypeError):
        {Field("x"): 1}


def test_and_or_compose():
    a = Field("lang") == "en"
    b = Field("olang") == "ja"
    assert (a & b).to_filter() == ["and", ["lang", "=", "en"], ["olang", "=", "ja"]]
    assert (a | b).to_filter() == ["or", ["lang", "=", "en"], ["olang", "=", "ja"]]


def test_same_kind_chains_flatten():
    a = Field("a") == 1
    b = Field("b") == 2
    c = Field("c") == 3
    assert (a & b & c).to_filter() == ["and", ["a", "=", 1], ["b", "=", 2], ["c", "=", 3]]
    assert (a | b | c).to_filter() == ["or", ["a", "=", 1], ["b", "=", 2], ["c", "=", 3]]


def test_mixed_kinds_nest():
    a = Field("a") == 1
    b = Field("b") == 2
    c = Field("c") == 3
    assert ((a & b) | c).to_filter() == ["or", ["and", ["a", "=", 1], ["b", "=", 2]], ["c", "=", 3]]


def test_nested_predicate_value_serializes_recursively():
    pred = Field("character") == (Field("role") == "main")
    assert pred.to_filter() == ["character", "=", ["role", "=", "main"]]


def test_nested_compound_value():
    inner = (Field("role") == "main") & (Field("trait") == "i123")
    pred = Field("character") == inner
    assert pred.to_filter() == ["character", "=", ["and", ["role", "=", "main"], ["trait", "=", "i123"]]]


def test_scalar_and_list_values_pass_through():
    assert (Field("tag") == "g546").to_filter() == ["tag", "=", "g546"]
    assert (Field("tag") == ["g546", 0, 2]).to_filter() == ["tag", "=", ["g546", 0, 2]]


def test_resolve_filters():
    pred = Field("rating") >= 80
    assert resolve_filters(pred) == ["rating", ">=", 80]
    assert resolve_filters(["search", "=", "x"]) == ["search", "=", "x"]
    assert resolve_filters(None) is None


def test_predicate_base_is_abstract():
    assert issubclass(Comparison, Predicate)
    assert issubclass(Compound, Predicate)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_filters_predicate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.filters'`.

- [ ] **Step 3: Create the package marker + implementation**

`src/vndb_client/filters/__init__.py`:
```python
from __future__ import annotations
```
(Task 3 fills in the real exports; an empty future-import file is fine for now.)

`src/vndb_client/filters/predicate.py`:
```python
from __future__ import annotations

from typing import Any


class Predicate:
    """Base class for filter predicates that serialize to VNDB's filter DSL."""

    def to_filter(self) -> list[Any]:
        raise NotImplementedError

    def __and__(self, other: Predicate) -> Compound:
        return Compound._combine("and", self, other)

    def __or__(self, other: Predicate) -> Compound:
        return Compound._combine("or", self, other)


def _serialize_value(value: Any) -> Any:
    return value.to_filter() if isinstance(value, Predicate) else value


class Comparison(Predicate):
    """A single ``[field, op, value]`` predicate."""

    def __init__(self, name: str, op: str, value: Any) -> None:
        self.name = name
        self.op = op
        self.value = value

    def to_filter(self) -> list[Any]:
        return [self.name, self.op, _serialize_value(self.value)]


class Compound(Predicate):
    """An ``["and"|"or", ...]`` predicate."""

    def __init__(self, kind: str, predicates: list[Predicate]) -> None:
        self.kind = kind
        self.predicates = predicates

    @classmethod
    def _combine(cls, kind: str, left: Predicate, right: Predicate) -> Compound:
        terms: list[Predicate] = []
        for part in (left, right):
            if isinstance(part, Compound) and part.kind == kind:
                terms.extend(part.predicates)
            else:
                terms.append(part)
        return cls(kind, terms)

    def to_filter(self) -> list[Any]:
        return [self.kind, *(p.to_filter() for p in self.predicates)]


class Field:
    """A filterable field; comparison operators build :class:`Comparison`s."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: Any) -> Comparison:  # type: ignore[override]
        return Comparison(self.name, "=", other)

    def __ne__(self, other: Any) -> Comparison:  # type: ignore[override]
        return Comparison(self.name, "!=", other)

    def __ge__(self, other: Any) -> Comparison:
        return Comparison(self.name, ">=", other)

    def __gt__(self, other: Any) -> Comparison:
        return Comparison(self.name, ">", other)

    def __le__(self, other: Any) -> Comparison:
        return Comparison(self.name, "<=", other)

    def __lt__(self, other: Any) -> Comparison:
        return Comparison(self.name, "<", other)


def resolve_filters(filters: Predicate | list[Any] | None) -> list[Any] | None:
    """Serialize a :class:`Predicate` to its list form; pass raw lists / ``None`` through."""
    if isinstance(filters, Predicate):
        return filters.to_filter()
    return filters
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_filters_predicate.py -v`
Expected: PASS (all cases).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run ruff format --check && uv run mypy
git add src/vndb_client/filters/ tests/test_filters_predicate.py
git commit -m "feat(filters): add predicate builder primitives

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

If mypy reports the `# type: ignore[override]` on `__eq__`/`__ne__` as *unused*, remove it; if it reports `[override]` errors there, keep it. (Standard mypy flags these — the ignores should be needed.)

---

## Task 2: Per-entity namespaces (`filters/namespaces.py`)

**Files:**
- Create: `src/vndb_client/filters/namespaces.py`
- Test: `tests/test_filters_namespaces.py`

Namespace fields use annotated class attributes (`name: Field = Field("name")`) — this matches the annotated-field style already used by the Pydantic models (which pass Ruff's flake8-builtins `A` rules for `id`/`type`), avoiding builtin-shadowing lint on `id`/`type`.

- [ ] **Step 1: Write the failing test** `tests/test_filters_namespaces.py`:
```python
from __future__ import annotations

from vndb_client.filters.namespaces import (
    character_filters,
    field,
    producer_filters,
    quote_filters,
    release_filters,
    staff_filters,
    tag_filters,
    trait_filters,
    vn_filters,
)
from vndb_client.filters.predicate import Field


def test_vn_namespace_fields():
    assert vn_filters.rating.name == "rating"
    assert vn_filters.tag.name == "tag"
    assert vn_filters.search.name == "search"
    assert vn_filters.character.name == "character"


def test_character_namespace_fields():
    assert character_filters.seiyuu.name == "seiyuu"
    assert character_filters.trait.name == "trait"
    assert character_filters.cup.name == "cup"


def test_other_namespaces_spot_check():
    assert release_filters.platform.name == "platform"
    assert producer_filters.type.name == "type"
    assert staff_filters.ismain.name == "ismain"
    assert tag_filters.category.name == "category"
    assert trait_filters.search.name == "search"
    assert quote_filters.random.name == "random"


def test_field_escape_hatch():
    f = field("some_new_filter")
    assert isinstance(f, Field)
    assert (f >= 5).to_filter() == ["some_new_filter", ">=", 5]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_filters_namespaces.py -v`
Expected: FAIL — `ModuleNotFoundError` / attribute errors.

- [ ] **Step 3: Implement** `src/vndb_client/filters/namespaces.py`:
```python
from __future__ import annotations

from vndb_client.filters.predicate import Field


def field(name: str) -> Field:
    """Build a :class:`Field` for an arbitrary VNDB filter name (escape hatch)."""
    return Field(name)


class _VNFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    olang: Field = Field("olang")
    platform: Field = Field("platform")
    length: Field = Field("length")
    released: Field = Field("released")
    rating: Field = Field("rating")
    votecount: Field = Field("votecount")
    has_description: Field = Field("has_description")
    has_anime: Field = Field("has_anime")
    has_screenshot: Field = Field("has_screenshot")
    has_review: Field = Field("has_review")
    devstatus: Field = Field("devstatus")
    tag: Field = Field("tag")
    dtag: Field = Field("dtag")
    anime_id: Field = Field("anime_id")
    label: Field = Field("label")
    release: Field = Field("release")
    character: Field = Field("character")
    staff: Field = Field("staff")
    developer: Field = Field("developer")


class _ReleaseFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    platform: Field = Field("platform")
    released: Field = Field("released")
    resolution: Field = Field("resolution")
    resolution_aspect: Field = Field("resolution_aspect")
    minage: Field = Field("minage")
    medium: Field = Field("medium")
    voiced: Field = Field("voiced")
    engine: Field = Field("engine")
    rtype: Field = Field("rtype")
    extlink: Field = Field("extlink")
    drm: Field = Field("drm")
    patch: Field = Field("patch")
    freeware: Field = Field("freeware")
    uncensored: Field = Field("uncensored")
    official: Field = Field("official")
    has_ero: Field = Field("has_ero")
    vn: Field = Field("vn")
    producer: Field = Field("producer")


class _ProducerFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    type: Field = Field("type")
    extlink: Field = Field("extlink")


class _CharacterFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    role: Field = Field("role")
    blood_type: Field = Field("blood_type")
    sex: Field = Field("sex")
    sex_spoil: Field = Field("sex_spoil")
    gender: Field = Field("gender")
    gender_spoil: Field = Field("gender_spoil")
    height: Field = Field("height")
    weight: Field = Field("weight")
    bust: Field = Field("bust")
    waist: Field = Field("waist")
    hips: Field = Field("hips")
    cup: Field = Field("cup")
    age: Field = Field("age")
    trait: Field = Field("trait")
    dtrait: Field = Field("dtrait")
    birthday: Field = Field("birthday")
    seiyuu: Field = Field("seiyuu")
    vn: Field = Field("vn")


class _StaffFilters:
    id: Field = Field("id")
    aid: Field = Field("aid")
    search: Field = Field("search")
    lang: Field = Field("lang")
    gender: Field = Field("gender")
    role: Field = Field("role")
    extlink: Field = Field("extlink")
    ismain: Field = Field("ismain")


class _TagFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    category: Field = Field("category")


class _TraitFilters:
    id: Field = Field("id")
    search: Field = Field("search")


class _QuoteFilters:
    id: Field = Field("id")
    vn: Field = Field("vn")
    character: Field = Field("character")
    random: Field = Field("random")


vn_filters = _VNFilters()
release_filters = _ReleaseFilters()
producer_filters = _ProducerFilters()
character_filters = _CharacterFilters()
staff_filters = _StaffFilters()
tag_filters = _TagFilters()
trait_filters = _TraitFilters()
quote_filters = _QuoteFilters()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_filters_namespaces.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/filters/namespaces.py tests/test_filters_namespaces.py
git commit -m "feat(filters): add per-entity filter namespaces and field() escape hatch

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

If Ruff flags `A003` (builtin attribute shadowing) on `id`/`type`/`type` despite the annotations, add `"src/vndb_client/filters/namespaces.py" = ["A003"]` under `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml` and re-run; commit pyproject too.

---

## Task 3: Package exports (`filters/__init__.py`)

**Files:**
- Modify: `src/vndb_client/filters/__init__.py`
- Test: `tests/test_public_api.py` (extend)

- [ ] **Step 1: Write the failing test** — append to `tests/test_public_api.py`:
```python
def test_filters_package_exports():
    import vndb_client.filters as f

    for name in (
        "vn_filters",
        "release_filters",
        "producer_filters",
        "character_filters",
        "staff_filters",
        "tag_filters",
        "trait_filters",
        "quote_filters",
        "field",
        "Predicate",
    ):
        assert hasattr(f, name), name
        assert name in f.__all__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_public_api.py::test_filters_package_exports -v`
Expected: FAIL — names not exported.

- [ ] **Step 3: Replace `src/vndb_client/filters/__init__.py`** with:
```python
from __future__ import annotations

from vndb_client.filters.namespaces import (
    character_filters,
    field,
    producer_filters,
    quote_filters,
    release_filters,
    staff_filters,
    tag_filters,
    trait_filters,
    vn_filters,
)
from vndb_client.filters.predicate import Predicate

__all__ = [
    "Predicate",
    "character_filters",
    "field",
    "producer_filters",
    "quote_filters",
    "release_filters",
    "staff_filters",
    "tag_filters",
    "trait_filters",
    "vn_filters",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/filters/__init__.py tests/test_public_api.py
git commit -m "feat(filters): export namespaces, field, and Predicate from vndb_client.filters

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Query integration (`resource.py`)

**Files:**
- Modify: `src/vndb_client/resource.py`
- Test: `tests/test_resource.py` (extend)

- [ ] **Step 1: Write the failing test** — append to `tests/test_resource.py` (helpers `_client`, `_aclient`, `_capture`, `Client`, `AsyncClient`, `httpx`, `asyncio` already present):
```python
from vndb_client.filters import vn_filters as VF


def test_query_serializes_predicate_filters():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=(VF.rating >= 80) & (VF.lang == "en"))
    assert captured["body"]["filters"] == ["and", ["rating", ">=", 80], ["lang", "=", "en"]]


def test_query_raw_list_filters_unchanged():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=["search", "=", "ever17"])
    assert captured["body"]["filters"] == ["search", "=", "ever17"]


def test_query_nested_relational_predicate():
    from vndb_client.filters import character_filters as CF

    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=VF.character == (CF.role == "main"))
    assert captured["body"]["filters"] == ["character", "=", ["role", "=", "main"]]


def test_async_query_serializes_predicate():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.vn.query(filters=VF.rating > 50)

    asyncio.run(scenario())
    assert captured["body"]["filters"] == ["rating", ">", 50]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_resource.py -k "predicate or raw_list or relational" -v`
Expected: FAIL — `filters` is sent as the `Predicate` object (not a list), so `response.json()`/body assertion fails or the request serialization errors.

- [ ] **Step 3: Edit `src/vndb_client/resource.py`**

Add the import near the top (after the existing imports):
```python
from vndb_client.filters.predicate import Predicate, resolve_filters
```
In BOTH `QueryResource.query` and `AsyncQueryResource.query`, change the `filters` parameter type from `filters: Any = None` to:
```python
        filters: Predicate | list[Any] | None = None,
```
and change the forwarded argument from `filters=filters,` to:
```python
            filters=resolve_filters(filters),
```
(Everything else in `query` stays the same. `Any` is still imported for `**`-free params; keep it.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_resource.py -v`
Expected: PASS (new predicate tests + existing tests).

- [ ] **Step 5: Format/type-check, then commit**

```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/resource.py tests/test_resource.py
git commit -m "feat(filters): accept Predicate filters in query resources (resolve to raw list)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Docs & quality gate

**Files:** Modify `docs/modules.md`.

- [ ] **Step 1: Add a filter-DSL usage snippet + reference blocks**

Append to `docs/modules.md`:
````markdown

## Filtering

```python
from vndb_client import Client
from vndb_client.filters import vn_filters as F

with Client() as client:
    page = client.vn.query(
        filters=(F.rating >= 80) & (F.lang == "en"),
        fields="id,title,rating",
    )
```

::: vndb_client.filters.predicate

::: vndb_client.filters.namespaces
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
git commit -m "docs(filters): add filter-DSL usage snippet and API reference

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Skip if nothing remains to commit.)

---

## Self-Review

**Spec coverage:**

| Capability requirement | Task |
|---|---|
| Field comparison predicates (6 operators, unhashable) | Task 1 |
| And/or composition (flatten same-kind) | Task 1 |
| Nested relational filters (recursive, scalar/list passthrough) | Task 1 |
| Per-entity namespaces + escape hatch + Predicate export | Tasks 2, 3 |
| Query integration with graceful degradation | Task 4 |
| Docs | Task 5 |

No gaps.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N" — every code step contains complete code. (The two conditional lint/mypy notes in Tasks 1–2 are explicit, bounded fallbacks, not placeholders.)

**Type consistency:** `Field`/`Predicate`/`Comparison`/`Compound`/`resolve_filters` defined in Task 1 are used consistently in Tasks 2–4. Namespace singletons (`vn_filters` … `quote_filters`) and `field` from Task 2 match the exports in Task 3 and the resource/test usage in Task 4. `resolve_filters(filters)` signature matches the resource call. `Comparison.to_filter()` recursion (`_serialize_value`) underpins the nested-filter tests. The resource `filters: Predicate | list[Any] | None` type matches `resolve_filters`'s parameter.
