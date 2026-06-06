from __future__ import annotations

from vndb_client.entities.staff import Staff, StaffAlias


def test_staff_parses_scalars_and_aliases():
    s = Staff.model_validate({
        "id": "s1",
        "aid": 10,
        "ismain": True,
        "name": "Author",
        "original": None,
        "lang": "ja",
        "gender": "f",
        "description": None,
        "aliases": [{"aid": 10, "name": "Author", "latin": None, "ismain": True}],
    })
    assert s.id == "s1"
    assert s.aid == 10
    assert s.ismain is True
    assert isinstance(s.aliases[0], StaffAlias)
    assert s.aliases[0].aid == 10
