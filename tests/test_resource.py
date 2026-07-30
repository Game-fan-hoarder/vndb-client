from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from vndb_client.client import AsyncClient, Client
from vndb_client.config import PROD_BASE_URL
from vndb_client.entities.vn import VN
from vndb_client.exceptions import VndbServerError
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


def test_query_forwards_filter_echo_flags_and_compact_string():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters="compact-xyz", compact_filters=True, normalized_filters=True)
    assert captured["body"]["filters"] == "compact-xyz"
    assert captured["body"]["compact_filters"] is True
    assert captured["body"]["normalized_filters"] is True


def test_query_omits_filter_echo_flags_when_unset():
    captured, handler = _capture()
    with Client(http_client=_client(handler)) as client:
        client.vn.query()
    assert "compact_filters" not in captured["body"]
    assert "normalized_filters" not in captured["body"]


def test_async_query_forwards_filter_echo_flags_and_compact_string():
    captured, handler = _capture()

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            await client.vn.query(filters="compact-async", normalized_filters=True)

    asyncio.run(scenario())
    assert captured["body"]["filters"] == "compact-async"
    assert captured["body"]["normalized_filters"] is True
    assert "compact_filters" not in captured["body"]


def test_client_cache_ttl_serves_repeated_query_once():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json=VN_RESPONSE)

    with Client(http_client=_client(handler), cache_ttl=60.0) as client:
        client.vn.query(filters=["search", "=", "ever"])
        client.vn.query(filters=["search", "=", "ever"])
    assert calls["n"] == 1


def test_client_without_cache_queries_each_time():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, json=VN_RESPONSE)

    with Client(http_client=_client(handler)) as client:
        client.vn.query(filters=["search", "=", "ever"])
        client.vn.query(filters=["search", "=", "ever"])
    assert calls["n"] == 2


# --- pagination: pages() / iterate() ---


def _vns(start, n):
    return [{"id": f"v{i}", "title": f"T{i}"} for i in range(start, start + n)]


def _pager(page_map):
    """Serve a canned response per requested page, recording every request body.

    ``page_map`` maps a 1-based page number to a ``(results, more)`` pair, or to
    an ``httpx.Response`` to simulate a failure for that page.
    """
    seen: list[dict] = []

    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        spec = page_map[body["page"]]
        if isinstance(spec, httpx.Response):
            return spec
        results, more = spec
        return httpx.Response(200, json={"results": results, "more": more, "count": 250})

    return seen, handler


def test_iterate_streams_records_across_pages():
    seen, handler = _pager({1: (_vns(0, 2), True), 2: (_vns(2, 2), True), 3: (_vns(4, 1), False)})
    with Client(http_client=_client(handler)) as client:
        records = list(client.vn.iterate(filters=VF.rating >= 80))
    assert [r.id for r in records] == ["v0", "v1", "v2", "v3", "v4"]
    assert [body["page"] for body in seen] == [1, 2, 3]
    assert all(isinstance(r, VN) for r in records)


def test_pages_streams_envelopes():
    _, handler = _pager({1: (_vns(0, 2), True), 2: (_vns(2, 1), False)})
    with Client(http_client=_client(handler)) as client:
        pages = list(client.vn.pages(count=True))
    assert [len(p.results) for p in pages] == [2, 1]
    assert [p.more for p in pages] == [True, False]
    assert all(p.count == 250 for p in pages)
    assert all(isinstance(p, Page) for p in pages)


def test_pages_defaults_page_size_to_api_maximum():
    seen, handler = _pager({1: (_vns(0, 1), False)})
    with Client(http_client=_client(handler)) as client:
        list(client.vn.pages())
    assert seen[0]["results"] == 100


def test_pages_honours_caller_page_size():
    seen, handler = _pager({1: (_vns(0, 1), False)})
    with Client(http_client=_client(handler)) as client:
        list(client.vn.pages(results=25))
    assert seen[0]["results"] == 25


def test_pagination_methods_reject_page_parameter():
    with Client(http_client=_client(lambda r: httpx.Response(200, json=VN_RESPONSE))) as client:
        with pytest.raises(TypeError):
            client.vn.pages(page=2)
        with pytest.raises(TypeError):
            client.vn.iterate(page=2)


