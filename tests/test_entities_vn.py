from __future__ import annotations

from vndb_client.entities.vn import VN, DevStatus, Image, Title, VNLength

SAMPLE = {
    "id": "v17",
    "title": "Ever17",
    "alttitle": "Ever17 -The Out of Infinity-",
    "titles": [{"lang": "en", "title": "Ever17", "official": True, "main": True}],
    "aliases": ["E17"],
    "olang": "ja",
    "devstatus": 0,
    "released": "2002-08-29",
    "languages": ["ja", "en"],
    "platforms": ["win"],
    "image": {
        "id": "cv123",
        "url": "https://t.vndb.org/cv/123.jpg",
        "dims": [800, 600],
        "sexual": 0.0,
        "violence": 0.1,
        "votecount": 10,
        "thumbnail": "https://t.vndb.org/st/123.jpg",
        "thumbnail_dims": [256, 192],
    },
    "length": 3,
    "length_minutes": 3000,
    "length_votes": 5,
    "description": "A sci-fi mystery.",
    "rating": 85.0,
    "votecount": 1200,
    "average": 83.2,
}


def test_vn_parses_scalars_and_nested():
    vn = VN.model_validate(SAMPLE)
    assert vn.id == "v17"
    assert vn.rating == 85.0
    assert isinstance(vn.image, Image)
    assert vn.image.dims == [800, 600]
    assert vn.titles is not None
    assert isinstance(vn.titles[0], Title)
    assert vn.titles[0].lang == "en"


def test_vn_absent_fields_are_none():
    vn = VN.model_validate({"id": "v1"})
    assert vn.title is None
    assert vn.image is None
    assert vn.titles is None


def test_mirror_constants_compare_to_int_fields():
    vn = VN.model_validate({"id": "v1", "devstatus": 0, "length": 1})
    assert vn.devstatus == DevStatus.FINISHED
    assert vn.length == VNLength.VERY_SHORT


def test_unknown_closed_set_value_still_parses():
    vn = VN.model_validate({"id": "v1", "devstatus": 9, "length": 99})
    assert vn.devstatus == 9
    assert vn.length == 99
