from __future__ import annotations

from vndb_client.meta import AuthInfo, Stats, UlistLabel, User


def test_stats_parses():
    s = Stats.model_validate({"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7})
    assert s.vn == 7
    assert s.chars == 1


def test_authinfo_parses():
    a = AuthInfo.model_validate({"id": "u1", "username": "Nemo", "permissions": ["listread", "listwrite"]})
    assert a.id == "u1"
    assert a.permissions == ["listread", "listwrite"]


def test_user_parses_and_optional_none():
    u = User.model_validate({"id": "u1", "username": "Nemo"})
    assert u.id == "u1"
    assert u.lengthvotes is None
    u2 = User.model_validate({"id": "u2", "username": "X", "lengthvotes": 10, "lengthvotes_sum": 200})
    assert u2.lengthvotes == 10
    assert u2.lengthvotes_sum == 200


def test_ulist_label_id_is_int():
    label = UlistLabel.model_validate({"id": 7, "label": "Wishlist", "private": False, "count": 42})
    assert label.id == 7
    assert isinstance(label.id, int)
    assert label.private is False
    assert label.count == 42
