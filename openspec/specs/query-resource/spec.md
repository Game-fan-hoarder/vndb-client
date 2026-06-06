# query-resource Specification

## Purpose
TBD - created by archiving change vn-flagship-entity. Update Purpose after archive.
## Requirements
### Requirement: Model-to-fields derivation

The library SHALL derive the VNDB `fields` request string from a `VndbModel`
subclass by reflecting over its declared fields, emitting each field's API alias
(or its name when no alias is set), and recursing into nested `VndbModel`
sub-models using dotted paths. List-of-scalar fields SHALL emit a bare name;
list-of-sub-model and single-sub-model fields SHALL emit dotted paths.

#### Scenario: Flat model fields

- **WHEN** the derivation runs on a model whose fields are all scalars (some with
  aliases differing from the Python name)
- **THEN** it returns a comma-separated string of the API alias-or-name for each field

#### Scenario: Nested sub-model fields

- **WHEN** a model has a field whose type is a nested `VndbModel` (e.g. an `image`
  object) or a list of `VndbModel`
- **THEN** the derived string contains dotted paths for each nested field
  (e.g. `image.id`, `image.url`; `titles.lang`, `titles.title`)

#### Scenario: List-of-scalar field

- **WHEN** a model has a field that is a list of scalars (e.g. `aliases`)
- **THEN** the derived string contains the bare field name, not a dotted path

### Requirement: Generic query resource

The library SHALL provide a synchronous query resource and an asynchronous query
resource, each bound to a `(client, endpoint, model)` triple and exposing a
`query` method accepting the standard VNDB query parameters (`filters`, `fields`,
`sort`, `reverse`, `results`, `page`, `count`) and returning a typed `Page` of
the bound model. When `fields` is omitted, the resource SHALL request the model's
full derived field set; when provided, it SHALL use the caller's value.

#### Scenario: Default fields requested

- **WHEN** `query()` is called without a `fields` argument
- **THEN** the issued request's `fields` equals the model's derived field set

#### Scenario: Explicit fields override

- **WHEN** `query()` is called with an explicit `fields` value
- **THEN** the issued request uses that value instead of the derived set

#### Scenario: Parameters forwarded and typed page returned

- **WHEN** `query()` is called with `filters`, `results`, `page`, and `count`
- **THEN** those parameters are forwarded to the underlying query and the result
  is a `Page` whose `results` are instances of the bound model

#### Scenario: Async resource awaits

- **WHEN** the asynchronous resource's `query()` is awaited
- **THEN** it returns the same typed `Page` as the synchronous resource

