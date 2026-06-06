## ADDED Requirements

### Requirement: GET request helper

The clients SHALL provide an internal GET helper that issues a GET request to a
given path with optional query parameters (omitting parameters whose value is
`None`), applying the transport's retry, error mapping, and auth header, and
returning the decoded JSON. A JSON decode failure SHALL raise `VndbParseError`.

#### Scenario: Optional params omitted

- **WHEN** the helper is called with a params mapping containing `None` values
- **THEN** those keys are absent from the issued request's query string

#### Scenario: Decode failure wrapped

- **WHEN** a GET response body is not valid JSON
- **THEN** a `VndbParseError` is raised

### Requirement: Stats endpoint

`Client` and `AsyncClient` SHALL provide a `stats()` method issuing `GET /stats`
and returning a `Stats` model with integer fields `chars`, `producers`,
`releases`, `staff`, `tags`, `traits`, `vn`.

#### Scenario: Fetch stats

- **WHEN** `stats()` is called and a successful response is returned
- **THEN** it GETs `/stats` and returns a `Stats` with the integer counts populated

### Requirement: Authinfo endpoint

`Client` and `AsyncClient` SHALL provide an `authinfo()` method issuing
`GET /authinfo` and returning an `AuthInfo` model (`id`, `username`,
`permissions`). The token, when configured, SHALL be sent.

#### Scenario: Fetch authinfo with token

- **WHEN** `authinfo()` is called on a client created with a token
- **THEN** the request includes `Authorization: Token <token>` and returns an `AuthInfo`

### Requirement: User lookup endpoint

`Client` and `AsyncClient` SHALL provide a `get_user(q, *, fields=None)` method
issuing `GET /user` where `q` is a single value or a list (sent as repeated `q`
parameters) and optional `fields`. It SHALL return a mapping from each `q` to a
`User` model or `None` (for unknown lookups).

#### Scenario: Lookup multiple users

- **WHEN** `get_user(["u1", "Nemo"], fields="lengthvotes")` is called
- **THEN** the request GETs `/user` with repeated `q` params and `fields`, and the
  result maps each `q` to a `User` (or `None` when the API returns `null`)

### Requirement: Ulist labels endpoint

`Client` and `AsyncClient` SHALL provide a `ulist_labels(user=None, *,
fields=None)` method issuing `GET /ulist_labels` and returning a list of
`UlistLabel` models unwrapped from the response's `labels` array. `UlistLabel.id`
SHALL be an integer.

#### Scenario: Fetch labels

- **WHEN** `ulist_labels(user="u1", fields="count")` is called
- **THEN** it GETs `/ulist_labels` and returns a `list[UlistLabel]` from the
  response's `labels` array, each with an integer `id`

### Requirement: Schema endpoint

`Client` and `AsyncClient` SHALL provide a `schema()` method issuing
`GET /schema` and returning the decoded JSON as a `dict` (no model).

#### Scenario: Fetch schema raw

- **WHEN** `schema()` is called and a successful response is returned
- **THEN** it GETs `/schema` and returns the decoded JSON object unchanged

### Requirement: Public exports

The `Stats`, `AuthInfo`, `User`, and `UlistLabel` models SHALL be importable from
the package root.

#### Scenario: Import meta models

- **WHEN** importing from `vndb_client`
- **THEN** `Stats`, `AuthInfo`, `User`, and `UlistLabel` are available
