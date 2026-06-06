from __future__ import annotations

import httpx
import pytest

from vndb_client import core
from vndb_client.config import RetryConfig
from vndb_client.core import RequestSpec, RetryPolicy
from vndb_client.exceptions import (
    VndbAPIError,
    VndbAuthError,
    VndbBadRequestError,
    VndbNotFoundError,
    VndbParseError,
    VndbRateLimitError,
    VndbServerError,
)
from vndb_client.models import Page, VndbModel


class _Dummy(VndbModel):
    id: str


# --- build_query_request ---


def test_build_query_request_includes_only_provided_fields():
    spec = core.build_query_request("vn", filters=["id", "=", "v17"], fields="id,title", results=5)
    assert isinstance(spec, RequestSpec)
    assert spec.method == "POST"
    assert spec.path == "/vn"
    assert spec.json == {"filters": ["id", "=", "v17"], "fields": "id,title", "results": 5}


def test_build_query_request_normalizes_leading_slash():
    spec = core.build_query_request("/vn", count=True)
    assert spec.path == "/vn"
    assert spec.json == {"count": True}


# --- raise_for_status ---


@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (400, VndbBadRequestError),
        (401, VndbAuthError),
        (404, VndbNotFoundError),
        (429, VndbRateLimitError),
        (500, VndbServerError),
        (502, VndbServerError),
        (418, VndbAPIError),
    ],
)
def test_raise_for_status_maps_codes(status, exc_type):
    with pytest.raises(exc_type) as info:
        core.raise_for_status(status, "  body text  ")
    assert info.value.status_code == status
    assert info.value.message == "body text"


def test_raise_for_status_noop_below_400():
    assert core.raise_for_status(200, "ok") is None


# --- RetryPolicy.next ---


def _policy():
    return RetryPolicy(RetryConfig(max_attempts=3, backoff_base=0.5, backoff_cap=10.0))


def test_retry_on_429_without_retry_after_uses_exponential_backoff():
    retry, delay = _policy().next(attempt=1, status=429, exc=None)
    assert retry is True
    assert delay == pytest.approx(0.5)  # base * 2**(1-1)
    retry2, delay2 = _policy().next(attempt=2, status=429, exc=None)
    assert retry2 is True
    assert delay2 == pytest.approx(1.0)  # base * 2**(2-1)


def test_retry_on_429_honors_retry_after():
    retry, delay = _policy().next(attempt=1, status=429, exc=None, retry_after=7.0)
    assert retry is True
    assert delay == pytest.approx(7.0)


def test_retry_on_transient_5xx_and_network():
    assert _policy().next(attempt=1, status=502, exc=None)[0] is True
    assert _policy().next(attempt=1, status=None, exc=httpx.ConnectError("x"))[0] is True


def test_retry_honors_retry_after_on_transient_5xx():
    retry, delay = _policy().next(attempt=1, status=503, exc=None, retry_after=9.0)
    assert retry is True
    assert delay == pytest.approx(9.0)  # Retry-After honored for 5xx, not just 429


def test_no_retry_on_non_retryable_statuses():
    for status in (400, 401, 404, 500):
        assert _policy().next(attempt=1, status=status, exc=None)[0] is False


def test_no_retry_when_attempts_exhausted():
    retry, delay = _policy().next(attempt=3, status=429, exc=None)
    assert retry is False
    assert delay == 0.0


def test_backoff_is_capped():
    cfg = RetryConfig(max_attempts=99, backoff_base=1.0, backoff_cap=4.0)
    retry, delay = RetryPolicy(cfg).next(attempt=10, status=429, exc=None)
    assert retry is True
    assert delay == pytest.approx(4.0)


# --- parse_page ---


def test_parse_page_returns_typed_page():
    page = core.parse_page({"results": [{"id": "v1"}], "more": False}, _Dummy)
    assert isinstance(page, Page)
    assert page.results[0].id == "v1"


def test_parse_page_wraps_validation_error():
    with pytest.raises(VndbParseError):
        core.parse_page({"results": [{"wrong": "shape"}], "more": False}, _Dummy)


# --- decode_json ---


def test_decode_json_returns_payload():
    assert core.decode_json(httpx.Response(200, json={"a": 1})) == {"a": 1}


def test_decode_json_wraps_value_error():
    with pytest.raises(VndbParseError):
        core.decode_json(httpx.Response(200, text="not json"))


def test_build_query_request_includes_filter_echo_flags_when_set():
    spec = core.build_query_request("vn", compact_filters=True, normalized_filters=True)
    assert spec.json["compact_filters"] is True
    assert spec.json["normalized_filters"] is True


def test_build_query_request_omits_filter_echo_flags_when_unset():
    spec = core.build_query_request("vn", filters=["id", "=", "v1"])
    assert "compact_filters" not in spec.json
    assert "normalized_filters" not in spec.json
