# Entity Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 7 remaining VNDB query entities (release, producer, character, staff, tag, trait, quote) as typed models + `client.<entity>` surfaces, reusing the existing generic `QueryResource`.

**Architecture:** Shared image sub-models go in `entities/common.py` (`ImageBase`, `Image(ImageBase)`); `VN` imports `Image` from there. Each entity is a `VndbModel` (core scalars + key nested, relational deferred) wired as `QueryResource(self, "<endpoint>", Model)` on `Client`/`AsyncClient`. No transport/core/resource changes.

**Tech Stack:** Python 3.10–3.14, httpx, Pydantic v2, pytest (async via `asyncio.run`), uv, Ruff, mypy (strict).

**Spec:** `openspec/changes/entity-coverage/` (capability `entity-coverage`). **Design:** `docs/2026-06-06_entity_coverage_design.md`. **Reuses:** `VndbModel` (`models.py`), `field_spec` (`fields.py`), `QueryResource`/`AsyncQueryResource` (`resource.py`), the `client.vn` wiring pattern.

**Conventions for every commit:**
- Run from the worktree root `C:\Users\ml-na\PycharmProjects\personal\vndb-client\.worktrees\entity-coverage`; use `uv run ...`.
- Pre-commit hooks are NOT installed: before each commit run `uv run ruff format`, `uv run ruff check --fix`, `uv run ruff format --check`, `uv run mypy`, and re-stage.
- New modules start with `from __future__ import annotations`.
- End commit messages with: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
- Models inherit `VndbModel`; `id: str` is required (no default); all other fields default to `None`.

---

## Task 1: Shared image sub-models (`entities/common.py`) + VN import update

**Files:**
- Create: `src/vndb_client/entities/common.py`
- Modify: `src/vndb_client/entities/vn.py`
- Test: `tests/test_common.py`

- [ ] **Step 1: Write the failing test** `tests/test_common.py`:
```python
from __future__ import annotations

from vndb_client.entities.common import Image, ImageBase
from vndb_client.entities.vn import VN
from vndb_client.fields import field_spec


def test_imagebase_parses_without_thumbnail():
    img = ImageBase.model_validate(
        {"id": "ch1", "url": "https://x/1.jpg", "dims": [256, 300], "sexual": 0.0, "violence": 0.0, "votecount": 3}
    )
    assert img.id == "ch1"
    assert img.dims == [256, 300]


def test_image_parses_with_thumbnail():
    img = Image.model_validate({"id": "cv1", "url": "https://x/1.jpg", "thumbnail": "https://x/t.jpg", "thumbnail_dims": [128, 150]})
    assert img.thumbnail == "https://x/t.jpg"
    assert img.thumbnail_dims == [128, 150]


def test_field_spec_image_includes_thumbnail():
    assert "thumbnail" in field_spec(Image).split(",")


def test_field_spec_imagebase_excludes_thumbnail():
    assert "thumbnail" not in field_spec(ImageBase).split(",")


def test_vn_field_spec_includes_image_thumbnail():
    assert "image.thumbnail" in field_spec(VN).split(",")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_common.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vndb_client.entities.common'`.

- [ ] **Step 3: Create `src/vndb_client/entities/common.py`**
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class ImageBase(VndbModel):
    """Image fields common to all VNDB image objects."""

    id: str
    url: str | None = None
    dims: list[int] | None = None
    sexual: float | None = None
    violence: float | None = None
    votecount: int | None = None


class Image(ImageBase):
    """VN cover image (adds thumbnail fields not present on character images)."""

    thumbnail: str | None = None
    thumbnail_dims: list[int] | None = None
```

- [ ] **Step 4: Update `src/vndb_client/entities/vn.py`**

Remove the local `class Image(VndbModel): ...` definition and import it from `common` instead. The import block at the top becomes:
```python
from __future__ import annotations

from enum import IntEnum

