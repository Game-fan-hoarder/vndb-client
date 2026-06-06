from __future__ import annotations

from vndb_client.entities.character import Character
from vndb_client.entities.common import ImageBase


def test_character_parses_scalars_and_image():
    c = Character.model_validate({
        "id": "c1",
        "name": "Tsugumi",
        "original": "つぐみ",
        "aliases": ["Tsu"],
        "description": "heroine",
        "blood_type": "a",
        "height": 160,
        "weight": None,
        "bust": None,
        "waist": None,
        "hips": None,
        "cup": None,
        "age": 17,
        "birthday": [6, 6],
        "sex": ["f", "f"],
        "gender": ["f", "f"],
        "image": {
            "id": "ch1",
            "url": "https://x/1.jpg",
            "dims": [256, 300],
            "sexual": 0.0,
            "violence": 0.0,
            "votecount": 3,
        },
    })
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
