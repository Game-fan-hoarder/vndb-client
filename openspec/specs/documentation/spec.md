# documentation Specification

## Purpose
TBD - created by archiving change release-and-docs-v1. Update Purpose after archive.
## Requirements
### Requirement: Landing page

The documentation site SHALL present a landing page (`docs/index.md`) that
introduces the library, shows installation and a minimal quickstart, highlights
the main features, and links to the guides and API reference. It SHALL NOT be a
badges-only stub.

#### Scenario: Landing page orients a new user
- **WHEN** a new user opens the documentation home page
- **THEN** they see what the library does, how to install it, a runnable
  quickstart example, and links into the guides and API reference

### Requirement: Task-oriented guide set

The documentation SHALL include task-oriented guide pages under `docs/guides/`
covering getting started, authentication, querying, filtering, entities, user
lists, and error handling. Each guide SHALL contain at least one runnable code
example.

#### Scenario: Guides cover the core workflows
- **WHEN** the docs are built
- **THEN** guide pages exist for getting-started, authentication, querying,
  filtering, entities, user-lists, and error-handling, each reachable from the
  site navigation

#### Scenario: Guide examples are runnable
- **WHEN** a reader copies a code example from any guide
- **THEN** the example uses the public `vndb_client` API as documented and is
  syntactically valid Python

### Requirement: Split API reference

The API reference SHALL be split into focused per-area pages under
`docs/reference/` (client, models/resource, entities, filters, meta, config,
exceptions), each rendering its members via mkdocstrings `:::` directives. The
monolithic `docs/modules.md` SHALL be removed once its directives are migrated.

#### Scenario: Reference is navigable by area
- **WHEN** the docs are built
- **THEN** each public area (client, models/resource, entities, filters, meta,
  config, exceptions) has its own reference page reachable from the navigation,
  and `docs/modules.md` no longer exists

### Requirement: Strict documentation build

The documentation site SHALL build successfully under
`mkdocs build --strict` (no warnings, no dead navigation links).

#### Scenario: Strict build succeeds
- **WHEN** `uv run mkdocs build --strict` is run
- **THEN** the build completes with exit code 0 and no warnings

### Requirement: User-facing README

`README.md` SHALL be a user-facing document — intro, features, install,
quickstart (synchronous and asynchronous), authentication, docs link, and
license — suitable for use as the PyPI long-description. It SHALL NOT contain
cookiecutter scaffolding instructions.

#### Scenario: README serves end users
- **WHEN** a prospective user reads the README on the repository or PyPI
- **THEN** they can install the library and run a first query without reading
  project-scaffolding instructions

### Requirement: Changelog

The project SHALL maintain a `CHANGELOG.md` in Keep a Changelog format with a
`1.0.0` entry documenting the V1 feature set.

#### Scenario: Changelog records the 1.0.0 release
- **WHEN** a reader opens `CHANGELOG.md`
- **THEN** a `1.0.0` section lists the V1 capabilities (transport, entities,
  query builder / filter DSL, GET endpoints, user-list read and write)