from vndb_client.entities.common import Image
from vndb_client.models import VndbModel
```
Leave `DevStatus`, `VNLength`, `Title`, and `VN` unchanged (VN still references `Image` for its `image` field).

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_common.py tests/test_entities_vn.py tests/test_fields.py -v`
Expected: PASS (existing VN/fields tests still green; new common tests pass).

- [ ] **Step 6: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/common.py src/vndb_client/entities/vn.py tests/test_common.py
git commit -m "feat(entities): add shared ImageBase/Image in common; VN imports Image

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Release model (`entities/release.py`)

**Files:** Create `src/vndb_client/entities/release.py`; Test `tests/test_entities_release.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_release.py`:
```python
from __future__ import annotations

import pytest

from vndb_client.entities.release import Release, ReleaseLang, ReleaseMedia

SAMPLE = {
    "id": "r1", "title": "Ever17 (DVD)", "alttitle": None, "released": "2002-08-29",
    "platforms": ["win"], "minage": 0, "patch": False, "freeware": False,
    "uncensored": None, "official": True, "has_ero": False,
    "resolution": [800, 600], "engine": None, "voiced": 2, "notes": None,
    "gtin": None, "catalog": None,
    "languages": [{"lang": "ja", "title": "Ever17", "latin": None, "mtl": False, "main": True}],
    "media": [{"medium": "dvd", "qty": 1}],
}


def test_release_parses_scalars_and_nested():
    r = Release.model_validate(SAMPLE)
    assert r.id == "r1"
    assert r.official is True
    assert r.resolution == [800, 600]
    assert isinstance(r.languages[0], ReleaseLang)
    assert r.languages[0].lang == "ja"
    assert isinstance(r.media[0], ReleaseMedia)
    assert r.media[0].medium == "dvd"


@pytest.mark.parametrize("value", [[800, 600], "non-standard", None])
def test_release_resolution_polymorphic(value):
    r = Release.model_validate({"id": "r1", "resolution": value})
    assert r.resolution == value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_release.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/release.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class ReleaseLang(VndbModel):
    lang: str
    title: str | None = None
    latin: str | None = None
    mtl: bool | None = None
    main: bool | None = None


class ReleaseMedia(VndbModel):
    medium: str | None = None
    qty: int | None = None


class Release(VndbModel):
    id: str
    title: str | None = None
    alttitle: str | None = None
    released: str | None = None
    platforms: list[str] | None = None
    minage: int | None = None
    patch: bool | None = None
    freeware: bool | None = None
    uncensored: bool | None = None
    official: bool | None = None
    has_ero: bool | None = None
    resolution: list[int] | str | None = None
    engine: str | None = None
    voiced: int | None = None
    notes: str | None = None
    gtin: str | None = None
    catalog: str | None = None
    languages: list[ReleaseLang] | None = None
    media: list[ReleaseMedia] | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_release.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/release.py tests/test_entities_release.py
git commit -m "feat(entities): add Release model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Producer model (`entities/producer.py`)

**Files:** Create `src/vndb_client/entities/producer.py`; Test `tests/test_entities_producer.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_producer.py`:
```python
from __future__ import annotations

from vndb_client.entities.producer import Producer, ProducerType


def test_producer_parses_and_mirror_compares():
    p = Producer.model_validate(
        {"id": "p1", "name": "KID", "original": None, "aliases": ["Kid"], "lang": "ja", "type": "co", "description": None}
    )
    assert p.id == "p1"
    assert p.name == "KID"
    assert p.type == "co"
    assert ProducerType.CO == p.type
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_producer.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/producer.py`:
```python
from __future__ import annotations

from enum import Enum

from vndb_client.models import VndbModel


class ProducerType(str, Enum):
    """Mirror of VNDB producer ``type`` values (for comparison; not a field type)."""

    CO = "co"
    IN = "in"
    NG = "ng"


