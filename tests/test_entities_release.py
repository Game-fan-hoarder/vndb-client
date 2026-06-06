from __future__ import annotations

import pytest

from vndb_client.entities.release import Release, ReleaseLang, ReleaseMedia

SAMPLE = {
    "id": "r1",
    "title": "Ever17 (DVD)",
    "alttitle": None,
    "released": "2002-08-29",
    "platforms": ["win"],
    "minage": 0,
    "patch": False,
    "freeware": False,
    "uncensored": None,
    "official": True,
    "has_ero": False,
    "resolution": [800, 600],
    "engine": None,
    "voiced": 2,
    "notes": None,
    "gtin": None,
    "catalog": None,
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
