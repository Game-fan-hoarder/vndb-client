# Schema drift detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect when hand-written entity models drift from VNDB's live `/schema` field definitions, via a pure offline comparison library plus an opt-in `make schema-check` runner.

**Architecture:** A new pure module `src/vndb_client/schemacheck.py` does all logic with no I/O: an `ENTITY_MODELS` registry, `model_field_names`, `parse_schema_field_names` (the only `/schema`-shape-dependent function), and `diff_schema → SchemaDriftReport`. A thin `main()` / `__main__` runner does the single live `client.schema()` call and exits non-zero on actionable drift. Unit tests drive the pure functions with a hand-built fake `/schema` dict, so the default suite stays offline.

**Tech Stack:** Python 3.10+, Pydantic v2 (`model_fields`/`FieldInfo.alias`), dataclasses; pytest; ruff; mypy (strict); uv.

**Source of truth:** approved design `design/2026-06-06_schema_drift_design.md`; delta spec `openspec/changes/schema-drift-detection/specs/schema-drift-detection/spec.md`.

**Worktree note:** pre-commit hooks are NOT installed in this worktree. Before each commit run `uv run ruff format .` and `uv run ruff check --fix .` and re-stage.

---

## Verified facts (use verbatim)

- `VndbModel` is `src/vndb_client/models.py`; subclasses expose `model_fields: dict[str, FieldInfo]`; `FieldInfo.alias` is `str | None`. The request key for a field is `info.alias or name` (matches `fields.field_spec`).
- Entity model classes and import paths: `VN` (`vndb_client.entities.vn`), `Release` (`...release`), `Producer` (`...producer`), `Character` (`...character`), `Staff` (`...staff`), `Tag` (`...tag`), `Trait` (`...trait`), `Quote` (`...quote`).
- `Client` (`vndb_client.client`) is a context manager; `client.schema()` returns the raw `/schema` dict (`dict[str, Any]`).
- `/schema` exposes selectable fields per type under the `api_fields` key. The exact shape is confirmed at runtime by the runner (see Task 4 / Risk); the unit tests use a controlled fake dict, so they do not depend on it.

---

## Task 1: Pure registry + `model_field_names`

**Files:**
- Create: `src/vndb_client/schemacheck.py`
- Test: `tests/test_schemacheck.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemacheck.py`:

```python
from __future__ import annotations

from pydantic import Field as PydField

from vndb_client.entities.vn import VN
from vndb_client.models import VndbModel
from vndb_client.schemacheck import ENTITY_MODELS, model_field_names


def test_registry_covers_queryable_types():
    assert set(ENTITY_MODELS) == {
        "vn",
        "release",
        "producer",
        "character",
        "staff",
        "tag",
        "trait",
        "quote",
    }
    assert ENTITY_MODELS["vn"] is VN


def test_model_field_names_uses_alias_then_name():
    class M(VndbModel):
        id: str
        kind: str = PydField(default="x", alias="type")

    assert model_field_names(M) == {"id", "type"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vndb_client.schemacheck'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/vndb_client/schemacheck.py`:

```python
from __future__ import annotations

from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait
from vndb_client.entities.vn import VN
from vndb_client.models import VndbModel

ENTITY_MODELS: dict[str, type[VndbModel]] = {
    "vn": VN,
    "release": Release,
    "producer": Producer,
    "character": Character,
    "staff": Staff,
    "tag": Tag,
    "trait": Trait,
    "quote": Quote,
}


def model_field_names(model: type[VndbModel]) -> set[str]:
    """Return the top-level request field names (alias or name) a model declares."""
    return {info.alias or name for name, info in model.model_fields.items()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/schemacheck.py tests/test_schemacheck.py
uv run ruff check --fix src/vndb_client/schemacheck.py tests/test_schemacheck.py
git add src/vndb_client/schemacheck.py tests/test_schemacheck.py
git commit -m "feat(schemacheck): ENTITY_MODELS registry + model_field_names"
```

---

## Task 2: `parse_schema_field_names`

**Files:**
- Modify: `src/vndb_client/schemacheck.py`
- Test: `tests/test_schemacheck.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_schemacheck.py`:

