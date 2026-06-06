## ADDED Requirements

### Requirement: Release version

The package version in `pyproject.toml` SHALL be `1.0.0`, marking the first
stable public release.

#### Scenario: Version reflects the stable release
- **WHEN** the packaging metadata is inspected
- **THEN** `[project].version` is `1.0.0`

### Requirement: License metadata

The packaging metadata SHALL declare the MIT license via a `[project].license`
field and the `License :: OSI Approved :: MIT License` classifier, consistent
with the repository `LICENSE` file.

#### Scenario: License is discoverable from metadata
- **WHEN** the built distribution metadata is read
- **THEN** it declares the MIT license through both the license field and the
  classifier

### Requirement: Discoverability metadata

The packaging metadata SHALL provide meaningful `keywords` (beyond the
placeholder `python`) and release classifiers including
`Development Status :: 5 - Production/Stable`, `Typing :: Typed`, and a relevant
topic classifier.

#### Scenario: Package is discoverable and described as stable
- **WHEN** the packaging metadata is inspected
- **THEN** keywords describe the project domain (e.g. vndb, visual-novel,
  api-client) and the classifiers mark the package as production-stable and typed

### Requirement: Typed marker ships in the wheel

The built wheel SHALL include the `py.typed` marker so downstream type checkers
recognise the package as typed.

#### Scenario: py.typed present in wheel
- **WHEN** `uv build` produces a wheel and its contents are listed
- **THEN** `vndb_client/py.typed` is present in the wheel

### Requirement: Coverage floor

The test configuration SHALL enforce a minimum coverage threshold of 90% via
`--cov-fail-under=90`, failing the test run if coverage drops below it.

#### Scenario: Coverage regression fails the build
- **WHEN** `make test` runs and total coverage is below 90%
- **THEN** the test run exits non-zero

#### Scenario: Current coverage passes the gate
- **WHEN** `make test` runs against the current code (coverage ~96%)
- **THEN** the coverage gate passes

### Requirement: Verified release workflow

The tag-driven release workflow (`.github/workflows/on-release-main.yml`) SHALL
be verified to build and publish the package and deploy the docs on a published
release. The build SHALL succeed locally via `uv build`.

#### Scenario: Build succeeds and workflow is sound
- **WHEN** `uv build` is run locally
- **THEN** it produces a valid sdist and wheel, and the release workflow's
  build/publish/deploy steps are confirmed consistent with this packaging
