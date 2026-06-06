from __future__ import annotations

from types import UnionType
from typing import Any, Union, get_args, get_origin

from vndb_client.models import VndbModel


def _core_type(annotation: Any) -> Any:
    """Strip Optional/Union[..., None] and list/set/tuple wrappers to the core type."""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        return _core_type(non_none[0]) if len(non_none) == 1 else annotation
    if origin in (list, set, frozenset, tuple):
        args = get_args(annotation)
        return _core_type(args[0]) if args else annotation
    return annotation


def field_spec(model: type[VndbModel]) -> str:
    """Derive the VNDB ``fields`` request string from a model.

    Uses each field's alias (or name), and recurses into nested ``VndbModel``
    sub-models with dotted paths. List-of-scalar fields stay bare.

    Raises:
        ValueError: if ``model`` declares no fields (would produce an empty,
            API-rejected ``fields`` string).
    """
    parts: list[str] = []
    for name, info in model.model_fields.items():
        key = info.alias or name
        inner = _core_type(info.annotation)
        if isinstance(inner, type) and issubclass(inner, VndbModel):
            parts.extend(f"{key}.{nested}" for nested in field_spec(inner).split(",") if nested)
        else:
            parts.append(key)
    if not parts:
        msg = f"{model.__name__} declares no fields to request"
        raise ValueError(msg)
    return ",".join(parts)
