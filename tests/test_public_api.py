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
