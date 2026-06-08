# query-builder Specification

## Purpose
TBD - created by archiving change query-builder. Update Purpose after archive.
## Requirements
### Requirement: Field comparison predicates

The library SHALL provide a `Field` type whose comparison operators build
predicates mapping to the VNDB filter operators: `==`→`"="`, `!=`→`"!="`,
`>=`→`">="`, `>`→`">"`, `<=`→`"<="`, `<`→`"<"`. A predicate SHALL serialize to a
`[name, op, value]` list. `Field` SHALL NOT be hashable (its `__eq__` is
overloaded for predicate construction).

#### Scenario: Each operator maps to its VNDB symbol

- **WHEN** a `Field("rating")` is compared with each of `==`, `!=`, `>=`, `>`, `<=`, `<`
- **THEN** the predicate serializes to `["rating", <symbol>, value]` with the matching symbol

#### Scenario: Field is not hashable

- **WHEN** a `Field` is used as a dict key or in a set
- **THEN** a `TypeError` is raised (hashing is disabled)

### Requirement: And/or composition

The library SHALL compose predicates with `&` (and) and `|` (or) into compound
predicates serializing to `["and", ...]` / `["or", ...]`. Chaining the same
operator SHALL flatten into a single compound rather than nesting pairwise.

#### Scenario: Combine with and

- **WHEN** two predicates are combined with `&`
- **THEN** the result serializes to `["and", <p1>, <p2>]`

#### Scenario: Same-operator chains flatten

- **WHEN** three predicates are combined as `a & b & c`
- **THEN** the result serializes to a single `["and", <a>, <b>, <c>]` (not nested pairs)

#### Scenario: Combine with or

- **WHEN** two predicates are combined with `|`
- **THEN** the result serializes to `["or", <p1>, <p2>]`

### Requirement: Nested relational filters

A predicate's value MAY itself be a predicate; serialization SHALL recurse so the
nested predicate's list form becomes the value. The builder SHALL NOT restrict
which fields accept nested values.

#### Scenario: Nested predicate value

- **WHEN** a comparison's value is another predicate (e.g. `character == (role == "main")`)
- **THEN** it serializes to `["character", "=", ["role", "=", "main"]]`

#### Scenario: Nested compound value

- **WHEN** a comparison's value is a compound predicate
- **THEN** it serializes with the nested `["and"|"or", ...]` as the value

#### Scenario: Scalar and list values pass through

- **WHEN** a comparison's value is a scalar or a list (e.g. a tag `[id, spoiler, level]`)
- **THEN** the value is used unchanged

### Requirement: Per-entity field namespaces and escape hatch

The library SHALL provide a filter namespace for each of the 8 query entities
(`vn_filters`, `release_filters`, `producer_filters`, `character_filters`,
`staff_filters`, `tag_filters`, `trait_filters`, `quote_filters`) exposing that
entity's documented filterable fields as `Field`s, and a generic `field(name)`
factory for arbitrary field names. These SHALL be importable from
`vndb_client.filters` along with `Predicate`.

#### Scenario: Namespace exposes documented fields

- **WHEN** accessing a documented field on a namespace (e.g. `vn_filters.rating`)
- **THEN** it is a `Field` whose name is that field's API name

#### Scenario: Generic escape hatch

- **WHEN** `field("some_new_filter")` is called and compared
- **THEN** it builds a predicate with that field name

#### Scenario: Public exports

- **WHEN** importing from `vndb_client.filters`
- **THEN** the 8 namespaces, `field`, and `Predicate` are available

### Requirement: Query integration with graceful degradation

`QueryResource.query` and `AsyncQueryResource.query` SHALL accept `filters` as a
`Predicate`, a raw list, or `None`. A `Predicate` SHALL be resolved to its list
form before the request is issued; a raw list SHALL be forwarded unchanged.

#### Scenario: Built predicate is serialized in the request

- **WHEN** `client.vn.query(filters=(vn_filters.rating >= 80) & (vn_filters.lang == "en"))` is issued
- **THEN** the request body `filters` is `["and", ["rating", ">=", 80], ["lang", "=", "en"]]`

#### Scenario: Raw list still works

- **WHEN** `client.vn.query(filters=["search", "=", "ever17"])` is issued
- **THEN** the request body `filters` is that list unchanged

#### Scenario: No filters

- **WHEN** `query()` is called without `filters`
- **THEN** no `filters` key is sent in the request body
