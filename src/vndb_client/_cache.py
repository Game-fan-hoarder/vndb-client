from __future__ import annotations

import json

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
