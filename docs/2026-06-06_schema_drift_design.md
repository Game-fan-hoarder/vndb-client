# Schema drift detection (zkf) — Design

**Status:** Approved 2026-06-06
**Beads task:** `vndb-client-zkf` (post-V1 stretch, deferred from epic 6lp)

## Goal

Detect when the hand-written entity models fall out of sync with VNDB's live
`/schema` field definitions, so drift is caught deliberately (in CI) rather than
as surprise runtime errors. Models stay hand-authored; nothing is generated.

## Scope decisions (from brainstorm)

- **Purpose:** validate / drift-detect only — no code generation.
- **Execution model:** a pure, no-I/O comparison library plus a thin opt-in
  runner that does the one live `/schema` call. Keeps the unit suite offline.
- **Comparison depth:** top-level field-name presence per entity type only — no
  nested/dotted paths, no type-category checks (shape-tolerant, robust).

## Architecture — sans-I/O comparison + thin opt-in runner

Mirrors the project's existing sans-I/O core + thin-client split.

### `src/vndb_client/schemacheck.py` (pure, no network)

- `ENTITY_MODELS: dict[str, type[VndbModel]]` — registry mapping each queryable
  type name to its model: `"vn": VN`, `"release": Release`, `"producer":
  Producer`, `"character": Character`, `"staff": Staff`, `"tag": Tag`, `"trait":
  Trait`, `"quote": Quote`. (`ulist` excluded unless `/schema` documents it.)
- `model_field_names(model) -> set[str]` — the top-level request keys
  (`info.alias or name`) declared by one model.
- `parse_schema_field_names(raw_schema) -> dict[str, set[str]]` — extract
  `{type_name: {field_names}}` from the raw `/schema` dict. **This is the only
  `/schema`-shape-dependent piece**, deliberately isolated.
- `diff_schema(raw_schema, models=ENTITY_MODELS) -> SchemaDriftReport` — per
  type, compute the two difference sets and return a structured report.

### Drift semantics (key decision)

Per entity type, comparing model field names against `/schema` field names:

- **`missing_in_schema`** (model has it, `/schema` does not) → **actionable /
  failing**. These are renamed or removed API fields; requesting them is wrong.
  This is what fails the CI check.
- **`missing_in_model`** (`/schema` has it, model does not) → **informational
  only**. The client intentionally models a curated subset, so new API fields
  are reported but do **not** fail.

`SchemaDriftReport` is a small dataclass exposing `has_actionable_drift: bool`
plus per-type `missing_in_schema` / `missing_in_model` mappings, with a readable
`__str__`.

### Opt-in live runner

- `make schema-check` → runs a tiny runner (`python -m vndb_client.schemacheck`)
  that constructs a `Client`, calls `client.schema()`, runs `diff_schema`, prints
  the report, and **exits non-zero iff `has_actionable_drift`**. CI runs this on
  a schedule (not in the per-commit matrix), so the normal `make test` suite
  stays fully offline.

## Testing

- Offline unit tests (`tests/test_schemacheck.py`) drive every pure function with
  a small hand-built fake `/schema` dict:
  - clean case (no drift);
  - `missing_in_schema` case (asserts `has_actionable_drift` is True);
  - `missing_in_model` case (asserts reported but not actionable);
  - `model_field_names` alias handling.
  No network.
- The live runner is not unit-tested against the real API; that is the scheduled
  CI job's role.

## Out of scope

- Code generation of models or field-spec strings.
- Nested / dotted-path comparison (e.g. `vn.titles.*`).
- Type-category comparison (int/string/array/object).
- `ulist` coverage unless `/schema` documents it.

## Risk

`parse_schema_field_names` depends on the real `/schema` JSON shape, which has
not been fetched during design. It is isolated as the single shape-dependent
function; the implementer confirms the shape against a live `/schema` response
and adapts only that parser. The `diff_schema` logic and all unit tests are
shape-independent.
