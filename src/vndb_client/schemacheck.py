from __future__ import annotations

from typing import Any

from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait
from vndb_client.entities.vn import VN
from vndb_client.models import VndbModel

ENTITY_MODELS: dict[str, type[VndbModel]] = {
    "vn": VN,
    "release": Release,
    "producer": Producer,
    "character": Character,
    "staff": Staff,
    "tag": Tag,
    "trait": Trait,
    "quote": Quote,
}


def model_field_names(model: type[VndbModel]) -> set[str]:
    """Return the top-level request field names (alias or name) a model declares."""
    return {info.alias or name for name, info in model.model_fields.items()}


def parse_schema_field_names(raw_schema: dict[str, Any]) -> dict[str, set[str]]:
    """Extract ``{type_name: {field names}}`` from a raw ``/schema`` document.

    VNDB exposes selectable fields per type under the ``api_fields`` key. Each
    type maps to a container of field definitions: the top-level field names are
    the keys (object form) or each entry's ``name`` (list form). Keys beginning
    with ``_`` are treated as metadata and ignored.
    """
    api_fields = raw_schema.get("api_fields", {})
    result: dict[str, set[str]] = {}
    for type_name, fields_def in api_fields.items():
        if isinstance(fields_def, dict):
            result[type_name] = {key for key in fields_def if not key.startswith("_")}
        elif isinstance(fields_def, list):
            result[type_name] = {entry["name"] for entry in fields_def if isinstance(entry, dict) and "name" in entry}
        else:
            result[type_name] = set()
    return result
