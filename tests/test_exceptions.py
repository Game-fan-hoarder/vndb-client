from __future__ import annotations

import pytest

from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbError,
    VndbNetworkError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)


@pytest.mark.parametrize(
    "exc_type",
    [
        VndbBadRequestError,
        VndbAuthError,
        VndbNotFoundError,
        VndbRateLimitError,
        VndbServerError,
    ],
)
def test_api_errors_are_vndb_errors_and_carry_status_and_message(exc_type):
    err = exc_type(status_code=418, message="teapot")
    assert isinstance(err, VndbError)
    assert isinstance(err, VndbAPIError)
    assert err.status_code == 418
    assert err.message == "teapot"
    assert "418" in str(err)
    assert "teapot" in str(err)


def test_network_error_is_vndb_error_and_chains_cause():
    original = ConnectionError("boom")
    err = VndbNetworkError("connect failed")
    assert isinstance(err, VndbError)
    assert err.message == "connect failed"
    err.__cause__ = original
    assert err.__cause__ is original


def test_parse_error_is_vndb_error():
    err = VndbParseError("bad shape")
    assert isinstance(err, VndbError)
    assert err.message == "bad shape"
