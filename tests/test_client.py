from __future__ import annotations

import asyncio

import httpx

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.models import Page, VndbModel


class _VN(VndbModel):
    id: str


def _handler(request):
    return httpx.Response(200, json={"results": [{"id": "v1"}], "more": False, "count": 1})


def _mock_client():
    return httpx.Client(transport=httpx.MockTransport(_handler), base_url=PROD_BASE_URL)


def _mock_async_client():
    return httpx.AsyncClient(transport=httpx.MockTransport(_handler), base_url=PROD_BASE_URL)


def test_sync_query_returns_typed_page():
    with Client(http_client=_mock_client()) as client:
        page = client._query("vn", _VN, fields="id", count=True)
    assert isinstance(page, Page)
    assert page.count == 1
    assert page.results[0].id == "v1"
    assert isinstance(page.results[0], _VN)


def test_sync_context_manager_closes_owned_client():
    client = Client()  # builds its own httpx client
    with client:
        pass
    assert client._transport._client.is_closed is True


def test_async_query_returns_typed_page():
    async def scenario():
        async with AsyncClient(http_client=_mock_async_client()) as client:
            return await client._query("vn", _VN, fields="id")

    page = asyncio.run(scenario())
    assert page.results[0].id == "v1"
    assert isinstance(page.results[0], _VN)
