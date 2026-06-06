from __future__ import annotations

import asyncio

import httpx

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.meta import AuthInfo, Stats, UlistLabel, User


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def test_stats():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(
            200, json={"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7}
        )

    with Client(http_client=_client(handler)) as client:
        result = client.stats()
    assert seen["method"] == "GET"
    assert seen["path"].endswith("/stats")
    assert isinstance(result, Stats)
    assert result.vn == 7


def test_authinfo_sends_token():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id": "u1", "username": "Nemo", "permissions": ["listread"]})

    with Client(token="tok", http_client=_client(handler)) as client:
        result = client.authinfo()
    assert seen["path"].endswith("/authinfo")
    assert seen["auth"] == "Token tok"
    assert isinstance(result, AuthInfo)
    assert result.permissions == ["listread"]


def test_get_user_multiple_and_null():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["q"] = request.url.params.get_list("q")
        seen["fields"] = request.url.params.get("fields")
        return httpx.Response(200, json={"u1": {"id": "u1", "username": "Nemo", "lengthvotes": 5}, "Ghost": None})

    with Client(http_client=_client(handler)) as client:
        result = client.get_user(["u1", "Ghost"], fields="lengthvotes")
    assert seen["path"].endswith("/user")
    assert seen["q"] == ["u1", "Ghost"]
    assert seen["fields"] == "lengthvotes"
    assert isinstance(result["u1"], User)
    assert result["u1"].lengthvotes == 5
    assert result["Ghost"] is None


def test_ulist_labels_unwraps_list():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["user"] = request.url.params.get("user")
        return httpx.Response(
            200,
            json={
                "labels": [
                    {"id": 1, "label": "Playing", "private": False},
                    {"id": 2, "label": "Wishlist", "private": True},
                ]
            },
        )

    with Client(http_client=_client(handler)) as client:
        result = client.ulist_labels(user="u1", fields="count")
    assert seen["path"].endswith("/ulist_labels")
    assert seen["user"] == "u1"
    assert [label.id for label in result] == [1, 2]
    assert all(isinstance(label, UlistLabel) for label in result)


def test_ulist_labels_omits_none_params():
    seen = {}

    def handler(request):
        seen["query"] = str(request.url.query)
        return httpx.Response(200, json={"labels": []})

    with Client(http_client=_client(handler)) as client:
        client.ulist_labels()
    assert "user" not in seen["query"]
    assert "fields" not in seen["query"]


def test_schema_returns_raw_dict():
    def handler(request):
        return httpx.Response(200, json={"api_fields": {"vn": ["id", "title"]}, "enums": {}})

    with Client(http_client=_client(handler)) as client:
        result = client.schema()
    assert result == {"api_fields": {"vn": ["id", "title"]}, "enums": {}}


def test_async_stats_and_get_user():
    def handler(request):
        if request.url.path.endswith("/stats"):
            return httpx.Response(
                200, json={"chars": 1, "producers": 2, "releases": 3, "staff": 4, "tags": 5, "traits": 6, "vn": 7}
            )
        return httpx.Response(200, json={"u1": {"id": "u1", "username": "Nemo"}})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return await client.stats(), await client.get_user("u1")

    stats, users = asyncio.run(scenario())
    assert isinstance(stats, Stats)
    assert isinstance(users["u1"], User)


def test_malformed_response_raises_vndb_parse_error():
    import pytest

    from vndb_client.exceptions import VndbParseError

    def handler(request):  # /stats missing required int counts
        return httpx.Response(200, json={"chars": "not-an-int"})

    with Client(http_client=_client(handler)) as client, pytest.raises(VndbParseError):
        client.stats()


def test_ulist_labels_missing_key_raises_parse_error():
    import pytest

    from vndb_client.exceptions import VndbParseError

    def handler(request):
        return httpx.Response(200, json={"unexpected": []})

    with Client(http_client=_client(handler)) as client, pytest.raises(VndbParseError):
        client.ulist_labels()


def test_get_user_non_dict_raises_parse_error():
    import pytest

    from vndb_client.exceptions import VndbParseError

    def handler(request):
        return httpx.Response(200, json=["not", "a", "map"])

    with Client(http_client=_client(handler)) as client, pytest.raises(VndbParseError):
        client.get_user("u1")
