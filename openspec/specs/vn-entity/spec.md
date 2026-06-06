# vn-entity Specification

## Purpose
TBD - created by archiving change vn-flagship-entity. Update Purpose after archive.
## Requirements
### Requirement: VN model

The library SHALL provide a `VN` model deriving from `VndbModel` covering the VN
core scalar fields (`id`, `title`, `alttitle`, `olang`, `devstatus`, `released`,
`languages`, `platforms`, `length`, `length_minutes`, `length_votes`,
`description`, `rating`, `votecount`, `average`), the list fields `titles` and
`aliases`, and the nested `image`. It SHALL provide `Title` and `Image`
sub-models. Closed-set integer fields (`devstatus`, `length`) SHALL be typed as
`int | None`, with `DevStatus` and `VNLength` IntEnum constants provided as
comparison mirrors (not used as field types). `released` SHALL be typed as a
string.

#### Scenario: Parse a populated VN payload

- **WHEN** a realistic `/vn` response object is parsed into `VN`
- **THEN** scalar fields are populated, `image` is an `Image` instance, and
  `titles` items are `Title` instances

#### Scenario: Absent fields are None

- **WHEN** a VN payload omits fields that were not requested
- **THEN** those fields parse as `None` rather than raising

#### Scenario: Mirror constants compare to int fields

- **WHEN** a `VN` has `devstatus` equal to 0
- **THEN** comparing it to `DevStatus.FINISHED` is true (the field remains a plain int)

#### Scenario: Unknown closed-set value still parses

- **WHEN** a VN payload contains a `devstatus` or `length` value outside the known set
- **THEN** parsing succeeds and the field holds the raw integer

### Requirement: VN query surface

Both `Client` and `AsyncClient` SHALL expose a `vn` query resource such that
`Client().vn.query(...)` returns a `Page[VN]` and
`await AsyncClient().vn.query(...)` returns a `Page[VN]`. The `VN`, `Title`,
`Image`, `DevStatus`, and `VNLength` symbols SHALL be importable from the package
root.

#### Scenario: Sync VN query

- **WHEN** `Client().vn.query(...)` is called and a successful `/vn` response is returned
- **THEN** it returns a `Page[VN]` whose results are `VN` instances

#### Scenario: Async VN query

- **WHEN** `await AsyncClient().vn.query(...)` is called and a successful `/vn` response is returned
- **THEN** it returns a `Page[VN]` whose results are `VN` instances

#### Scenario: Public exports

- **WHEN** importing from the package root
- **THEN** `VN`, `Title`, `Image`, `DevStatus`, and `VNLength` are available

