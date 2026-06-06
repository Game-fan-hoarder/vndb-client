## Why

The library's behavioral surface (transport, entities, query builder, GET
endpoints, user lists) is complete and at 96% coverage, but it is not
publishable: the README is still cookiecutter boilerplate, the docs are a
badges-only landing page plus one monolithic API-reference page, there is no
CHANGELOG, and the packaging metadata (version, license, keywords, classifiers)
is incomplete. This change makes `vndb-client` release-ready as **v1.0.0** so a
maintainer can cut the release confidently.

## What Changes

- Add a task-oriented documentation guide set (`getting-started`,
  `authentication`, `querying`, `filtering`, `entities`, `user-lists`,
  `error-handling`) under `docs/guides/`.
- Split the monolithic `docs/modules.md` API reference into focused per-area
  pages under `docs/reference/` (client, models/resource, entities, filters,
  meta, config, exceptions), each carrying its mkdocstrings directives.
- Rewrite `index.md` into a real landing page and restructure `mkdocs.yml` nav
  into Home / Guides / API Reference; the site must build under
  `mkdocs build --strict`.
- Rewrite `README.md` from cookiecutter boilerplate into a user-facing document
  that also serves as the PyPI long-description.
- Add `CHANGELOG.md` (Keep a Changelog format) with a `1.0.0` entry covering the
  V1 feature set.
- Update packaging metadata in `pyproject.toml`: bump `version` to `1.0.0`, add
  a `license` field, real `keywords`, and release classifiers
  (`Development Status :: 5 - Production/Stable`,
  `License :: OSI Approved :: MIT License`, `Typing :: Typed`,
  `Topic :: Internet`).
- Add a `--cov-fail-under=90` coverage gate so coverage cannot regress below the
  V1 bar.
- Verify the release workflow and build artifacts: `uv build` produces a wheel
  containing `py.typed`, and `mkdocs build --strict` passes.

Out of scope (deferred to post-V1): the actual `git push` / tag / PyPI publish /
GitHub Pages deploy (no remote; human + credentials required), and the three
stretch features (schema-driven codegen, compact↔normalized filter
round-tripping, response caching).

## Capabilities

### New Capabilities

- `documentation`: the published documentation set — landing page, task-oriented
  guides, split API reference, and the strict-build requirement — plus the
  user-facing README and CHANGELOG.
- `release-packaging`: packaging and release-readiness — version `1.0.0`, license
  and discoverability metadata, release classifiers, the typed-marker shipping in
  the wheel, and the coverage-floor gate.

### Modified Capabilities

<!-- None. This change is additive (docs + packaging); no existing capability's
     spec-level requirements change. -->

## Impact

- **Docs:** `docs/index.md`, new `docs/guides/*.md`, new `docs/reference/*.md`,
  removal/replacement of `docs/modules.md`, `mkdocs.yml` nav.
- **Project root:** `README.md` (rewrite), `CHANGELOG.md` (new).
- **Packaging/CI:** `pyproject.toml` (`[project]` metadata + pytest
  `--cov-fail-under`); `.github/workflows/on-release-main.yml` reviewed (not
  modified unless a defect is found).
- **No source-code behavior changes**: `src/vndb_client/**` is unchanged except
  possibly docstrings if a reference page surfaces a gap.
