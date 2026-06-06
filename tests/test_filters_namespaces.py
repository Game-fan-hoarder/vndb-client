from __future__ import annotations

from vndb_client.filters.namespaces import (
    character_filters,
    field,
    producer_filters,
    quote_filters,
    release_filters,
    staff_filters,
    tag_filters,
    trait_filters,
    vn_filters,
)
from vndb_client.filters.predicate import Field


def test_vn_namespace_fields():
    assert vn_filters.rating.name == "rating"
    assert vn_filters.tag.name == "tag"
    assert vn_filters.search.name == "search"
    assert vn_filters.character.name == "character"


def test_character_namespace_fields():
    assert character_filters.seiyuu.name == "seiyuu"
    assert character_filters.trait.name == "trait"
    assert character_filters.cup.name == "cup"


def test_other_namespaces_spot_check():
    assert release_filters.platform.name == "platform"
    assert producer_filters.type.name == "type"
    assert staff_filters.ismain.name == "ismain"
    assert tag_filters.category.name == "category"
    assert trait_filters.search.name == "search"
    assert quote_filters.random.name == "random"


def test_field_escape_hatch():
    f = field("some_new_filter")
    assert isinstance(f, Field)
    assert (f >= 5).to_filter() == ["some_new_filter", ">=", 5]
