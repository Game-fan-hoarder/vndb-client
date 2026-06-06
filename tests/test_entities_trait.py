from __future__ import annotations

from vndb_client.entities.trait import Trait


def test_trait_parses_scalars():
    t = Trait.model_validate({
        "id": "i1",
        "name": "Tsundere",
        "aliases": [],
        "description": "d",
        "searchable": True,
        "applicable": True,
        "sexual": False,
        "group_id": "i100",
        "group_name": "Personality",
        "char_count": 999,
    })
    assert t.id == "i1"
    assert t.group_id == "i100"
    assert t.group_name == "Personality"
    assert t.char_count == 999
