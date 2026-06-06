from __future__ import annotations

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
