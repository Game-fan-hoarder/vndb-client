from __future__ import annotations

import pytest

from vndb_client.filters.predicate import Comparison, Compound, Field, Predicate, resolve_filters


def test_bare_field_as_value_raises():
    pred = Field("a") == Field("b")
    with pytest.raises(TypeError, match="not a valid filter value"):
        pred.to_filter()


def test_each_operator_maps_to_symbol():
    f = Field("rating")
    assert (f == 80).to_filter() == ["rating", "=", 80]
    assert (f != 80).to_filter() == ["rating", "!=", 80]
    assert (f >= 80).to_filter() == ["rating", ">=", 80]
    assert (f > 80).to_filter() == ["rating", ">", 80]
    assert (f <= 80).to_filter() == ["rating", "<=", 80]
    assert (f < 80).to_filter() == ["rating", "<", 80]


def test_field_is_unhashable():
    with pytest.raises(TypeError):
        {Field("x"): 1}


def test_and_or_compose():
    a = Field("lang") == "en"
    b = Field("olang") == "ja"
    assert (a & b).to_filter() == ["and", ["lang", "=", "en"], ["olang", "=", "ja"]]
    assert (a | b).to_filter() == ["or", ["lang", "=", "en"], ["olang", "=", "ja"]]


def test_same_kind_chains_flatten():
    a = Field("a") == 1
    b = Field("b") == 2
    c = Field("c") == 3
    assert (a & b & c).to_filter() == ["and", ["a", "=", 1], ["b", "=", 2], ["c", "=", 3]]
    assert (a | b | c).to_filter() == ["or", ["a", "=", 1], ["b", "=", 2], ["c", "=", 3]]


def test_mixed_kinds_nest():
    a = Field("a") == 1
    b = Field("b") == 2
    c = Field("c") == 3
    assert ((a & b) | c).to_filter() == ["or", ["and", ["a", "=", 1], ["b", "=", 2]], ["c", "=", 3]]


def test_nested_predicate_value_serializes_recursively():
    pred = Field("character") == (Field("role") == "main")
    assert pred.to_filter() == ["character", "=", ["role", "=", "main"]]


def test_nested_compound_value():
    inner = (Field("role") == "main") & (Field("trait") == "i123")
    pred = Field("character") == inner
    assert pred.to_filter() == ["character", "=", ["and", ["role", "=", "main"], ["trait", "=", "i123"]]]


def test_scalar_and_list_values_pass_through():
    assert (Field("tag") == "g546").to_filter() == ["tag", "=", "g546"]
    assert (Field("tag") == ["g546", 0, 2]).to_filter() == ["tag", "=", ["g546", 0, 2]]


def test_resolve_filters():
    pred = Field("rating") >= 80
    assert resolve_filters(pred) == ["rating", ">=", 80]
    assert resolve_filters(["search", "=", "x"]) == ["search", "=", "x"]
    assert resolve_filters(None) is None


def test_predicate_base_is_abstract():
    assert issubclass(Comparison, Predicate)
    assert issubclass(Compound, Predicate)
