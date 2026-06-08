# schema-drift-detection Specification

## Purpose
TBD - created by archiving change schema-drift-detection. Update Purpose after archive.
## Requirements
### Requirement: Pure model field-name extraction

The library SHALL expose a pure function that returns the set of top-level
request field names a given entity model declares, using each field's alias when
present and its name otherwise. It SHALL perform no I/O.

#### Scenario: Field names use aliases
- **WHEN** `model_field_names` is called with a model whose fields declare
  aliases
- **THEN** it returns the set of alias values (and plain names where no alias is
  declared), with no network access

### Requirement: Pure schema field-name extraction

The library SHALL expose a pure function that extracts, from a raw `/schema`
document, a mapping of each queryable type name to the set of field names the API
defines for it. It SHALL perform no I/O.

#### Scenario: Extract field names per type
- **WHEN** `parse_schema_field_names` is given a raw `/schema` dict
- **THEN** it returns a mapping `{type_name: {field_names}}` for the queryable
  types it describes

### Requirement: Pure drift comparison

The library SHALL expose a pure `diff_schema` function that compares the
registered entity models against a raw `/schema` document and returns a
structured drift report. For each type it SHALL compute the field names present
on the model but absent from `/schema` (actionable drift) and the field names
present in `/schema` but absent from the model (informational drift). It SHALL
perform no I/O.

#### Scenario: No drift
- **WHEN** every model's field names exactly match the corresponding `/schema`
  field names
- **THEN** the report's `has_actionable_drift` is False and both difference sets
  are empty for every type

#### Scenario: Model field missing from schema is actionable
- **WHEN** a model declares a field name that `/schema` does not list for that
  type
- **THEN** that name appears under the type's `missing_in_schema` set and the
  report's `has_actionable_drift` is True

#### Scenario: Schema field missing from model is informational
- **WHEN** `/schema` lists a field name for a type that the model does not declare
- **THEN** that name appears under the type's `missing_in_model` set and, absent
  any actionable drift, `has_actionable_drift` remains False

### Requirement: Opt-in live drift runner

The package SHALL provide an opt-in runner, invokable as
`python -m vndb_client.schemacheck` (wired to a `make schema-check` target), that
fetches the live `/schema`, runs `diff_schema`, prints the report, and exits with
a non-zero status if and only if the report has actionable drift. The default
test suite SHALL NOT perform this live call.

#### Scenario: Runner fails on actionable drift
- **WHEN** the runner is executed and the live `/schema` reveals actionable drift
- **THEN** it prints the report and exits with a non-zero status

#### Scenario: Runner passes when in sync
- **WHEN** the runner is executed and there is no actionable drift
- **THEN** it prints the report and exits zero
