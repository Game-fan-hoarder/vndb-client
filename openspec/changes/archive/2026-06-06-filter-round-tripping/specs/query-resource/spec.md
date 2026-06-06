## MODIFIED Requirements

### Requirement: Generic query resource

The library SHALL provide a synchronous query resource and an asynchronous query
resource, each bound to a `(client, endpoint, model)` triple and exposing a
`query` method accepting the standard VNDB query parameters (`filters`, `fields`,
`sort`, `reverse`, `results`, `page`, `count`, `user`) plus the boolean
filter-echo request flags `compact_filters` and `normalized_filters`, and
returning a typed `Page` of the bound model. The `filters` parameter SHALL accept
a `Predicate`, a normalized filter `list`, a compact filter `str`, or `None`, so
a filter form returned on a previous `Page` can be fed back into a later query.
When `fields` is omitted, the resource SHALL request the model's full derived
field set; when provided, it SHALL use the caller's value. Each of the
`compact_filters` / `normalized_filters` flags SHALL be sent only when set; when
`True`, the response's matching `Page` field is populated.

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

#### Scenario: Filter-echo flags forwarded

- **WHEN** `query()` is called with `compact_filters=True` and/or
  `normalized_filters=True`
- **THEN** the issued request body includes those flags, and flags left unset are
  absent from the body

#### Scenario: Compact filter string fed back

- **WHEN** `query()` is called with `filters` set to a compact filter `str`
  (such as a previous `Page.compact_filters`)
- **THEN** that string is forwarded unchanged as the request's `filters`

#### Scenario: Async resource awaits

- **WHEN** the asynchronous resource's `query()` is awaited
- **THEN** it returns the same typed `Page` as the synchronous resource would
