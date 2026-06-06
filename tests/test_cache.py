from __future__ import annotations

from vndb_client._cache import cache_key, is_cacheable
from vndb_client.core import RequestSpec


def test_is_cacheable_reads_true_writes_false():
    assert is_cacheable(RequestSpec(method="GET", path="/stats")) is True
    assert is_cacheable(RequestSpec(method="POST", path="/vn", json={"fields": "id"})) is True
    assert is_cacheable(RequestSpec(method="PATCH", path="/ulist/v17", json={"vote": 90})) is False
    assert is_cacheable(RequestSpec(method="DELETE", path="/ulist/v17")) is False


def test_cache_key_identical_for_identical_specs():
    a = RequestSpec(method="POST", path="/vn", json={"fields": "id", "filters": ["x"]})
    b = RequestSpec(method="POST", path="/vn", json={"filters": ["x"], "fields": "id"})
    assert cache_key(a) == cache_key(b)  # key order in json must not matter


def test_cache_key_differs_on_method_path_body_params():
    base = RequestSpec(method="POST", path="/vn", json={"fields": "id"})
    assert cache_key(base) != cache_key(RequestSpec(method="GET", path="/vn", json={"fields": "id"}))
    assert cache_key(base) != cache_key(RequestSpec(method="POST", path="/release", json={"fields": "id"}))
    assert cache_key(base) != cache_key(RequestSpec(method="POST", path="/vn", json={"fields": "id,title"}))
    assert cache_key(base) != cache_key(
        RequestSpec(method="POST", path="/vn", json={"fields": "id"}, params={"x": "1"})
    )
