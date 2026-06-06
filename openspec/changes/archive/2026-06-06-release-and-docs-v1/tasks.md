## 1. Packaging metadata & coverage gate

- [x] 1.1 Bump `[project].version` to `1.0.0` in `pyproject.toml`
- [x] 1.2 Add `[project].license` (MIT) and replace placeholder `keywords` with domain keywords (vndb, visual-novel, api-client, httpx, pydantic, async)
- [x] 1.3 Add release classifiers: `Development Status :: 5 - Production/Stable`, `License :: OSI Approved :: MIT License`, `Typing :: Typed`, `Topic :: Internet`
- [x] 1.4 Add `--cov-fail-under=90` to pytest addopts (or `[tool.coverage]`/Makefile as appropriate) and confirm `make test` still passes at ~96%

## 2. README & CHANGELOG

- [x] 2.1 Rewrite `README.md`: intro, features, install (`pip install vndb-client`), quickstart (sync + async), authentication, docs link, license — remove cookiecutter scaffolding
- [x] 2.2 Create `CHANGELOG.md` (Keep a Changelog format) with a `1.0.0` entry documenting the V1 feature set

## 3. Documentation guides

- [x] 3.1 Rewrite `docs/index.md` as a real landing page (intro, install, quickstart, feature highlights, links)
- [x] 3.2 Add `docs/guides/getting-started.md` (install, first query, sync vs async)
- [x] 3.3 Add `docs/guides/authentication.md` (tokens, scopes, setting token on `Client`)
- [x] 3.4 Add `docs/guides/querying.md` (`query()`, fields, pagination, sorting)
- [x] 3.5 Add `docs/guides/filtering.md` (filter DSL: namespaces, predicates, `&`/`|`)
- [x] 3.6 Add `docs/guides/entities.md` (overview of entities and field models)
- [x] 3.7 Add `docs/guides/user-lists.md` (ulist read, `set_ulist`/`delete_ulist`, rlist, `UNSET`)
- [x] 3.8 Add `docs/guides/error-handling.md` (exception hierarchy, retries / `Retry-After`)

## 4. Split API reference

- [x] 4.1 Create `docs/reference/` pages migrating `:::` directives from `modules.md` (client, models/resource, entities, filters, meta, config, exceptions)
- [x] 4.2 Remove `docs/modules.md` once all directives are migrated
- [x] 4.3 Restructure `mkdocs.yml` nav into Home / Guides / API Reference (nested), wiring every new page

## 5. Verification

- [x] 5.1 Run `uv run mkdocs build --strict` and confirm exit 0 with no warnings
- [x] 5.2 Run `uv build`; list wheel contents and confirm `vndb_client/py.typed` is present and metadata is valid
- [x] 5.3 Review `.github/workflows/on-release-main.yml` for consistency with the 1.0.0 packaging (note: version is set from the git tag; human must tag `1.0.0`)
- [x] 5.4 Run `make check` (ruff, mypy, deptry) and `make test` — all clean