class Producer(VndbModel):
    id: str
    name: str | None = None
    original: str | None = None
    aliases: list[str] | None = None
    lang: str | None = None
    type: str | None = None
    description: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_producer.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/producer.py tests/test_entities_producer.py
git commit -m "feat(entities): add Producer model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Character model (`entities/character.py`)

**Files:** Create `src/vndb_client/entities/character.py`; Test `tests/test_entities_character.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_character.py`:
```python
from __future__ import annotations

from vndb_client.entities.character import Character
from vndb_client.entities.common import ImageBase


def test_character_parses_scalars_and_image():
    c = Character.model_validate(
        {
            "id": "c1", "name": "Tsugumi", "original": "つぐみ", "aliases": ["Tsu"],
            "description": "heroine", "blood_type": "a", "height": 160, "weight": None,
            "bust": None, "waist": None, "hips": None, "cup": None, "age": 17,
            "birthday": [6, 6], "sex": ["f", "f"], "gender": ["f", "f"],
            "image": {"id": "ch1", "url": "https://x/1.jpg", "dims": [256, 300], "sexual": 0.0, "violence": 0.0, "votecount": 3},
        }
    )
    assert c.id == "c1"
    assert c.height == 160
    assert c.birthday == [6, 6]
    assert c.sex == ["f", "f"]
    assert isinstance(c.image, ImageBase)
    assert c.image.dims == [256, 300]


def test_character_absent_fields_none():
    c = Character.model_validate({"id": "c1"})
    assert c.name is None
    assert c.image is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_character.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/character.py`:
```python
from __future__ import annotations

from vndb_client.entities.common import ImageBase
from vndb_client.models import VndbModel


class Character(VndbModel):
    id: str
    name: str | None = None
    original: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    blood_type: str | None = None
    height: int | None = None
    weight: int | None = None
    bust: int | None = None
    waist: int | None = None
    hips: int | None = None
    cup: str | None = None
    age: int | None = None
    birthday: list[int] | None = None
    sex: list[str | None] | None = None
    gender: list[str | None] | None = None
    image: ImageBase | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_character.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/character.py tests/test_entities_character.py
git commit -m "feat(entities): add Character model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Staff model (`entities/staff.py`)

**Files:** Create `src/vndb_client/entities/staff.py`; Test `tests/test_entities_staff.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_staff.py`:
```python
from __future__ import annotations

from vndb_client.entities.staff import Staff, StaffAlias


def test_staff_parses_scalars_and_aliases():
    s = Staff.model_validate(
        {
            "id": "s1", "aid": 10, "ismain": True, "name": "Author", "original": None,
            "lang": "ja", "gender": "f", "description": None,
            "aliases": [{"aid": 10, "name": "Author", "latin": None, "ismain": True}],
        }
    )
    assert s.id == "s1"
    assert s.aid == 10
    assert s.ismain is True
    assert isinstance(s.aliases[0], StaffAlias)
    assert s.aliases[0].aid == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_staff.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/staff.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class StaffAlias(VndbModel):
    aid: int | None = None
    name: str | None = None
    latin: str | None = None
    ismain: bool | None = None


class Staff(VndbModel):
    id: str
    aid: int | None = None
    ismain: bool | None = None
    name: str | None = None
    original: str | None = None
    lang: str | None = None
    gender: str | None = None
    description: str | None = None
    aliases: list[StaffAlias] | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_staff.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/staff.py tests/test_entities_staff.py
git commit -m "feat(entities): add Staff model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Tag model (`entities/tag.py`)

