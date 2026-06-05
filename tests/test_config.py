from __future__ import annotations

from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    SANDBOX_BASE_URL,
    RetryConfig,
)


def test_base_urls():
    assert PROD_BASE_URL == "https://api.vndb.org/kana"
    assert SANDBOX_BASE_URL == "https://beta.vndb.org/api/kana"


def test_defaults_present():
    assert DEFAULT_TIMEOUT > 0
    assert "vndb-client" in DEFAULT_USER_AGENT


def test_retry_config_defaults_and_immutability():
    cfg = RetryConfig()
    assert cfg.max_attempts == 3
    assert cfg.backoff_base > 0
    assert cfg.backoff_cap >= cfg.backoff_base
    assert 429 in cfg.retry_statuses
    assert 502 in cfg.retry_statuses
    assert 503 in cfg.retry_statuses
    assert 500 not in cfg.retry_statuses
