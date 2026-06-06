from __future__ import annotations

from vndb_client.entities.ulist import UlistEntry, UlistEntryLabel, UlistVN
from vndb_client.fields import field_spec

SAMPLE = {
    "id": "v17",
    "added": 1600000000,
    "voted": None,
    "lastmod": 1600000100,
    "vote": 85,
    "started": "2020-01-01",
    "finished": None,
    "notes": "great",
    "labels": [{"id": 1, "label": "Finished", "private": False}],
    "vn": {"id": "v17", "title": "Ever17"},
}


def test_ulist_entry_parses():
    e = UlistEntry.model_validate(SAMPLE)
    assert e.id == "v17"
    assert e.vote == 85
    assert e.voted is None
    assert isinstance(e.labels[0], UlistEntryLabel)
    assert e.labels[0].id == 1
    assert isinstance(e.vn, UlistVN)
    assert e.vn.title == "Ever17"


def test_ulist_entry_absent_fields_none():
    e = UlistEntry.model_validate({"id": "v1"})
    assert e.vote is None
    assert e.labels is None
    assert e.vn is None


def test_field_spec_includes_nested_excludes_releases():
    parts = field_spec(UlistEntry).split(",")
    assert "labels.id" in parts
    assert "vn.title" in parts
    assert "releases" not in parts
