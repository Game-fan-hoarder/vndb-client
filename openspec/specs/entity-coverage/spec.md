# entity-coverage Specification

## Purpose
TBD - created by archiving change entity-coverage. Update Purpose after archive.
## Requirements
### Requirement: Shared image sub-models

The library SHALL provide `ImageBase` (fields `id`, `url`, `dims`, `sexual`,
`violence`, `votecount`) and `Image(ImageBase)` (adding `thumbnail`,
`thumbnail_dims`) in a shared module, so that endpoints whose image object omits
`thumbnail` (e.g. `/character`) request only supported fields while `/vn`
requests the full image. The `VN` model SHALL use `Image`; `Character` SHALL use
`ImageBase`. The public `Image` export SHALL remain available.

#### Scenario: Character image excludes thumbnail

- **WHEN** the request fields are derived for the `Character` model
- **THEN** they include `image.id`/`image.url` but NOT `image.thumbnail`

#### Scenario: VN image includes thumbnail

- **WHEN** the request fields are derived for the `VN` model
- **THEN** they include `image.thumbnail`

#### Scenario: Image export stable

- **WHEN** importing `Image` from the package root
- **THEN** it resolves to the full image model (with `thumbnail`)

### Requirement: Release model

The library SHALL provide a `Release` model (core scalars incl. `id`, `title`,
`alttitle`, `released`, `platforms`, `minage`, `patch`, `freeware`,
`uncensored`, `official`, `has_ero`, `resolution`, `engine`, `voiced`, `notes`,
`gtin`, `catalog`) with nested `languages` (`ReleaseLang`) and `media`
(`ReleaseMedia`); relational arrays are excluded. `resolution` SHALL accept
`null`, a string, or a `[w, h]` list.

#### Scenario: Parse a release payload

- **WHEN** a realistic `/release` object is parsed into `Release`
- **THEN** scalars populate, `languages` items are `ReleaseLang`, `media` items are `ReleaseMedia`

#### Scenario: Polymorphic resolution

- **WHEN** `resolution` is a `[w, h]` list, a string, or absent
- **THEN** parsing succeeds in each case

### Requirement: Producer model

The library SHALL provide a `Producer` model (`id`, `name`, `original`,
`aliases`, `lang`, `type`, `description`) with a `ProducerType` mirror constant
(`co`/`in`/`ng`); `type` remains a string field.

#### Scenario: Parse a producer payload

- **WHEN** a realistic `/producer` object is parsed into `Producer`
- **THEN** scalars populate and `ProducerType.CO == producer.type` holds when type is "co"

### Requirement: Character model

The library SHALL provide a `Character` model (`id`, `name`, `original`,
`aliases`, `description`, `blood_type`, `height`, `weight`, `bust`, `waist`,
`hips`, `cup`, `age`, `birthday`, `sex`, `gender`) with `image` typed as
`ImageBase`; relational arrays (`vns`, `traits`) are excluded.

#### Scenario: Parse a character payload

- **WHEN** a realistic `/character` object is parsed into `Character`
- **THEN** scalars populate and `image` is an `ImageBase` instance

### Requirement: Staff model

The library SHALL provide a `Staff` model (`id`, `aid`, `ismain`, `name`,
`original`, `lang`, `gender`, `description`) with nested `aliases` (`StaffAlias`
objects: `aid`, `name`, `latin`, `ismain`); `extlinks` is excluded.

#### Scenario: Parse a staff payload

- **WHEN** a realistic `/staff` object is parsed into `Staff`
- **THEN** scalars populate and `aliases` items are `StaffAlias` instances

### Requirement: Tag model

The library SHALL provide a `Tag` model (`id`, `name`, `aliases`, `description`,
`category`, `searchable`, `applicable`, `vn_count`) with a `TagCategory` mirror
constant (`cont`/`ero`/`tech`); `category` remains a string field.

#### Scenario: Parse a tag payload

- **WHEN** a realistic `/tag` object is parsed into `Tag`
- **THEN** scalars populate and `vn_count` is an integer

### Requirement: Trait model

The library SHALL provide a `Trait` model (`id`, `name`, `aliases`,
`description`, `searchable`, `applicable`, `sexual`, `group_id`, `group_name`,
`char_count`).

#### Scenario: Parse a trait payload

- **WHEN** a realistic `/trait` object is parsed into `Trait`
- **THEN** scalars populate including `group_id`/`group_name`

### Requirement: Quote model

The library SHALL provide a `Quote` model (`id`, `quote`, `score`) with nested
minimal references `vn` (`QuoteVN`: `id`, `title`) and `character`
(`QuoteCharacter`: `id`, `name`).

#### Scenario: Parse a quote payload

- **WHEN** a realistic `/quote` object is parsed into `Quote`
- **THEN** `quote`/`score` populate, `vn` is a `QuoteVN`, and `character` is a `QuoteCharacter`

### Requirement: Entity query surfaces

Both `Client` and `AsyncClient` SHALL expose `release`, `producer`, `character`,
`staff`, `tag`, `trait`, and `quote` query resources, each returning a `Page` of
its model, defaulting `fields` to the model's derived set. All new models and
`ImageBase` SHALL be importable from the package root.

#### Scenario: Sync entity query

- **WHEN** `Client().<entity>.query(...)` is called for any of the 7 entities and a successful response is returned
- **THEN** it returns a `Page` whose results are instances of that entity's model

#### Scenario: Async entity query

- **WHEN** `await AsyncClient().<entity>.query(...)` is called for any of the 7 entities
- **THEN** it returns a `Page` whose results are instances of that entity's model

#### Scenario: Derived fields exclude deferred relations

- **WHEN** the default `fields` are derived for `Character`
- **THEN** they exclude relational arrays such as `vns` and `traits`

#### Scenario: Public exports

- **WHEN** importing from the package root
- **THEN** `Release`, `Producer`, `Character`, `Staff`, `Tag`, `Trait`, `Quote`, and `ImageBase` are available