def test_pages_construction_issues_no_request():
    seen, handler = _pager({1: (_vns(0, 1), False)})
    with Client(http_client=_client(handler)) as client:
        gen = client.vn.pages()
        igen = client.vn.iterate()
        assert seen == []
        next(gen)
        next(igen)
    assert len(seen) == 2


def test_limit_truncates_final_page_to_exact_record_total():
    page_map = {1: (_vns(0, 100), True), 2: (_vns(100, 100), True), 3: (_vns(200, 100), True)}
    seen, handler = _pager(page_map)
    with Client(http_client=_client(handler)) as client:
        pages = list(client.vn.pages(limit=250))
    assert [len(p.results) for p in pages] == [100, 100, 50]
    assert sum(len(p.results) for p in pages) == 250
    assert [body["page"] for body in seen] == [1, 2, 3]


def test_limit_applies_identically_to_iterate():
    page_map = {1: (_vns(0, 100), True), 2: (_vns(100, 100), True), 3: (_vns(200, 100), True)}
    _, handler = _pager(page_map)
    with Client(http_client=_client(handler)) as client:
        records = list(client.vn.iterate(limit=250))
    assert len(records) == 250
    assert records[-1].id == "v249"


def test_truncated_page_preserves_api_more_flag():
    _, handler = _pager({1: (_vns(0, 10), True)})
    with Client(http_client=_client(handler)) as client:
        pages = list(client.vn.pages(limit=4))
    assert len(pages) == 1
    assert len(pages[0].results) == 4
    assert pages[0].more is True


def test_limit_stops_exactly_on_page_boundary():
    seen, handler = _pager({1: (_vns(0, 10), True), 2: (_vns(10, 10), True)})
    with Client(http_client=_client(handler)) as client:
        records = list(client.vn.iterate(results=10, limit=20))
    assert len(records) == 20
    assert [body["page"] for body in seen] == [1, 2]


def test_start_page_resumes_walk():
    seen, handler = _pager({137: (_vns(0, 3), False)})
    with Client(http_client=_client(handler)) as client:
        records = list(client.vn.iterate(start_page=137))
    assert len(records) == 3
    assert [body["page"] for body in seen] == [137]


def test_empty_page_claiming_more_stops_walk():
    seen, handler = _pager({1: ([], True)})
    with Client(http_client=_client(handler)) as client:
        pages = list(client.vn.pages())
    assert [len(p.results) for p in pages] == [0]
    assert len(seen) == 1


@pytest.mark.parametrize(("kwargs", "match"), [({"limit": 0}, "limit"), ({"start_page": 0}, "start_page")])
def test_invalid_bounds_raise_before_any_request(kwargs, match):
    seen, handler = _pager({1: (_vns(0, 1), False)})
    with Client(http_client=_client(handler)) as client:
        with pytest.raises(ValueError, match=match):
            client.vn.pages(**kwargs)
        with pytest.raises(ValueError, match=match):
            client.vn.iterate(**kwargs)
    assert seen == []


def test_request_failure_propagates_mid_walk():
    page_map = {
        1: (_vns(0, 2), True),
        2: (_vns(2, 2), True),
        3: httpx.Response(500, text="boom"),
    }
    _, handler = _pager(page_map)
    seen_records = []
    with Client(http_client=_client(handler)) as client, pytest.raises(VndbServerError):
        for record in client.vn.iterate():
            seen_records.append(record)
    assert [r.id for r in seen_records] == ["v0", "v1", "v2", "v3"]


# --- pagination: async mirrors ---


