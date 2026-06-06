from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class TypeDrift:
    """Per-type field-name drift between a model and ``/schema``."""

    missing_in_schema: set[str]  # model declares it, /schema does not -> actionable
    missing_in_model: set[str]  # /schema lists it, model does not -> informational


@dataclass
class SchemaDriftReport:
    """Drift between the registered models and a ``/schema`` document."""

    drifts: dict[str, TypeDrift] = field(default_factory=dict)

    @property
    def has_actionable_drift(self) -> bool:
        """True if any type has model fields the live ``/schema`` no longer lists."""
        return any(drift.missing_in_schema for drift in self.drifts.values())

    def __str__(self) -> str:
        lines: list[str] = []
        for type_name, drift in sorted(self.drifts.items()):
            if not drift.missing_in_schema and not drift.missing_in_model:
                continue
            lines.append(f"{type_name}:")
            if drift.missing_in_schema:
                lines.append(f"  ! not in /schema (actionable): {sorted(drift.missing_in_schema)}")
            if drift.missing_in_model:
                lines.append(f"  + not modelled (info): {sorted(drift.missing_in_model)}")
        if not lines:
            return "No schema drift."
        verdict = "ACTIONABLE DRIFT" if self.has_actionable_drift else "informational drift only"
        return "\n".join([*lines, f"-> {verdict}"])


def diff_schema(
    raw_schema: dict[str, Any],
    models: dict[str, type[VndbModel]] | None = None,
) -> SchemaDriftReport:
    """Compare model field names against a ``/schema`` document.

    For each registered type, computes the field names the model declares but
    ``/schema`` omits (actionable) and the names ``/schema`` lists but the model
    omits (informational). Pure: performs no I/O.
    """
    models = ENTITY_MODELS if models is None else models
    schema_fields = parse_schema_field_names(raw_schema)
    report = SchemaDriftReport()
    for type_name, model in models.items():
        model_names = model_field_names(model)
        api_names = schema_fields.get(type_name, set())
        report.drifts[type_name] = TypeDrift(
            missing_in_schema=model_names - api_names,
            missing_in_model=api_names - model_names,
        )
    return report


def main() -> int:
    """Fetch the live ``/schema``, report drift, and return an exit code.

    Returns ``1`` if there is actionable drift (model fields the API no longer
    lists), else ``0``. Imports ``Client`` lazily so the pure module stays
    import-light and I/O-free.
    """
    from vndb_client.client import Client

    with Client() as client:
        raw_schema = client.schema()
    report = diff_schema(raw_schema)
    print(report)
    return 1 if report.has_actionable_drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
