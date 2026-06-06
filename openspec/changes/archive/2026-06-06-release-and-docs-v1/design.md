## Context

`vndb-client` has a complete behavioral surface at 96% coverage with 147 passing
tests, but it is not publishable. This change is the V1 release-readiness cycle.
The full approved brainstorm design lives at
`docs/2026-06-06_release_and_docs_design.md`; this document records the technical
decisions.

Current state: README is cookiecutter boilerplate; docs are a badges-only
`index.md` plus a single monolithic `modules.md`; no CHANGELOG; `pyproject`
metadata is incomplete (`version = 0.0.1`, no `license` field, `keywords =
['python']`, no release classifiers). The release workflow
(`on-release-main.yml`) is tag-driven and already wired (sets version from tag,
`uv build` + `uv publish`, deploys Pages). `py.typed` already exists at
`src/vndb_client/py.typed`.

## Goals / Non-Goals

**Goals:**

- Documentation a new user can follow end to end: landing page, task guides, and
  a navigable split API reference that builds under `mkdocs build --strict`.
- A user-facing README that renders as the PyPI long-description.
- A `CHANGELOG.md` with a `1.0.0` entry.
- Packaging metadata correct for a stable public release (version, license,
  keywords, classifiers) with the typed marker shipping in the wheel.
- A coverage floor (`--cov-fail-under=90`) so coverage cannot silently regress.

**Non-Goals:**

- Performing the actual release: `git push`, tagging, `uv publish`, and Pages
  deploy are human actions (no remote on this branch).
- New runtime behavior or API surface. `src/vndb_client/**` is unchanged except
  docstring fixes a reference page might surface.
- The three stretch features (schema codegen, filter round-tripping, response
  caching) — deferred to separate post-V1 epics.
- Writing new tests to raise coverage: it is already 96%, so the gate only
  prevents regression.

## Decisions

- **Version `1.0.0`, not `0.1.0`.** The API is settled across the V1 feature set
  and we want semver guarantees from the first publish. The release workflow
  overwrites `pyproject` version from the git tag, so `1.0.0` here is the
  source-of-truth dev version; release-prep notes must instruct the human to tag
  `1.0.0`.
- **Guide set + split reference, not a single page.** A task-oriented guide set
  plus per-area reference pages is the standard shape for a public client
  library and scales as the API grows. Alternative (keep one `modules.md`) was
  rejected as too thin for a 1.0 release. The split is migration of existing
  `:::` mkdocstrings directives, not new autodoc config.
- **`mkdocs build --strict` is the docs gate.** It already runs in CI via
  `make docs-test`; a dead nav link or warning fails the build, which catches
  reference-split mistakes early.
- **Coverage gate at 90%, not 96%.** Pin to the epic's stated bar to leave
  headroom; pinning at the current 96% would make unrelated future changes
  brittle.
- **Review the release workflow, don't rewrite it.** It is already correct
  (tag-driven, token-based publish, Pages deploy). Only touch it if verification
  surfaces a concrete defect.

## Risks / Trade-offs

- **Reference split breaks `--strict` build** → wire every new page into
  `mkdocs.yml` nav and run `uv run mkdocs build --strict` before completing the
  docs task; remove `modules.md` only once its directives are migrated.
- **README renders poorly on PyPI** → keep it plain CommonMark (the existing
  badge/link style already renders); validate the built wheel's metadata.
- **`py.typed` missing from wheel** → hatchling includes package data by default;
  verify by inspecting the built wheel contents, not by assumption.
- **Version bump is cosmetic vs. the tag** → documented in release-prep notes so
  the human tags `1.0.0`; no automation change needed.
