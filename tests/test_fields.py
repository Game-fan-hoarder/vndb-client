from __future__ import annotations

import pytest
from pydantic import Field

from vndb_client.fields import field_spec
from vndb_client.models import VndbModel


class _Sub(VndbModel):
    a: str
    b: int | None = None


class _Empty(VndbModel):
    pass


class _M(VndbModel):
    id: str
    dev_status: int | None = Field(default=None, alias="devstatus")
    tags: list[str] | None = None
    sub: _Sub | None = None
    subs: list[_Sub] | None = None


def test_empty_model_raises():
    with pytest.raises(ValueError, match="no fields"):
        field_spec(_Empty)


def test_flat_fields_use_alias_or_name():
    parts = field_spec(_M).split(",")
    assert "id" in parts
    assert "devstatus" in parts
    assert "dev_status" not in parts


def test_list_of_scalar_is_bare():
    assert "tags" in field_spec(_M).split(",")


def test_single_submodel_is_dotted():
    parts = field_spec(_M).split(",")
    assert "sub.a" in parts
    assert "sub.b" in parts
    assert "sub" not in parts


def test_list_of_submodel_is_dotted():
    parts = field_spec(_M).split(",")
    assert "subs.a" in parts
    assert "subs.b" in parts
