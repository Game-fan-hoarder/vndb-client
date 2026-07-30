# Release & docs (V1) — Design

**Status:** Approved 2026-06-06
**Beads epic:** `vndb-client-6lp`

## Goal

Make `vndb-client` release-ready as **v1.0.0**: real user-facing documentation
(a task-oriented guide set plus a split API reference), a rewritten README, a
CHANGELOG, verified release workflow and packaging metadata, and a coverage
floor — **without** performing the actual publish. This branch has no remote, so
`git push` / tag / PyPI publish / GitHub Pages deploy are human actions performed
later; this cycle delivers everything needed for the human to cut the release
confidently.

## Context (current state)

- **Coverage is already 96%** (TOTAL), past the epic's "90%+" goal. Lowest module
  is `client.py` at 84%; all 147 tests pass. "Reach 90%+ coverage" is effectively
  already met — this cycle adds a *gate*, not new tests.
- **README is still cookiecutter boilerplate** ("Create a New Repository",
  "Getting started with your project") — a real gap for a public release.
- **Docs** are a badges-only `index.md` plus one monolithic `modules.md` API
  reference page. Nav has only Home + Modules.
- **`py.typed` is present** at `src/vndb_client/py.typed` ✓ (confirm it ships in
  the wheel).
- **Release workflow** (`.github/workflows/on-release-main.yml`) is tag-driven:
  `set-version` rewrites the `pyproject` version *from the git tag*, then
  `uv build` + `uv publish` (via the `PYPI_TOKEN` secret), then deploys docs to
  GitHub Pages. The published version is whatever tag the human pushes; the
  `1.0.0` bump is the source-of-truth dev version.
- **LICENSE** is MIT, but `[project]` has no `license` field and no MIT
  classifier; `keywords = ['python']` is a discoverability gap.

## Scope decisions

- **Version:** target **1.0.0** (stable public API with semver from the start).
- **Stretch goals deferred:** schema-driven codegen from `/schema`,
  compact↔normalized filter round-tripping, and response caching are each
  substantial features warranting their own brainstorm→spec→plan cycle. File as
  separate post-V1 work; not in this cycle.
- **Docs scope:** full guide set **and** split API reference (richest option).

## Components

### 1. Release metadata — `pyproject.toml` + `LICENSE`

- Bump `version = "1.0.0"`.
- Add a `license` field (`"MIT"`) and real `keywords`
  (`vndb`, `visual-novel`, `api-client`, `httpx`, `pydantic`, `async`).
- Add classifiers: `Development Status :: 5 - Production/Stable`,
  `License :: OSI Approved :: MIT License`, `Typing :: Typed`,
  `Topic :: Internet`.
- Add a `--cov-fail-under=90` gate to pytest addopts so coverage cannot regress
  below the V1 bar (currently 96%).

### 2. `README.md` (full rewrite)

Replace cookiecutter boilerplate with a user-facing README — badges,
one-paragraph intro, Features, Install (`pip install vndb-client`), Quickstart
(sync **and** async), Authentication (token), link to full docs, License. Doubles
as the PyPI long-description, so it must render cleanly as Markdown on PyPI.

### 3. `CHANGELOG.md` (new)

Keep-a-Changelog format. `## [1.0.0] - 2026-06-06` documenting the V1 feature
set: transport core, VN + entity coverage, query builder / filter DSL, simple
GET endpoints, user-list read + write.

### 4. Docs — guide set + split API reference

- **`index.md`**: real landing page (intro, install, quickstart, feature
  highlights, links) — replaces the badges-only stub.
- **Guides** (`docs/guides/`):
  - `getting-started.md` — install, first query, sync vs async.
  - `authentication.md` — tokens, scopes, setting the token on `Client`.
  - `querying.md` — `query()`, fields, pagination (`results`/`more`/`count`),
    sorting.
  - `filtering.md` — filter DSL: namespaces, predicates, `&`/`|` operators.
  - `entities.md` — overview of available entities and their field models.
  - `user-lists.md` — ulist read, `set_ulist`/`delete_ulist`, rlist, the `UNSET`
    sentinel.
  - `error-handling.md` — exception hierarchy, retries / `Retry-After`.
- **API reference split** (`docs/reference/`): break the monolithic `modules.md`
  into focused pages — client, models/resource, entities, filters, meta (GET
  endpoints), config, exceptions — each carrying its `:::` mkdocstrings
  directives migrated from the current `modules.md`.
- **`mkdocs.yml` nav**: restructure into Home / Guides (nested) / API Reference
  (nested). Keep the `mkdocstrings` plugin. Must pass `mkdocs build --strict`
  (the `make docs-test` CI gate).

### 5. Testing / verification

- `make check` (ruff, mypy, deptry) clean.
- `make test` passes with the new `--cov-fail-under=90` (96% today).
- `uv run mkdocs build --strict` succeeds — no broken nav links or warnings.
- `uv build` produces sdist + wheel; confirm the wheel contains `py.typed` and
  the metadata / long-description is valid.
- **No forced test-writing**: coverage already clears the bar, so per YAGNI we do
  not pad `client.py` (84%) unless something drops total below 90% (it does not).

## Out of scope (deferred to post-V1)

- Actual `git push` / tag / PyPI publish / Pages deploy (needs remote + human
  credentials).
- The three stretch features (schema codegen, filter round-tripping, response
  caching) → separate post-V1 epics.

## Risk notes

- The release workflow overwrites the `pyproject` version from the git tag, so
  the CHANGELOG / release-prep notes must tell the human to tag `1.0.0`.
- `mkdocs --strict` fails on any dead nav link, so the reference split must be
  wired carefully and verified with a strict build.
