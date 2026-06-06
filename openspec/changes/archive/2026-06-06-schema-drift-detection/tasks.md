## 1. Pure comparison module

- [x] 1.1 Create `src/vndb_client/schemacheck.py` with `ENTITY_MODELS` registry (vn→VN, release→Release, producer→Producer, character→Character, staff→Staff, tag→Tag, trait→Trait, quote→Quote)
- [x] 1.2 Implement `model_field_names(model) -> set[str]` (top-level `info.alias or name`), no I/O
- [x] 1.3 Implement `parse_schema_field_names(raw_schema) -> dict[str, set[str]]`, isolating the `/schema`-shape dependency
- [x] 1.4 Implement `SchemaDriftReport` dataclass (`missing_in_schema`/`missing_in_model` per type, `has_actionable_drift`, readable `__str__`) and `diff_schema(raw_schema, models=ENTITY_MODELS) -> SchemaDriftReport`

## 2. Offline unit tests

- [x] 2.1 Test `model_field_names` returns aliases (and plain names where no alias), no network
- [x] 2.2 Test `parse_schema_field_names` extracts `{type: {fields}}` from a hand-built fake `/schema` dict
- [x] 2.3 Test `diff_schema` clean case → `has_actionable_drift` False, empty diffs
- [x] 2.4 Test `diff_schema` model-has-but-schema-lacks → name in `missing_in_schema`, `has_actionable_drift` True
- [x] 2.5 Test `diff_schema` schema-has-but-model-lacks → name in `missing_in_model`, `has_actionable_drift` False

## 3. Opt-in live runner

- [x] 3.1 Add a `__main__` entry / `main()` in `schemacheck.py` that builds a `Client`, calls `client.schema()`, runs `diff_schema`, prints the report, and exits non-zero iff `has_actionable_drift`
- [x] 3.2 Add a `make schema-check` target running `uv run python -m vndb_client.schemacheck`

## 4. Verification

- [x] 4.1 `make check` (ruff, mypy, deptry) clean and `make test` passes (offline; new tests included, coverage gate satisfied)
- [x] 4.2 `uv run mkdocs build --strict` still exit 0 (no doc regressions)