```python
from vndb_client.schemacheck import parse_schema_field_names


def test_parse_schema_field_names_object_form():
    raw = {"api_fields": {"vn": {"id": {}, "title": {}, "_meta": {}}}}
    assert parse_schema_field_names(raw)["vn"] == {"id", "title"}  # _meta ignored


def test_parse_schema_field_names_list_form():
    raw = {"api_fields": {"vn": [{"name": "id"}, {"name": "title"}]}}
    assert parse_schema_field_names(raw)["vn"] == {"id", "title"}


def test_parse_schema_field_names_missing_api_fields_is_empty():
    assert parse_schema_field_names({}) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: FAIL with `ImportError: cannot import name 'parse_schema_field_names'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/vndb_client/schemacheck.py` (add `from typing import Any` to the imports):

```python
def parse_schema_field_names(raw_schema: dict[str, Any]) -> dict[str, set[str]]:
    """Extract ``{type_name: {field names}}`` from a raw ``/schema`` document.

    VNDB exposes selectable fields per type under the ``api_fields`` key. Each
    type maps to a container of field definitions: the top-level field names are
    the keys (object form) or each entry's ``name`` (list form). Keys beginning
    with ``_`` are treated as metadata and ignored.
    """
    api_fields = raw_schema.get("api_fields", {})
    result: dict[str, set[str]] = {}
    for type_name, fields_def in api_fields.items():
        if isinstance(fields_def, dict):
            result[type_name] = {key for key in fields_def if not key.startswith("_")}
        elif isinstance(fields_def, list):
            result[type_name] = {
                entry["name"] for entry in fields_def if isinstance(entry, dict) and "name" in entry
            }
        else:
            result[type_name] = set()
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/schemacheck.py tests/test_schemacheck.py
uv run ruff check --fix src/vndb_client/schemacheck.py tests/test_schemacheck.py
git add src/vndb_client/schemacheck.py tests/test_schemacheck.py
git commit -m "feat(schemacheck): parse_schema_field_names (object + list forms)"
```

---

## Task 3: `SchemaDriftReport` + `diff_schema`

**Files:**
- Modify: `src/vndb_client/schemacheck.py`
- Test: `tests/test_schemacheck.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_schemacheck.py`:

```python
from vndb_client.schemacheck import diff_schema


class _FakeVN(VndbModel):
    id: str
    title: str | None = None


def test_diff_schema_clean():
    raw = {"api_fields": {"vn": {"id": {}, "title": {}}}}
    report = diff_schema(raw, models={"vn": _FakeVN})
    assert report.has_actionable_drift is False
    assert report.drifts["vn"].missing_in_schema == set()
    assert report.drifts["vn"].missing_in_model == set()


def test_diff_schema_model_field_missing_from_schema_is_actionable():
    raw = {"api_fields": {"vn": {"id": {}}}}  # API dropped "title"
    report = diff_schema(raw, models={"vn": _FakeVN})
    assert report.drifts["vn"].missing_in_schema == {"title"}
    assert report.has_actionable_drift is True


def test_diff_schema_schema_field_missing_from_model_is_informational():
    raw = {"api_fields": {"vn": {"id": {}, "title": {}, "newfield": {}}}}
    report = diff_schema(raw, models={"vn": _FakeVN})
    assert report.drifts["vn"].missing_in_model == {"newfield"}
    assert report.has_actionable_drift is False


def test_diff_schema_report_str_lists_drifting_types():
    raw = {"api_fields": {"vn": {"id": {}}}}
    text = str(diff_schema(raw, models={"vn": _FakeVN}))
    assert "vn" in text
    assert "title" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: FAIL with `ImportError: cannot import name 'diff_schema'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/vndb_client/schemacheck.py` (add `from dataclasses import dataclass, field` to imports):

```python
@dataclass(frozen=True)
class TypeDrift:
    """Per-type field-name drift between a model and ``/schema``."""

    missing_in_schema: set[str]  # model declares it, /schema does not -> actionable
    missing_in_model: set[str]  # /schema lists it, model does not -> informational


@dataclass
class SchemaDriftReport:
    """Drift between the registered models and a ``/schema`` document."""

    drifts: dict[str, TypeDrift] = field(default_factory=dict)

    @property
    def has_actionable_drift(self) -> bool:
        """True if any type has model fields the live ``/schema`` no longer lists."""
        return any(drift.missing_in_schema for drift in self.drifts.values())

    def __str__(self) -> str:
        lines: list[str] = []
        for type_name, drift in sorted(self.drifts.items()):
            if not drift.missing_in_schema and not drift.missing_in_model:
                continue
            lines.append(f"{type_name}:")
            if drift.missing_in_schema:
                lines.append(f"  ! not in /schema (actionable): {sorted(drift.missing_in_schema)}")
            if drift.missing_in_model:
                lines.append(f"  + not modelled (info): {sorted(drift.missing_in_model)}")
        if not lines:
            return "No schema drift."
        verdict = "ACTIONABLE DRIFT" if self.has_actionable_drift else "informational drift only"
        return "\n".join([*lines, f"-> {verdict}"])


def diff_schema(
    raw_schema: dict[str, Any],
    models: dict[str, type[VndbModel]] | None = None,
) -> SchemaDriftReport:
    """Compare model field names against a ``/schema`` document.

    For each registered type, computes the field names the model declares but
    ``/schema`` omits (actionable) and the names ``/schema`` lists but the model
    omits (informational). Pure: performs no I/O.
    """
    models = ENTITY_MODELS if models is None else models
    schema_fields = parse_schema_field_names(raw_schema)
    report = SchemaDriftReport()
    for type_name, model in models.items():
        model_names = model_field_names(model)
        api_names = schema_fields.get(type_name, set())
        report.drifts[type_name] = TypeDrift(
            missing_in_schema=model_names - api_names,
            missing_in_model=api_names - model_names,
        )
    return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_schemacheck.py -q`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/schemacheck.py tests/test_schemacheck.py
