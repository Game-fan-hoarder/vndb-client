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
    ):
        assert hasattr(vndb_client, name), name
        assert name in vndb_client.__all__
