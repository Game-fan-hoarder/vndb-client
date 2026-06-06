## Why

The entity models are hand-written and must match VNDB's live API field
definitions, but nothing detects when the API renames or drops a field. Such
drift surfaces only as runtime errors (the client requests a field the API no
longer accepts). A deliberate check against the live `/schema` document catches
this in CI instead.

## What Changes

- Add a pure, no-I/O comparison module `src/vndb_client/schemacheck.py`:
  - `ENTITY_MODELS` — registry mapping each queryable type name to its model.
  - `model_field_names(model)` — the top-level request keys a model declares.
  - `parse_schema_field_names(raw_schema)` — extract `{type: {field names}}` from
    the raw `/schema` dict (the only `/schema`-shape-dependent function).
  - `diff_schema(raw_schema, models=ENTITY_MODELS)` → `SchemaDriftReport`.
- `SchemaDriftReport` dataclass: per type, `missing_in_schema` (model has it,
  `/schema` lacks it — **actionable/failing**) and `missing_in_model` (`/schema`
  has it, model lacks it — **informational**), plus `has_actionable_drift` and a
  readable `__str__`.
- A thin opt-in runner (`python -m vndb_client.schemacheck`, wired to a
  `make schema-check` target) that does the one live `/schema` call, prints the
  report, and exits non-zero iff there is actionable drift.

Out of scope: code generation, nested/dotted-path comparison, type-category
checks, and `ulist` unless `/schema` documents it.

## Capabilities

### New Capabilities

- `schema-drift-detection`: comparing hand-written entity model field names
  against the live `/schema` document and reporting/ failing on actionable
  drift, via a pure comparison library plus an opt-in live runner.

### Modified Capabilities

<!-- None. This is additive; no existing capability's spec-level requirements
     change. -->

## Impact

- **New code:** `src/vndb_client/schemacheck.py` (pure comparison + registry +
  report + `__main__` runner).
- **Build:** a `make schema-check` target; the normal `make test` suite stays
  fully offline (no new network in the default test run).
- **Tests:** `tests/test_schemacheck.py` (offline unit tests over a fake
  `/schema` dict).
- **No change** to existing client/transport/entity behavior; `client.schema()`
  is reused as-is by the runner.