**Files:** Create `src/vndb_client/entities/tag.py`; Test `tests/test_entities_tag.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_tag.py`:
```python
from __future__ import annotations

from vndb_client.entities.tag import Tag, TagCategory


def test_tag_parses_and_mirror_compares():
    t = Tag.model_validate(
        {"id": "g1", "name": "Branching", "aliases": [], "description": "d", "category": "tech", "searchable": True, "applicable": True, "vn_count": 1234}
    )
    assert t.id == "g1"
    assert t.vn_count == 1234
    assert TagCategory.TECH == t.category
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_tag.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/tag.py`:
```python
from __future__ import annotations

from enum import Enum

from vndb_client.models import VndbModel


class TagCategory(str, Enum):
    """Mirror of VNDB tag ``category`` values (for comparison; not a field type)."""

    CONT = "cont"
    ERO = "ero"
    TECH = "tech"


class Tag(VndbModel):
    id: str
    name: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    category: str | None = None
    searchable: bool | None = None
    applicable: bool | None = None
    vn_count: int | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_tag.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/tag.py tests/test_entities_tag.py
git commit -m "feat(entities): add Tag model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Trait model (`entities/trait.py`)

**Files:** Create `src/vndb_client/entities/trait.py`; Test `tests/test_entities_trait.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_trait.py`:
```python
from __future__ import annotations

from vndb_client.entities.trait import Trait


def test_trait_parses_scalars():
    t = Trait.model_validate(
        {"id": "i1", "name": "Tsundere", "aliases": [], "description": "d", "searchable": True, "applicable": True, "sexual": False, "group_id": "i100", "group_name": "Personality", "char_count": 999}
    )
    assert t.id == "i1"
    assert t.group_id == "i100"
    assert t.group_name == "Personality"
    assert t.char_count == 999
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_trait.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/trait.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class Trait(VndbModel):
    id: str
    name: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    searchable: bool | None = None
    applicable: bool | None = None
    sexual: bool | None = None
    group_id: str | None = None
    group_name: str | None = None
    char_count: int | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_trait.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/trait.py tests/test_entities_trait.py
git commit -m "feat(entities): add Trait model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Quote model (`entities/quote.py`)

**Files:** Create `src/vndb_client/entities/quote.py`; Test `tests/test_entities_quote.py`.

- [ ] **Step 1: Write the failing test** `tests/test_entities_quote.py`:
```python
from __future__ import annotations

from vndb_client.entities.quote import Quote, QuoteCharacter, QuoteVN


def test_quote_parses_with_nested_refs():
    q = Quote.model_validate(
        {"id": "q1", "quote": "...", "score": 42, "vn": {"id": "v17", "title": "Ever17"}, "character": {"id": "c1", "name": "Tsugumi"}}
    )
    assert q.id == "q1"
    assert q.score == 42
    assert isinstance(q.vn, QuoteVN)
    assert q.vn.title == "Ever17"
    assert isinstance(q.character, QuoteCharacter)
    assert q.character.name == "Tsugumi"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_entities_quote.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement** `src/vndb_client/entities/quote.py`:
```python
from __future__ import annotations

from vndb_client.models import VndbModel


class QuoteVN(VndbModel):
    id: str
    title: str | None = None


class QuoteCharacter(VndbModel):
    id: str
    name: str | None = None


class Quote(VndbModel):
    id: str
    quote: str | None = None
    score: int | None = None
    vn: QuoteVN | None = None
    character: QuoteCharacter | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_entities_quote.py -v`
Expected: PASS.

- [ ] **Step 5: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/quote.py tests/test_entities_quote.py
git commit -m "feat(entities): add Quote model

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Wire client surfaces & public exports

**Files:**
- Modify: `src/vndb_client/entities/__init__.py`, `src/vndb_client/client.py`, `src/vndb_client/__init__.py`
- Test: `tests/test_resource.py` (extend), `tests/test_public_api.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_resource.py`:
```python
import pytest

from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait

_ENTITY_ATTRS = ["release", "producer", "character", "staff", "tag", "trait", "quote"]


@pytest.mark.parametrize("attr", _ENTITY_ATTRS)
def test_entity_attrs_are_query_resources(attr):
    sync = Client(http_client=_client(lambda r: httpx.Response(200, json={"results": [], "more": False})))
    assert isinstance(getattr(sync, attr), QueryResource)
    a = AsyncClient(http_client=_aclient(lambda r: httpx.Response(200, json={"results": [], "more": False})))
    assert isinstance(getattr(a, attr), AsyncQueryResource)


