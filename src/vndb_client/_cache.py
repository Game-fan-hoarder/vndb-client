from __future__ import annotations

import json
import time
from collections import OrderedDict
from collections.abc import Callable

import httpx

from vndb_client.core import RequestSpec

_CACHEABLE_METHODS = frozenset({"GET", "POST"})


def is_cacheable(spec: RequestSpec) -> bool:
    """True for read requests (GET/POST); False for writes (PATCH/DELETE)."""
    return spec.method in _CACHEABLE_METHODS


def cache_key(spec: RequestSpec) -> tuple[str, str, str, str]:
    """A stable cache key from the request's method, path, JSON body, and params."""
    return (
        spec.method,
        spec.path,
        json.dumps(spec.json, sort_keys=True),
        json.dumps(spec.params, sort_keys=True),
    )


class ResponseCache:
    """An in-memory, bounded (LRU) TTL cache of ``httpx.Response`` objects."""

    def __init__(self, ttl: float, maxsize: int = 128, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl
        self._maxsize = maxsize
        self._clock = clock
        self._store: OrderedDict[tuple[str, ...], tuple[float, httpx.Response]] = OrderedDict()

    def get(self, key: tuple[str, ...]) -> httpx.Response | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, response = entry
        if self._clock() >= expiry:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return response

    def set(self, key: tuple[str, ...], response: httpx.Response) -> None:
        self._store[key] = (self._clock() + self._ttl, response)
        self._store.move_to_end(key)
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)
