## 1. Builder primitives (`filters/predicate.py`)

- [ ] 1.1 Write tests (`tests/test_filters_predicate.py`): each of `==`/`!=`/`>=`/`>`/`<=`/`<` on `Field("rating")` serializes to `["rating", <symbol>, value]`; `Field` is unhashable (`TypeError` in a set); `a & b` → `["and", a, b]`; `a | b` → `["or", a, b]`; `a & b & c` flattens to one `["and", a, b, c]`; a `Predicate` value serializes recursively (nested + nested-compound); scalar and list values pass through; `resolve_filters` returns `.to_filter()` for a `Predicate`, the value unchanged for a list/None
- [ ] 1.2 Implement `src/vndb_client/filters/predicate.py`: `Field` (operator dunders → `Comparison`; `__hash__ = None`), `Predicate` base (`to_filter`, `__and__`, `__or__`), `Comparison` (`[name, op, _serialize(value)]`, recursing on `Predicate` values), `Compound` (`["and"|"or", *children]`, flattening same-kind chains), `resolve_filters(filters)`

## 2. Per-entity namespaces (`filters/namespaces.py`)

- [ ] 2.1 Write tests (`tests/test_filters_namespaces.py`): each of the 8 namespaces exposes its documented fields as `Field`s with the correct `name` (spot-check several per entity, e.g. `vn_filters.rating.name == "rating"`, `character_filters.seiyuu`, `quote_filters.random`); `field("x")` returns a usable `Field`
- [ ] 2.2 Implement `src/vndb_client/filters/namespaces.py`: explicit namespace classes with class-attribute `Field`s for vn/release/producer/character/staff/tag/trait/quote (documented filterable fields per the design), module-level singletons `vn_filters` … `quote_filters`, and `field(name) -> Field`

## 3. Package exports (`filters/__init__.py`)

- [ ] 3.1 Write tests (extend `tests/test_public_api.py`): `from vndb_client.filters import vn_filters, release_filters, producer_filters, character_filters, staff_filters, tag_filters, trait_filters, quote_filters, field, Predicate` all succeed
- [ ] 3.2 Implement `src/vndb_client/filters/__init__.py` re-exporting the 8 namespaces, `field`, and `Predicate` with `__all__`

## 4. Query integration (`resource.py`)

- [ ] 4.1 Write tests (extend `tests/test_resource.py`, mocked transport): `client.vn.query(filters=(vn_filters.rating >= 80) & (vn_filters.lang == "en"))` puts `["and", ["rating", ">=", 80], ["lang", "=", "en"]]` in the request body; a raw-list `filters=["search","=","ever17"]` is forwarded unchanged; a nested relational predicate serializes correctly in the body; async equivalent via `asyncio.run`
- [ ] 4.2 Edit `src/vndb_client/resource.py`: widen the `filters` parameter type on `QueryResource.query` and `AsyncQueryResource.query` to `Predicate | list[Any] | None`; call `resolve_filters(filters)` before passing to `_query` (import from `vndb_client.filters.predicate`; keep `core` untouched)

## 5. Docs & quality gate

- [ ] 5.1 Add a filter-DSL usage snippet and `::: vndb_client.filters.predicate` + `::: vndb_client.filters.namespaces` reference blocks to `docs/modules.md`; verify `uv run mkdocs build --strict`
- [ ] 5.2 Run the full gate green: `uv run python -m pytest`, `uv run mypy`, `uv run ruff format`/`check`, `uv run deptry src`, and `tox` (py310–py314)
