from __future__ import annotations

from vndb_client.entities.tag import Tag, TagCategory


def test_tag_parses_and_mirror_compares():
    t = Tag.model_validate({
        "id": "g1",
        "name": "Branching",
        "aliases": [],
        "description": "d",
        "category": "tech",
        "searchable": True,
        "applicable": True,
        "vn_count": 1234,
    })
    assert t.id == "g1"
    assert t.vn_count == 1234
    assert t.category == TagCategory.TECH