def test_async_iterate_streams_records_across_pages():
    seen, handler = _pager({1: (_vns(0, 2), True), 2: (_vns(2, 2), True), 3: (_vns(4, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [r async for r in client.vn.iterate(filters=VF.rating >= 80)]

    records = asyncio.run(scenario())
    assert [r.id for r in records] == ["v0", "v1", "v2", "v3", "v4"]
    assert [body["page"] for body in seen] == [1, 2, 3]
    assert all(isinstance(r, VN) for r in records)


def test_async_pages_streams_envelopes():
    _, handler = _pager({1: (_vns(0, 2), True), 2: (_vns(2, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages(count=True)]

    pages = asyncio.run(scenario())
    assert [len(p.results) for p in pages] == [2, 1]
    assert [p.more for p in pages] == [True, False]
    assert all(p.count == 250 for p in pages)


def test_async_pages_defaults_page_size_to_api_maximum():
    seen, handler = _pager({1: (_vns(0, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages()]

    asyncio.run(scenario())
    assert seen[0]["results"] == 100


def test_async_pages_honours_caller_page_size():
    seen, handler = _pager({1: (_vns(0, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages(results=25)]

    asyncio.run(scenario())
    assert seen[0]["results"] == 25


def test_async_pagination_methods_reject_page_parameter():
    async def scenario():
        async with AsyncClient(http_client=_aclient(lambda r: httpx.Response(200, json=VN_RESPONSE))) as client:
            with pytest.raises(TypeError):
                client.vn.pages(page=2)
            with pytest.raises(TypeError):
                client.vn.iterate(page=2)

    asyncio.run(scenario())


def test_async_pages_construction_issues_no_request():
    seen, handler = _pager({1: (_vns(0, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            gen = client.vn.pages()
            igen = client.vn.iterate()
            assert seen == []
            await gen.__anext__()
            await igen.__anext__()
            await gen.aclose()
            await igen.aclose()

    asyncio.run(scenario())
    assert len(seen) == 2


def test_async_limit_truncates_final_page_to_exact_record_total():
    page_map = {1: (_vns(0, 100), True), 2: (_vns(100, 100), True), 3: (_vns(200, 100), True)}
    seen, handler = _pager(page_map)

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages(limit=250)]

    pages = asyncio.run(scenario())
    assert [len(p.results) for p in pages] == [100, 100, 50]
    assert [body["page"] for body in seen] == [1, 2, 3]


def test_async_limit_applies_identically_to_iterate():
    page_map = {1: (_vns(0, 100), True), 2: (_vns(100, 100), True), 3: (_vns(200, 100), True)}
    _, handler = _pager(page_map)

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [r async for r in client.vn.iterate(limit=250)]

    records = asyncio.run(scenario())
    assert len(records) == 250
    assert records[-1].id == "v249"


def test_async_truncated_page_preserves_api_more_flag():
    _, handler = _pager({1: (_vns(0, 10), True)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages(limit=4)]

    pages = asyncio.run(scenario())
    assert len(pages) == 1
    assert len(pages[0].results) == 4
    assert pages[0].more is True


def test_async_start_page_resumes_walk():
    seen, handler = _pager({137: (_vns(0, 3), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [r async for r in client.vn.iterate(start_page=137)]

    records = asyncio.run(scenario())
    assert len(records) == 3
    assert [body["page"] for body in seen] == [137]


def test_async_empty_page_claiming_more_stops_walk():
    seen, handler = _pager({1: ([], True)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            return [p async for p in client.vn.pages()]

    pages = asyncio.run(scenario())
    assert [len(p.results) for p in pages] == [0]
    assert len(seen) == 1


@pytest.mark.parametrize(("kwargs", "match"), [({"limit": 0}, "limit"), ({"start_page": 0}, "start_page")])
def test_async_invalid_bounds_raise_before_any_request(kwargs, match):
    seen, handler = _pager({1: (_vns(0, 1), False)})

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            with pytest.raises(ValueError, match=match):
                client.vn.pages(**kwargs)
            with pytest.raises(ValueError, match=match):
                client.vn.iterate(**kwargs)

    asyncio.run(scenario())
    assert seen == []


def test_async_request_failure_propagates_mid_walk():
    page_map = {
        1: (_vns(0, 2), True),
        2: (_vns(2, 2), True),
        3: httpx.Response(500, text="boom"),
    }
    _, handler = _pager(page_map)
    seen_records = []

    async def scenario():
        async with AsyncClient(http_client=_aclient(handler)) as client:
            with pytest.raises(VndbServerError):
                async for record in client.vn.iterate():
                    seen_records.append(record)

    asyncio.run(scenario())
    assert [r.id for r in seen_records] == ["v0", "v1", "v2", "v3"]
