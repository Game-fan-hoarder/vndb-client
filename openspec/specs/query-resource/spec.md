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

### Requirement: Auto-paginating query resource

The synchronous and asynchronous query resources SHALL each expose a `pages`
method yielding successive `Page` objects of the bound model for a query, and an
`iterate` method yielding the individual model records of that same walk. Both
SHALL accept the standard VNDB query parameters accepted by `query` except
`page`, and SHALL request each page lazily, so constructing the generator issues
no request. `iterate` SHALL be defined in terms of the same walk as `pages` and
SHALL NOT implement independent paging. When the caller does not specify a page
size, both methods SHALL request the API's maximum page size of 100 rather than
inheriting the API's default of 10. The asynchronous resource SHALL expose both
methods as asynchronous generators.

#### Scenario: Records streamed across pages

- **WHEN** `iterate()` is consumed for a query whose matches span three pages
- **THEN** it yields every record from all three pages in order, issuing one
  request per page with an incrementing 1-based page number

#### Scenario: Page envelopes streamed

- **WHEN** `pages()` is consumed for the same query
- **THEN** it yields one `Page` per request, each carrying the envelope fields
  (`results`, `more`, and `count` when requested)

#### Scenario: Generator construction issues no request

- **WHEN** `pages()` or `iterate()` is called but the returned generator is not
  yet iterated
- **THEN** no HTTP request has been issued

#### Scenario: Default page size is the API maximum

- **WHEN** either method is called without an explicit page size
- **THEN** each issued request asks for 100 results per page

#### Scenario: Caller-supplied page size honoured

- **WHEN** either method is called with an explicit page size below the maximum
- **THEN** each issued request asks for that number of results per page

#### Scenario: Paging is not caller-controllable

- **WHEN** a caller inspects the signature of `pages()` or `iterate()`
- **THEN** neither accepts a `page` parameter, so the page counter cannot be
  driven from outside the walk

#### Scenario: Async resources mirror both methods

- **WHEN** the asynchronous resource's `pages()` or `iterate()` is consumed with
  `async for`
- **THEN** it yields the same envelopes and records the synchronous resource would

### Requirement: Pagination record cap and resumption

Both pagination methods SHALL accept an optional record cap and an optional
starting page. The cap SHALL count model records rather than pages, and SHALL
apply identically to `pages` and `iterate`: when the cap falls inside a page, that
page's records SHALL be truncated so the total records emitted by the walk equals
the cap exactly. A truncated `Page` SHALL retain the `more` value the API
reported, because `more` describes whether the server holds further matches and
not whether iteration continued. The starting page SHALL default to the first
page and SHALL allow a walk to resume from a later page after a failure. An
invalid cap or starting page SHALL raise `ValueError` when the method is called,
not on first iteration.

#### Scenario: Cap truncates the final page

- **WHEN** `pages()` is consumed with a page size of 100 and a cap of 250
- **THEN** it yields pages of 100, 100, and 50 records, and issues no further
  requests

#### Scenario: Cap applies identically to record iteration

- **WHEN** `iterate()` is consumed with a cap of 250
- **THEN** exactly 250 records are yielded

#### Scenario: Truncated page preserves the API's more flag

- **WHEN** a page is truncated because the cap was reached and the API reported
  `more == true` for that page
- **THEN** the yielded `Page` still reports `more == true`

#### Scenario: Walk resumes from a later page

- **WHEN** either method is called with a starting page of 137
- **THEN** the first issued request asks for page 137 and the walk proceeds from
  there

#### Scenario: Invalid bounds rejected at call time

- **WHEN** either method is called with a cap of zero or below, or a starting
  page below one
- **THEN** it raises `ValueError` immediately, before any request is issued

### Requirement: Pagination termination

A pagination walk SHALL stop when the API reports no further pages, when the
record cap is exhausted, or when a page returns zero records while reporting that
further pages exist. The third condition SHALL prevent an unbounded request loop
when the API reports `more == true` for an empty page. Request failures SHALL
propagate to the caller unchanged rather than being swallowed or retried by the
walk beyond the transport's own retry policy.

#### Scenario: Terminates when no further pages

- **WHEN** a page reports `more == false`
- **THEN** the walk yields that page's records and issues no further request

#### Scenario: Terminates when the cap is exhausted

- **WHEN** the record cap is reached while the API still reports `more == true`
- **THEN** the walk stops and issues no further request

#### Scenario: Terminates on an empty page claiming more pages

- **WHEN** a page returns zero records but reports `more == true`
- **THEN** the walk stops instead of requesting further pages

#### Scenario: Request failure propagates mid-walk

- **WHEN** a request for the third page fails with a VNDB error after the
  transport's retries are exhausted
- **THEN** that error propagates to the caller, and the records already yielded
  from the first two pages remain valid
