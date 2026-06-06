from __future__ import annotations

from pydantic import Field as PydField

from vndb_client.entities.vn import VN
from vndb_client.models import VndbModel
from vndb_client.schemacheck import ENTITY_MODELS, model_field_names, parse_schema_field_names


def test_registry_covers_queryable_types():
    assert set(ENTITY_MODELS) == {
        "vn",
        "release",
        "producer",
        "character",
        "staff",
        "tag",
        "trait",
        "quote",
    }
    assert ENTITY_MODELS["vn"] is VN


def test_model_field_names_uses_alias_then_name():
    class M(VndbModel):
        id: str
        kind: str = PydField(default="x", alias="type")

    assert model_field_names(M) == {"id", "type"}


def test_parse_schema_field_names_object_form():
    raw = {"api_fields": {"vn": {"id": {}, "title": {}, "_meta": {}}}}
    assert parse_schema_field_names(raw)["vn"] == {"id", "title"}  # _meta ignored


def test_parse_schema_field_names_list_form():
    raw = {"api_fields": {"vn": [{"name": "id"}, {"name": "title"}]}}
    assert parse_schema_field_names(raw)["vn"] == {"id", "title"}


def test_parse_schema_field_names_missing_api_fields_is_empty():
    assert parse_schema_field_names({}) == {}
