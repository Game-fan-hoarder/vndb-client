from __future__ import annotations

import abc
from typing import Any


class Predicate(abc.ABC):
    """Base class for filter predicates that serialize to VNDB's filter DSL."""

    @abc.abstractmethod
    def to_filter(self) -> list[Any]:
        """Serialize this predicate to VNDB's nested-list filter form."""

    def __and__(self, other: Predicate) -> Compound:
        return Compound._combine("and", self, other)

    def __or__(self, other: Predicate) -> Compound:
        return Compound._combine("or", self, other)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Field):
        msg = f"a bare Field ({value.name!r}) is not a valid filter value; use a comparison operator"
        raise TypeError(msg)
    return value.to_filter() if isinstance(value, Predicate) else value


class Comparison(Predicate):
    """A single ``[field, op, value]`` predicate."""

    def __init__(self, name: str, op: str, value: Any) -> None:
        self.name = name
        self.op = op
        self.value = value

    def to_filter(self) -> list[Any]:
        return [self.name, self.op, _serialize_value(self.value)]


class Compound(Predicate):
    """An ``["and"|"or", ...]`` predicate."""

    def __init__(self, kind: str, predicates: list[Predicate]) -> None:
        self.kind = kind
        self.predicates = predicates

    @classmethod
    def _combine(cls, kind: str, left: Predicate, right: Predicate) -> Compound:
        terms: list[Predicate] = []
        for part in (left, right):
            if isinstance(part, Compound) and part.kind == kind:
                terms.extend(part.predicates)
            else:
                terms.append(part)
        return cls(kind, terms)

    def to_filter(self) -> list[Any]:
        return [self.kind, *(p.to_filter() for p in self.predicates)]


class Field:
    """A filterable field; comparison operators build :class:`Comparison`s.

    Because ``&``/``|`` bind looser than comparison operators in Python, wrap each
    comparison in parentheses when composing: ``(f.rating >= 80) & (f.lang == "en")``.

    Instances are immutable: namespace fields (e.g. ``vn_filters.rating``) are shared
    singletons, so rebinding ``.name`` is blocked to avoid corrupting them globally.
    """

    __slots__ = ("name",)

    name: str

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "name", name)

    def __setattr__(self, key: str, value: Any) -> None:
        msg = "Field is immutable"
        raise AttributeError(msg)

    def __eq__(self, other: Any) -> Comparison:  # type: ignore[override]
        return Comparison(self.name, "=", other)

    def __ne__(self, other: Any) -> Comparison:  # type: ignore[override]
        return Comparison(self.name, "!=", other)

    def __ge__(self, other: Any) -> Comparison:
        return Comparison(self.name, ">=", other)

    def __gt__(self, other: Any) -> Comparison:
        return Comparison(self.name, ">", other)

    def __le__(self, other: Any) -> Comparison:
        return Comparison(self.name, "<=", other)

    def __lt__(self, other: Any) -> Comparison:
        return Comparison(self.name, "<", other)


def resolve_filters(filters: Predicate | list[Any] | None) -> list[Any] | None:
    """Serialize a :class:`Predicate` to its list form; pass raw lists / ``None`` through."""
    if isinstance(filters, Predicate):
        return filters.to_filter()
    return filters
