## ADDED Requirements

### Requirement: VndbModel parsing base

The library SHALL provide a `VndbModel` base class for all response models,
configured so that fields can be populated from the VNDB API's response keys via an
alias mapping while also supporting population by the Python field name.

#### Scenario: Populate from API keys

- **WHEN** a model deriving from `VndbModel` is parsed from a response dict using the
  API's key names
- **THEN** the corresponding snake_case Python fields are populated

#### Scenario: Populate by field name

- **WHEN** a model deriving from `VndbModel` is constructed using its Python field
  names
- **THEN** construction succeeds

### Requirement: Generic Page envelope

The library SHALL provide a generic `Page[T]` model representing the VNDB query
response envelope, exposing `results` as a list of `T`, a `more` flag, an optional
`count`, and the optional `compact_filters` and `normalized_filters` fields.

#### Scenario: Parse a populated page

- **WHEN** a response envelope with a non-empty `results` array and `more: true` is
  parsed as `Page[T]`
- **THEN** `results` contains instances of `T` and `more` is `True`

#### Scenario: Optional count present

- **WHEN** a response envelope includes a `count` value (requested via `count`)
- **THEN** the parsed `Page` exposes that count; otherwise `count` is `None`

### Requirement: Sans-I/O response parsing

The sans-I/O core SHALL parse a raw JSON response envelope into a `Page[T]` for a
given model type without performing any network I/O.

#### Scenario: Parse without I/O

- **WHEN** the core parse function is given a JSON envelope dict and a model type
- **THEN** it returns a `Page[T]` with parsed results and no network call occurs
