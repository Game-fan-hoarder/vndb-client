from __future__ import annotations

import asyncio

import httpx
import pytest

from vndb_client import _transport
from vndb_client._transport import AsyncTransport, SyncTransport
from vndb_client.config import PROD_BASE_URL, RetryConfig
from vndb_client.core import RequestSpec
from vndb_client.exceptions import VndbNetworkError, VndbRateLimitError


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(_transport, "_sleep", lambda seconds: None)

    async def _anoop(seconds):
        return None

    monkeypatch.setattr(_transport, "_asleep", _anoop)


def _mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _mock_async_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


SPEC = RequestSpec(method="POST", path="/vn", json={"fields": "id"})


def test_sync_success_returns_response():
    def handler(request):
        return httpx.Response(200, json={"results": [], "more": False})

    transport = SyncTransport(http_client=_mock_client(handler))
    response = transport.send(SPEC)
    assert response.status_code == 200
    assert response.json() == {"results": [], "more": False}


def test_sync_sends_authorization_header_only_with_token():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={})

    SyncTransport(http_client=_mock_client(handler)).send(SPEC)
    assert seen["auth"] is None

    SyncTransport(token="tok", http_client=_mock_client(handler)).send(SPEC)
    assert seen["auth"] == "Token tok"


def test_sync_retries_429_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, text="slow down")
        return httpx.Response(200, json={"ok": True})

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=3))
    response = transport.send(SPEC)
    assert calls["n"] == 2
    assert response.json() == {"ok": True}


def test_sync_raises_after_exhausting_retries():
    def handler(request):
        return httpx.Response(429, text="slow down")

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=2))
    with pytest.raises(VndbRateLimitError) as info:
        transport.send(SPEC)
    assert info.value.status_code == 429


def test_sync_wraps_network_error():
    def handler(request):
        raise httpx.ConnectError("no route")

    transport = SyncTransport(http_client=_mock_client(handler), retry=RetryConfig(max_attempts=1))
    with pytest.raises(VndbNetworkError):
        transport.send(SPEC)


def test_sync_close_only_closes_owned_client():
    injected = _mock_client(lambda r: httpx.Response(200, json={}))
    transport = SyncTransport(http_client=injected)
    transport.close()
    assert injected.is_closed is False  # injected client left open


def _run(coro):
    return asyncio.run(coro)


def test_async_success_and_retry():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, text="slow")
        return httpx.Response(200, json={"ok": True})

    async def scenario():
        transport = AsyncTransport(http_client=_mock_async_client(handler), retry=RetryConfig(max_attempts=3))
        response = await transport.send(SPEC)
        await transport.aclose()
        return response

    response = _run(scenario())
    assert calls["n"] == 2
    assert response.json() == {"ok": True}


def test_async_wraps_network_error():
    def handler(request):
        raise httpx.ConnectError("down")

    async def scenario():
        transport = AsyncTransport(http_client=_mock_async_client(handler), retry=RetryConfig(max_attempts=1))
        try:
            await transport.send(SPEC)
        finally:
            await transport.aclose()

    with pytest.raises(VndbNetworkError):
        _run(scenario())


def test_async_close_only_closes_owned_client():
    async def scenario():
        injected = _mock_async_client(lambda r: httpx.Response(200, json={}))
        transport = AsyncTransport(http_client=injected)
        await transport.aclose()
        assert injected.is_closed is False  # injected client left open
        await injected.aclose()

    _run(scenario())


def test_async_raises_after_exhausting_retries():
    def handler(request):
        return httpx.Response(429, text="slow down")

    async def scenario():
        transport = AsyncTransport(http_client=_mock_async_client(handler), retry=RetryConfig(max_attempts=2))
        try:
            await transport.send(SPEC)
        finally:
            await transport.aclose()

    with pytest.raises(VndbRateLimitError) as info:
        _run(scenario())
    assert info.value.status_code == 429


# ---------------------------------------------------------------------------
# Bug 1: negative Retry-After must return None (not crash time.sleep)
# ---------------------------------------------------------------------------


def test_retry_after_negative_returns_none():
    response = httpx.Response(429, headers={"Retry-After": "-5"}, text="slow")
    assert _transport._retry_after(response) is None


def test_retry_after_positive_returns_float():
    response = httpx.Response(429, headers={"Retry-After": "5"}, text="slow")
    assert _transport._retry_after(response) == 5.0


def test_retry_after_missing_returns_none():
    response = httpx.Response(429, text="slow")
    assert _transport._retry_after(response) is None


def test_retry_after_zero_returns_zero():
    response = httpx.Response(429, headers={"Retry-After": "0"}, text="slow")
    assert _transport._retry_after(response) == 0.0


def _counting_handler():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json={"results": [], "more": False})

    return calls, handler


def test_cache_serves_repeated_read_once():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler), cache_ttl=60.0)
    t.send(SPEC)
    t.send(SPEC)
    assert calls["n"] == 1  # second read served from cache


def test_cache_disabled_hits_network_each_time():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler))  # no cache_ttl
    t.send(SPEC)
    t.send(SPEC)
    assert calls["n"] == 2


def test_cache_bypassed_for_writes():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler), cache_ttl=60.0)
    write = RequestSpec(method="PATCH", path="/ulist/v17", json={"vote": 90})
    t.send(write)
    t.send(write)
    assert calls["n"] == 2  # writes always hit the network


def test_async_cache_serves_repeated_read_once():
    calls, handler = _counting_handler()

    async def scenario():
        t = AsyncTransport(http_client=_mock_async_client(handler), cache_ttl=60.0)
        await t.send(SPEC)
        await t.send(SPEC)

    asyncio.run(scenario())
    assert calls["n"] == 1


def test_cache_ttl_zero_disables_caching():
    calls, handler = _counting_handler()
    t = SyncTransport(http_client=_mock_client(handler), cache_ttl=0.0)
    t.send(SPEC)
    t.send(SPEC)
    assert calls["n"] == 2  # non-positive ttl => caching disabled