def test_quote_query_returns_typed_page_and_nested_fields():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.quote.query()
    fields = captured["body"]["fields"].split(",")
    assert "quote.vn.title" in fields or "vn.title" in fields  # quote nested ref


def test_release_default_fields_include_nested_languages():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.release.query()
    assert "languages.lang" in captured["body"]["fields"].split(",")


def test_character_default_fields_exclude_relational():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.character.query()
    fields = captured["body"]["fields"].split(",")
    assert "vns" not in fields
    assert "traits" not in fields
    assert "image.thumbnail" not in fields  # character image has no thumbnail
```
(Note: `field_spec(Quote)` yields `vn.title`/`vn.id`/`character.id`/`character.name` — the assertion accepts `vn.title`.)

Append to `tests/test_public_api.py`:
```python
def test_entity_coverage_exports_present():
    import vndb_client

    for name in ("Release", "Producer", "Character", "Staff", "Tag", "Trait", "Quote", "ImageBase"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_resource.py tests/test_public_api.py -v`
Expected: FAIL — entity attrs / exports missing.

- [ ] **Step 3: Update `src/vndb_client/entities/__init__.py`**

Replace its contents with:
```python
from __future__ import annotations

from vndb_client.entities.character import Character
from vndb_client.entities.common import Image, ImageBase
from vndb_client.entities.producer import Producer, ProducerType
from vndb_client.entities.quote import Quote, QuoteCharacter, QuoteVN
from vndb_client.entities.release import Release, ReleaseLang, ReleaseMedia
from vndb_client.entities.staff import Staff, StaffAlias
from vndb_client.entities.tag import Tag, TagCategory
from vndb_client.entities.trait import Trait
from vndb_client.entities.vn import VN, DevStatus, Title, VNLength

__all__ = [
    "VN",
    "Character",
    "DevStatus",
    "Image",
    "ImageBase",
    "Producer",
    "ProducerType",
    "Quote",
    "QuoteCharacter",
    "QuoteVN",
    "Release",
    "ReleaseLang",
    "ReleaseMedia",
    "Staff",
    "StaffAlias",
    "Tag",
    "TagCategory",
    "Title",
    "Trait",
    "VNLength",
]
```

- [ ] **Step 4: Wire the resources in `src/vndb_client/client.py`**

Update the entity import to bring in all 7 models (replace the `from vndb_client.entities.vn import VN` line):
```python
from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait
from vndb_client.entities.vn import VN
```
In `Client.__init__`, after the existing `self.vn = QueryResource(self, "vn", VN)` line, add:
```python
        self.release: QueryResource[Release] = QueryResource(self, "release", Release)
        self.producer: QueryResource[Producer] = QueryResource(self, "producer", Producer)
        self.character: QueryResource[Character] = QueryResource(self, "character", Character)
        self.staff: QueryResource[Staff] = QueryResource(self, "staff", Staff)
        self.tag: QueryResource[Tag] = QueryResource(self, "tag", Tag)
        self.trait: QueryResource[Trait] = QueryResource(self, "trait", Trait)
        self.quote: QueryResource[Quote] = QueryResource(self, "quote", Quote)
```
In `AsyncClient.__init__`, after the existing `self.vn = AsyncQueryResource(self, "vn", VN)` line, add the same seven with `AsyncQueryResource`:
```python
        self.release: AsyncQueryResource[Release] = AsyncQueryResource(self, "release", Release)
        self.producer: AsyncQueryResource[Producer] = AsyncQueryResource(self, "producer", Producer)
        self.character: AsyncQueryResource[Character] = AsyncQueryResource(self, "character", Character)
        self.staff: AsyncQueryResource[Staff] = AsyncQueryResource(self, "staff", Staff)
        self.tag: AsyncQueryResource[Tag] = AsyncQueryResource(self, "tag", Tag)
        self.trait: AsyncQueryResource[Trait] = AsyncQueryResource(self, "trait", Trait)
        self.quote: AsyncQueryResource[Quote] = AsyncQueryResource(self, "quote", Quote)
```

- [ ] **Step 5: Add exports to `src/vndb_client/__init__.py`**

Add the import (alongside the existing `from vndb_client.entities.vn import ...`); prefer importing the shared/new symbols from the entities package:
```python
from vndb_client.entities.common import ImageBase
from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait
```
Add `"Character"`, `"ImageBase"`, `"Producer"`, `"Quote"`, `"Release"`, `"Staff"`, `"Tag"`, `"Trait"` to `__all__` (run ruff to apply RUF022 ordering).

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_resource.py tests/test_public_api.py -v`
Expected: PASS.

- [ ] **Step 7: Format/type-check, then commit**
```bash
uv run ruff format && uv run ruff check --fix && uv run mypy
git add src/vndb_client/entities/__init__.py src/vndb_client/client.py src/vndb_client/__init__.py tests/test_resource.py tests/test_public_api.py
git commit -m "feat(entities): wire 7 entity query resources and export models

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Docs & quality gate

**Files:** Modify `docs/modules.md`.

- [ ] **Step 1: Add entity reference blocks**

Append to `docs/modules.md` (after the existing `::: vndb_client.entities.vn` block):
```markdown

::: vndb_client.entities.common

::: vndb_client.entities.release

::: vndb_client.entities.producer

::: vndb_client.entities.character

::: vndb_client.entities.staff

::: vndb_client.entities.tag

::: vndb_client.entities.trait

::: vndb_client.entities.quote
```

- [ ] **Step 2: Verify strict docs build**

Run: `uv run mkdocs build --strict`
Expected: builds successfully.

- [ ] **Step 3: Run the full quality gate**

Run, expecting all green:
```bash
uv run python -m pytest
uv run mypy
uv run ruff check
uv run ruff format --check
uv run deptry src
tox
```
Expected: pytest all pass; mypy clean; ruff clean; deptry clean; tox OK on py310–py314.

- [ ] **Step 4: Commit docs/any fixups**
```bash
git add docs/modules.md
git commit -m "docs(entities): add API reference blocks for the 7 entities + common

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```
(Skip if nothing remains to commit.)

---

## Self-Review

**Spec coverage:**

| Capability requirement | Task |
|---|---|
| Shared image sub-models (`ImageBase`/`Image`, char excludes thumbnail) | Task 1 + Task 9 char-fields test |
| Release model (+ ReleaseLang/Media, polymorphic resolution) | Task 2 |
| Producer model (+ ProducerType) | Task 3 |
| Character model (image=ImageBase) | Task 4 |
| Staff model (+ StaffAlias) | Task 5 |
| Tag model (+ TagCategory) | Task 6 |
| Trait model | Task 7 |
| Quote model (+ QuoteVN/QuoteCharacter) | Task 8 |
| Entity query surfaces (client.<entity> sync/async, derived fields, exports) | Task 9 |
| Docs reference | Task 10 |

No gaps.

**Placeholder scan:** No TBD/"handle edge cases"/"similar to Task N" — every model and test is written in full.

**Type consistency:** All models inherit `VndbModel`; sub-model names (`ReleaseLang`, `ReleaseMedia`, `StaffAlias`, `QuoteVN`, `QuoteCharacter`) and entity names match between their definition task, the wiring in Task 9, and the tests. `Character.image` and `Quote`/`Release` nested types align with `field_spec`'s dotted-path expansion. `Client`/`AsyncClient` attribute names match the endpoint strings and the `_ENTITY_ATTRS` test list. `ImageBase` is imported by `character.py` and `vn.py`'s `Image` (via `common`) consistently.