uv run ruff check --fix src/vndb_client/schemacheck.py tests/test_schemacheck.py
git add src/vndb_client/schemacheck.py tests/test_schemacheck.py
git commit -m "feat(schemacheck): SchemaDriftReport + diff_schema"
```

---

## Task 4: Opt-in live runner + `make schema-check`

**Files:**
- Modify: `src/vndb_client/schemacheck.py`
- Modify: `Makefile`

- [ ] **Step 1: Add the runner**

Append to `src/vndb_client/schemacheck.py`:

```python
def main() -> int:
    """Fetch the live ``/schema``, report drift, and return an exit code.

    Returns ``1`` if there is actionable drift (model fields the API no longer
    lists), else ``0``. Imports ``Client`` lazily so the pure module stays
    import-light and I/O-free.
    """
    from vndb_client.client import Client

    with Client() as client:
        raw_schema = client.schema()
    report = diff_schema(raw_schema)
    print(report)
    return 1 if report.has_actionable_drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Verify the runner imports and is invokable (offline import check)**

Run: `uv run python -c "from vndb_client.schemacheck import main; print(callable(main))"`
Expected: prints `True`. (Do NOT run `python -m vndb_client.schemacheck` here — it makes a live network call; that is the scheduled CI job's role.)

- [ ] **Step 3: Add the Makefile target**

Add to `Makefile` (after the `test` target, matching the existing `.PHONY` + `@echo "🚀 ..."` style):

```makefile
.PHONY: schema-check
schema-check: ## Check entity models against the live VNDB /schema (network)
	@echo "🚀 Checking schema drift against live /schema"
	@uv run python -m vndb_client.schemacheck
```

- [ ] **Step 4: Verify the target is wired (offline)**

Run: `grep -A2 "schema-check:" Makefile`
Expected: shows the echo line and the `uv run python -m vndb_client.schemacheck` line.

- [ ] **Step 5: Commit**

```bash
uv run ruff format src/vndb_client/schemacheck.py
uv run ruff check --fix src/vndb_client/schemacheck.py
git add src/vndb_client/schemacheck.py Makefile
git commit -m "feat(schemacheck): opt-in live runner + make schema-check target"
```

---

## Task 5: Full verification

**Files:** none modified (verification only; commit only if a fix is required).

- [ ] **Step 1: Quality gate**

Run: `uv run mypy`
Expected: `Success: no issues found`.

Run: `uv run ruff format --check . && uv run ruff check .`
Expected: format check passes; `All checks passed!`.

Run: `uv run deptry src`
Expected: no dependency violations.

- [ ] **Step 2: Full offline test suite + coverage gate**

Run: `uv run python -m pytest --cov --cov-config=pyproject.toml -q`
Expected: all tests pass (154 prior + 9 new = 163), coverage `TOTAL` ≥ 90% with no fail-under message. The suite makes NO network calls.

- [ ] **Step 3: Docs build unaffected**

Run: `uv run mkdocs build --strict`
Expected: exit 0, no warnings. (No docs changed; this just confirms no regression. Remove the built `site/` afterward: `rm -rf site`.)

---

## Self-Review

**1. Spec coverage** (delta spec requirement → task):

- Pure model field-name extraction → Task 1 (`model_field_names`, test_model_field_names_uses_alias_then_name). ✓
- Pure schema field-name extraction → Task 2 (`parse_schema_field_names`, 3 tests). ✓
- Pure drift comparison (3 scenarios: no drift / actionable / informational) → Task 3 (`diff_schema`, test_diff_schema_clean / _model_field_missing_from_schema_is_actionable / _schema_field_missing_from_model_is_informational). ✓
- Opt-in live runner (fails on actionable, passes when in sync; default suite no live call) → Task 4 (`main` returns 1 iff `has_actionable_drift`; `make schema-check`); offline-ness verified in Task 5 Step 2. ✓

No spec requirement is left without a task.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to". Every code step shows complete code; every command has expected output. ✓

**3. Type/name consistency:** `ENTITY_MODELS`, `model_field_names`, `parse_schema_field_names`, `diff_schema`, `SchemaDriftReport`, `TypeDrift`, `has_actionable_drift`, `missing_in_schema`, `missing_in_model`, `main` are used identically across tasks and match the spec/design. `diff_schema(raw_schema, models=None)` defaulting to `ENTITY_MODELS` lets tests inject `{"vn": _FakeVN}`. Imports (`Any`, `dataclass`/`field`) are introduced in the task that first needs them. ✓
