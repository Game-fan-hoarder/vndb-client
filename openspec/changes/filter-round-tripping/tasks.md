## 1. Request flags in the core builder

- [ ] 1.1 Add `compact_filters: bool | None = None` and `normalized_filters: bool | None = None` params to `core.build_query_request`, each added to the body only when not `None`
- [ ] 1.2 Test (`tests/test_core.py`): flags included in the body when set; absent when `None`/omitted

## 2. Widen filters to accept a compact string

- [ ] 2.1 Widen `resolve_filters` signature to `Predicate | list[Any] | str | None` (pass-through unchanged)
- [ ] 2.2 Test (`tests/test_filters_predicate.py`): a `str` passes through `resolve_filters` unchanged

## 3. Thread through the query resources

- [ ] 3.1 Add `compact_filters`/`normalized_filters` params and widen `filters` to `Predicate | list[Any] | str | None` on `QueryResource.query` and `AsyncQueryResource.query`, forwarding all to `_query`; update docstrings to note these are request flags
- [ ] 3.2 Test (`tests/test_resource.py`): sync + async `query()` with a compact-string `filters` and the two flags set produces a request spec body containing the string and the flags (fake-transport / spec-capture pattern)

## 4. Docs

- [ ] 4.1 Add a round-trip example to `docs/guides/filtering.md` (request the forms via the flags, reuse `page.compact_filters` / `page.normalized_filters` as `filters` in a later query)

## 5. Verification

- [ ] 5.1 `make check` (ruff, mypy, deptry) clean and `make test` passes with the coverage gate satisfied
- [ ] 5.2 `uv run mkdocs build --strict` exit 0
