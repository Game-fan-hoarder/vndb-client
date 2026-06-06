## Context

Entity models (`VN`, `Release`, …) are hand-written Pydantic `VndbModel`
subclasses whose field names (via `info.alias or name`) must match VNDB's API.
`client.schema()` already returns the raw `/schema` document. The full approved
design is at `docs/2026-06-06_schema_drift_design.md`; this records the technical
decisions.

## Goals / Non-Goals

**Goals:**

- Detect actionable drift — model fields the live `/schema` no longer lists — and
  fail a CI check on it.
- Report informational drift — `/schema` fields the curated models omit — without
  failing.
- Keep all comparison logic pure and offline; do the single live call in a thin
  runner only.

**Non-Goals:**

- Generating model or field-spec source from `/schema`.
- Nested/dotted-path comparison or type-category comparison (name presence only).
- Covering `ulist` unless `/schema` documents it.
- Running the live check in the default `make test` suite.

## Decisions

- **Pure comparison + thin runner**, mirroring the sans-I/O core + thin-client
  split. `diff_schema` and the registry are import-and-test-friendly with no I/O;
  only `python -m vndb_client.schemacheck` touches the network.
- **Asymmetric drift semantics.** `missing_in_schema` (model has it, API lacks
  it) is actionable and fails the check, because requesting such a field is
  wrong. `missing_in_model` (API has it, model lacks it) is informational,
  because the client deliberately models a curated subset. Treating both as
  failures would make the check perpetually red and useless.
- **Top-level field names only.** Robust and tolerant of `/schema`'s nested
  structure; nested/type drift is explicitly deferred.
- **Isolate the shape dependency.** `parse_schema_field_names` is the only
  function coupled to the real `/schema` JSON layout; everything else operates on
  `dict[str, set[str]]`, so the unit tests need no live response.
- **Opt-in runner via `make schema-check`**, not a network-marked pytest test, so
  the default suite stays hermetic without pytest marker-deselection config.

## Risks / Trade-offs

- **`/schema` shape unknown at design time** → isolate it in
  `parse_schema_field_names`; the implementer fetches a real `/schema` and adapts
  only that function. If the shape cannot be parsed for a type, that type is
  reported as unresolved rather than silently passing.
- **Registry duplicates the client's endpoint→model knowledge** → accept a small
  explicit `ENTITY_MODELS` map in the new module; it is the natural home for the
  check and avoids importing client internals.
- **Live runner is not unit-tested against the real API** → that is the scheduled
  CI job's role; the pure functions carry the unit-test coverage.
