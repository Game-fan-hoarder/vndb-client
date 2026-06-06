# user-lists Specification

## Purpose
TBD - created by archiving change user-lists. Update Purpose after archive.
## Requirements
### Requirement: Query resource user parameter

`QueryResource.query` and `AsyncQueryResource.query` SHALL accept an optional
`user` parameter, forwarded into the request body when provided and omitted when
`None`. Existing query usage SHALL be unaffected.

#### Scenario: User param forwarded

- **WHEN** `query(user="u2", ...)` is called
- **THEN** the issued request body includes `"user": "u2"`

#### Scenario: User param omitted by default

- **WHEN** `query(...)` is called without `user`
- **THEN** the request body has no `user` key

### Requirement: UlistEntry model

The library SHALL provide a `UlistEntry` model (`id` vn-id, `added`, `voted`,
`lastmod`, `vote`, `started`, `finished`, `notes`) with nested `labels`
(`UlistEntryLabel`: `id` int, `label`, `private`) and a minimal `vn` (`UlistVN`:
`id`, `title`). Relational `releases` are excluded.

#### Scenario: Parse a ulist entry

- **WHEN** a realistic `/ulist` entry is parsed into `UlistEntry`
- **THEN** scalars populate (with `None` where the API returns null), `labels`
  items are `UlistEntryLabel` (integer `id`), and `vn` is a `UlistVN`

### Requirement: Read a user's list

`Client` and `AsyncClient` SHALL expose `ulist` as a query resource such that
`client.ulist.query(user="u2", ...)` returns a `Page[UlistEntry]`.

#### Scenario: Query a user's list

- **WHEN** `client.ulist.query(user="u2")` is called and a successful response is returned
- **THEN** it POSTs to `/ulist` with `"user": "u2"` and returns a `Page[UlistEntry]`

### Requirement: Write helper and 204 handling

The clients SHALL provide an internal write helper that issues a request with a
given method, path, and optional JSON body, applying the transport's auth/retry/
error handling, and returning `None` on success (including `204 No Content`,
where no body is parsed).

#### Scenario: Successful write returns None

- **WHEN** a write helper call receives a `204` response
- **THEN** it returns `None` and does not attempt to decode a body

#### Scenario: Write error surfaces

- **WHEN** a write receives a `401` (missing/invalid `listwrite` token)
- **THEN** a `VndbAuthError` is raised

### Requirement: Modify ulist entries

`Client` and `AsyncClient` SHALL provide `set_ulist(vn_id, *, vote, notes,
started, finished, labels, labels_set, labels_unset)` issuing `PATCH
/ulist/<vn_id>`, and `delete_ulist(vn_id)` issuing `DELETE /ulist/<vn_id>`. The
nullable scalar fields SHALL use an `UNSET` sentinel so an omitted field is left
out of the body while an explicit `None` is sent as JSON `null` (unset). Label
list parameters SHALL be included only when not `None`.

#### Scenario: Partial update omits untouched fields

- **WHEN** `set_ulist("v17", vote=80, notes="x")` is called
- **THEN** the `PATCH /ulist/v17` body is `{"vote": 80, "notes": "x"}` (no `started`/`finished`/`labels` keys)

#### Scenario: Explicit None unsets

- **WHEN** `set_ulist("v17", vote=None)` is called
- **THEN** the body is `{"vote": null}` (the server unsets the vote)

#### Scenario: No fields yields empty body

- **WHEN** `set_ulist("v17")` is called with no field arguments
- **THEN** the body is `{}`

#### Scenario: Delete a ulist entry

- **WHEN** `delete_ulist("v17")` is called
- **THEN** it issues `DELETE /ulist/v17` and returns `None`

### Requirement: Modify rlist entries

`Client` and `AsyncClient` SHALL provide `set_rlist(release_id, *, status)`
issuing `PATCH /rlist/<release_id>` with body `{"status": status}`, and
`delete_rlist(release_id)` issuing `DELETE /rlist/<release_id>`. A `RListStatus`
IntEnum mirror SHALL be provided; `status` remains an `int`.

#### Scenario: Set release status

- **WHEN** `set_rlist("r5", status=2)` is called
- **THEN** the `PATCH /rlist/r5` body is `{"status": 2}` and `RListStatus.OBTAINED == 2`

#### Scenario: Delete an rlist entry

- **WHEN** `delete_rlist("r5")` is called
- **THEN** it issues `DELETE /rlist/r5` and returns `None`

### Requirement: Public exports

`UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, and `UNSET` SHALL be
importable from the package root.

#### Scenario: Import user-list symbols

- **WHEN** importing from `vndb_client`
- **THEN** `UlistEntry`, `UlistEntryLabel`, `UlistVN`, `RListStatus`, and `UNSET` are available

