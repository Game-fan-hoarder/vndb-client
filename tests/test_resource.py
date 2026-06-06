from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.entities.vn import VN
from vndb_client.fields import field_spec
from vndb_client.filters import vn_filters as VF
from vndb_client.models import Page
from vndb_client.resource import AsyncQueryResource, QueryResource

VN_RESPONSE = {"results": [{"id": "v17", "title": "Ever17"}], "more": False, "count": 1}


def _capture():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=VN_RESPONSE)

    return captured, handler


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def _aclient(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url=PROD_BASE_URL)


def test_vn_attr_is_query_resource():
    client = Client(http_client=_client(lambda r: httpx.Response(200, json=VN_RESPONSE)))
    assert isinstance(client.vn, QueryResource)


def test_query_defaults_fields_and_forwards_params():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        page = client.vn.query(filters=["search", "=", "ever"], results=5, count=True)
    assert captured["body"]["fields"] == field_spec(VN)
    assert captured["body"]["filters"] == ["search", "=", "ever"]
    assert captured["body"]["results"] == 5
    assert captured["body"]["count"] is True
    assert isinstance(page, Page)
    assert isinstance(page.results[0], VN)
    assert page.results[0].id == "v17"


def test_query_explicit_fields_override():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(fields="id,title")
    assert captured["body"]["fields"] == "id,title"


def test_query_forwards_sort_and_reverse():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(sort="rating", reverse=True)
    assert captured["body"]["sort"] == "rating"
    assert captured["body"]["reverse"] is True


def test_query_omits_unset_optional_params():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query()
    body = captured["body"]
    for absent in ("sort", "reverse", "results", "page", "count", "filters"):
        assert absent not in body


def test_async_vn_attr_and_query():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            assert isinstance(client.vn, AsyncQueryResource)
            return await client.vn.query(page=2)

    page = asyncio.run(scenario())
    assert isinstance(page.results[0], VN)
    assert captured["body"]["page"] == 2


_ENTITY_ATTRS = ["release", "producer", "character", "staff", "tag", "trait", "quote"]


@pytest.mark.parametrize("attr", _ENTITY_ATTRS)
def test_entity_attrs_are_query_resources(attr):
    sync = Client(http_client=_client(lambda r: httpx.Response(200, json={"results": [], "more": False})))
    assert isinstance(getattr(sync, attr), QueryResource)
    a = AsyncClient(http_client=_aclient(lambda r: httpx.Response(200, json={"results": [], "more": False})))
    assert isinstance(getattr(a, attr), AsyncQueryResource)


def test_quote_default_fields_include_nested_vn():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.quote.query()
    assert "vn.title" in captured["body"]["fields"].split(",")


def test_release_default_fields_include_nested_languages():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.release.query()
    assert "languages.lang" in captured["body"]["fields"].split(",")


def test_character_default_fields_exclude_relational_and_thumbnail():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.character.query()
    fields = captured["body"]["fields"].split(",")
    assert "vns" not in fields
    assert "traits" not in fields
    assert "image.thumbnail" not in fields


def test_query_serializes_predicate_filters():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=(VF.rating >= 80) & (VF.lang == "en"))
    assert captured["body"]["filters"] == ["and", ["rating", ">=", 80], ["lang", "=", "en"]]


def test_query_raw_list_filters_unchanged():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=["search", "=", "ever17"])
    assert captured["body"]["filters"] == ["search", "=", "ever17"]


def test_query_nested_relational_predicate():
    from vndb_client.filters import character_filters as CF

    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=VF.character == (CF.role == "main"))
    assert captured["body"]["filters"] == ["character", "=", ["role", "=", "main"]]


def test_async_query_serializes_predicate():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.vn.query(filters=VF.rating > 50)

    asyncio.run(scenario())
    assert captured["body"]["filters"] == ["rating", ">", 50]


def test_query_forwards_user_param():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(user="u2")
    assert captured["body"]["user"] == "u2"


def test_query_omits_user_when_absent():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query()
    assert "user" not in captured["body"]


def test_ulist_resource_query():
    import json

    from vndb_client.entities.ulist import UlistEntry
    from vndb_client.fields import field_spec

    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"id": "v17", "vote": 85}], "more": False})

    with Client(http_client=_client(handler)) as client:
        assert isinstance(client.ulist, QueryResource)
        page = client.ulist.query(user="u2")
    assert captured["body"]["user"] == "u2"
    assert captured["body"]["fields"] == field_spec(UlistEntry)
    assert page.results[0].id == "v17"
    assert isinstance(page.results[0], UlistEntry)


def test_async_ulist_resource():
    from vndb_client.entities.ulist import UlistEntry

    def handler(request):
        return httpx.Response(200, json={"results": [{"id": "v17"}], "more": False})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            assert isinstance(client.ulist, AsyncQueryResource)
            return await client.ulist.query(user="u2")

    page = asyncio.run(scenario())
    assert isinstance(page.results[0], UlistEntry)
