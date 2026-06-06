from __future__ import annotations

import vndb_client


def test_public_exports_present():
    for name in (
        "Client",
        "AsyncClient",
        "Page",
        "RetryConfig",
        "VndbError",
        "VndbAPIError",
        "VndbBadRequestError",
        "VndbAuthError",
        "VndbNotFoundError",
        "VndbRateLimitError",
        "VndbServerError",
        "VndbNetworkError",
        "VndbParseError",
        "VndbModel",
    ):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_vn_entity_exports_present():
    import vndb_client

    for name in ("VN", "Title", "Image", "DevStatus", "VNLength"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_entity_coverage_exports_present():
    import vndb_client

    for name in ("Release", "Producer", "Character", "Staff", "Tag", "Trait", "Quote", "ImageBase"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_filters_package_exports():
    import vndb_client.filters as f

    for name in (
        "vn_filters",
        "release_filters",
        "producer_filters",
        "character_filters",
        "staff_filters",
        "tag_filters",
        "trait_filters",
        "quote_filters",
        "field",
        "Predicate",
    ):
        assert hasattr(f, name), name
        assert name in f.__all__


def test_meta_exports_present():
    import vndb_client

    for name in ("Stats", "AuthInfo", "User", "UlistLabel"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_user_list_exports_present():
    import vndb_client

    for name in ("UlistEntry", "UlistEntryLabel", "UlistVN", "RListStatus", "UNSET", "UnsetType"):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_entity_submodels_exported():
    import vndb_client

    for name in (
        "ProducerType",
        "QuoteVN",
        "QuoteCharacter",
        "ReleaseLang",
        "ReleaseMedia",
        "StaffAlias",
        "TagCategory",
    ):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__


def test_all_is_consistent_and_sorted():
    import vndb_client

    names = vndb_client.__all__
    # No duplicates, and every listed name actually resolves on the package.
    assert len(names) == len(set(names))
    for name in names:
        assert hasattr(vndb_client, name), name
    # Matches ruff RUF022 ordering: all-uppercase constants first, then the rest.
    consts = sorted(n for n in names if n.isupper())
    others = sorted(n for n in names if not n.isupper())
    assert list(names) == consts + others
