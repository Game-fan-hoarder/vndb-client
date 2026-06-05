from __future__ import annotations

from pydantic import Field

from vndb_client.models import Page, VndbModel


class _Dummy(VndbModel):
    id: str
    title: str | None = None
    dev_status: int | None = Field(default=None, alias="devstatus")


def test_vndbmodel_populates_from_api_alias():
    obj = _Dummy.model_validate({"id": "v17", "devstatus": 0})
    assert obj.id == "v17"
    assert obj.dev_status == 0


def test_vndbmodel_populates_by_field_name():
    obj = _Dummy(id="v17", dev_status=2)
    assert obj.dev_status == 2


def test_page_parses_results_more_and_count():
    page = Page[_Dummy].model_validate({"results": [{"id": "v1"}, {"id": "v2"}], "more": True, "count": 2})
    assert page.more is True
    assert page.count == 2
    assert [r.id for r in page.results] == ["v1", "v2"]
    assert all(isinstance(r, _Dummy) for r in page.results)


def test_page_count_defaults_to_none():
    page = Page[_Dummy].model_validate({"results": [], "more": False})
    assert page.count is None
    assert page.compact_filters is None
    assert page.normalized_filters is None
