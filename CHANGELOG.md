# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-06

First stable release.

### Added

- Sans-I/O core with synchronous `Client` and asynchronous `AsyncClient`,
  sharing one request/transport layer.
- HTTP transport over `httpx` with configurable retries (`RetryConfig`),
  `Retry-After` handling, and a typed exception hierarchy (`VndbError` and
  subclasses).
- Typed query resources for `vn`, `release`, `producer`, `character`, `staff`,
  `tag`, `trait`, `quote`, and `ulist`, returning a typed `Page` envelope.
- Pydantic models for every supported entity, with field specs derived from the
  models.
- A composable filter DSL (`vn_filters`, `release_filters`, …) supporting
  comparisons and `&` / `|` composition, plus raw list filters.
- Simple GET endpoints: `stats`, `authinfo`, `get_user`, `ulist_labels`,
  `schema`.
- User-list read plus write operations: `set_ulist`, `delete_ulist`,
  `set_rlist`, `delete_rlist`, with an `UNSET` sentinel for omit-vs-null bodies.
- `py.typed` marker for downstream type checkers.

[1.0.0]: https://github.com/HOZHENWAI/vndb-client/releases/tag/1.0.0
