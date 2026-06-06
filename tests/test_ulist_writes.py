from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.entities.ulist import RListStatus
from vndb_client.exceptions import VndbAuthError


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _capture():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content) if request.content else None
        return httpx.Response(204)

    return seen, handler


def test_set_ulist_partial_body():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        result = client.set_ulist("v17", vote=80, notes="x")
    assert result is None
    assert seen["method"] == "PATCH"
    assert seen["path"].endswith("/ulist/v17")
    assert seen["body"] == {"vote": 80, "notes": "x"}


def test_set_ulist_none_unsets():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17", vote=None)
    assert seen["body"] == {"vote": None}


def test_set_ulist_empty_body():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17")
    assert seen["body"] == {}


def test_set_ulist_labels_set():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_ulist("v17", labels_set=[1, 2])
    assert seen["body"] == {"labels_set": [1, 2]}


def test_delete_ulist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.delete_ulist("v17")
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/ulist/v17")


def test_set_rlist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.set_rlist("r5", status=2)
    assert seen["method"] == "PATCH"
    assert seen["path"].endswith("/rlist/r5")
    assert seen["body"] == {"status": 2}
    assert RListStatus.OBTAINED == 2


def test_delete_rlist():
    seen, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.delete_rlist("r5")
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/rlist/r5")


def test_write_auth_error():
    def handler(request):
        return httpx.Response(401, text="Invalid token")

    with Client(http_client=_client(handler)) as client, pytest.raises(VndbAuthError):
        client.delete_ulist("v17")


def test_async_set_ulist_and_delete():
    seen, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.set_ulist("v17", vote=90)
            await client.delete_rlist("r5")

    asyncio.run(scenario())
    assert seen["method"] == "DELETE"
    assert seen["path"].endswith("/rlist/r5")
