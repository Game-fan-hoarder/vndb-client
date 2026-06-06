## 1. Shared image sub-models (`entities/common.py`)

- [ ] 1.1 Write tests (`tests/test_common.py`): `ImageBase` parses an image dict without `thumbnail`; `Image` parses one with `thumbnail`/`thumbnail_dims`; `field_spec(Image)` contains `thumbnail` and `field_spec(ImageBase)` does not
- [ ] 1.2 Implement `src/vndb_client/entities/common.py`: `ImageBase(VndbModel)` (`id`,`url`,`dims`,`sexual`,`violence`,`votecount`) and `Image(ImageBase)` (+`thumbnail`,`thumbnail_dims`)
- [ ] 1.3 Edit `src/vndb_client/entities/vn.py` to import `Image` from `vndb_client.entities.common` (remove the local `Image`); confirm `tests/test_entities_vn.py` and `field_spec(VN)` (incl. `image.thumbnail`) still pass

## 2. Release model (`entities/release.py`)

- [ ] 2.1 Write tests (`tests/test_entities_release.py`): parse a realistic `/release` payload (scalars; `languages` → `ReleaseLang`, `media` → `ReleaseMedia`); `resolution` parses as `[w,h]`, as a string, and when absent (`None`)
- [ ] 2.2 Implement `src/vndb_client/entities/release.py`: `Release` (scalars per design incl. `resolution: list[int] | str | None`), `ReleaseLang`, `ReleaseMedia`

## 3. Producer model (`entities/producer.py`)

- [ ] 3.1 Write tests (`tests/test_entities_producer.py`): parse a `/producer` payload; `ProducerType.CO == producer.type` when type is "co"
- [ ] 3.2 Implement `src/vndb_client/entities/producer.py`: `Producer` (+ `ProducerType` IntEnum-style str mirror: `CO="co"`, `IN="in"`, `NG="ng"` — use `str, Enum`)

## 4. Character model (`entities/character.py`)

- [ ] 4.1 Write tests (`tests/test_entities_character.py`): parse a `/character` payload; `image` is `ImageBase`; `birthday`/`sex`/`gender` are lists; absent field → `None`
- [ ] 4.2 Implement `src/vndb_client/entities/character.py`: `Character` (scalars per design; `image: ImageBase | None`; `birthday: list[int] | None`; `sex`/`gender`: `list[str | None] | None`)

## 5. Staff model (`entities/staff.py`)

- [ ] 5.1 Write tests (`tests/test_entities_staff.py`): parse a `/staff` payload; `aliases` items are `StaffAlias`
- [ ] 5.2 Implement `src/vndb_client/entities/staff.py`: `Staff` + `StaffAlias` (`aid`,`name`,`latin`,`ismain`)

## 6. Tag model (`entities/tag.py`)

- [ ] 6.1 Write tests (`tests/test_entities_tag.py`): parse a `/tag` payload; `TagCategory.CONT == tag.category` when "cont"; `vn_count` int
- [ ] 6.2 Implement `src/vndb_client/entities/tag.py`: `Tag` (+ `TagCategory` str mirror: `CONT="cont"`, `ERO="ero"`, `TECH="tech"`)

## 7. Trait model (`entities/trait.py`)

- [ ] 7.1 Write tests (`tests/test_entities_trait.py`): parse a `/trait` payload incl. `group_id`/`group_name`/`char_count`
- [ ] 7.2 Implement `src/vndb_client/entities/trait.py`: `Trait`

## 8. Quote model (`entities/quote.py`)

- [ ] 8.1 Write tests (`tests/test_entities_quote.py`): parse a `/quote` payload; `vn` is `QuoteVN`, `character` is `QuoteCharacter`
- [ ] 8.2 Implement `src/vndb_client/entities/quote.py`: `Quote` + `QuoteVN`(`id`,`title`) + `QuoteCharacter`(`id`,`name`)

## 9. Wire client surfaces & public exports

- [ ] 9.1 Write tests (extend `tests/test_resource.py`): for each of the 7 entities, `Client().<attr>` is a `QueryResource` and `AsyncClient().<attr>` is an `AsyncQueryResource`; a representative `.query()` against a mock returns `Page[<Model>]`; assert the derived `fields` contains `quote.vn.title` and `release.languages.lang`, and `field_spec(Character)` excludes `vns`/`traits`
- [ ] 9.2 Write tests (extend `tests/test_public_api.py`): `Release`, `Producer`, `Character`, `Staff`, `Tag`, `Trait`, `Quote`, `ImageBase` are importable and in `__all__`
- [ ] 9.3 Edit `entities/__init__.py` to re-export all new symbols; edit `client.py` to wire `self.release`/`self.producer`/`self.character`/`self.staff`/`self.tag`/`self.trait`/`self.quote` on `Client` (QueryResource) and `AsyncClient` (AsyncQueryResource); edit `__init__.py` to export the new models + `ImageBase`

## 10. Docs & quality gate

- [ ] 10.1 Add `::: vndb_client.entities.common` and `::: vndb_client.entities.<name>` blocks for the 7 entities to `docs/modules.md`; verify `uv run mkdocs build --strict`
- [ ] 10.2 Run the full gate green: `uv run python -m pytest`, `uv run mypy`, `uv run ruff format`/`check`, `uv run deptry src`, and `tox` (py310–py314)
