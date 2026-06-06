from __future__ import annotations

import httpx

from vndb_client._cache import ResponseCache, cache_key, is_cacheable
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


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _resp(n: int) -> httpx.Response:
    return httpx.Response(200, json={"n": n})


def test_response_cache_hit_and_miss():
    clock = _FakeClock()
    cache = ResponseCache(ttl=10.0, clock=clock)
    assert cache.get(("k",)) is None  # miss on absent
    cache.set(("k",), _resp(1))
    assert cache.get(("k",)).json() == {"n": 1}  # hit


def test_response_cache_expires_after_ttl():
    clock = _FakeClock()
    cache = ResponseCache(ttl=10.0, clock=clock)
    cache.set(("k",), _resp(1))
    clock.now = 9.999
    assert cache.get(("k",)) is not None  # still fresh
    clock.now = 10.0
    assert cache.get(("k",)) is None  # expired at/after ttl


def test_response_cache_evicts_lru_beyond_maxsize():
    clock = _FakeClock()
    cache = ResponseCache(ttl=100.0, maxsize=2, clock=clock)
    cache.set(("a",), _resp(1))
    cache.set(("b",), _resp(2))
    cache.get(("a",))  # touch "a" so "b" is now least-recently-used
    cache.set(("c",), _resp(3))  # exceeds maxsize -> evict LRU ("b")
    assert cache.get(("b",)) is None
    assert cache.get(("a",)) is not None
    assert cache.get(("c",)) is not None
