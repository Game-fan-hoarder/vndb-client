from __future__ import annotations

import asyncio
import time

import httpx

from vndb_client import core
from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    RetryConfig,
)
from vndb_client.core import RequestSpec, RetryPolicy
from vndb_client.exceptions import VndbNetworkError


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


async def _asleep(seconds: float) -> None:
    await asyncio.sleep(seconds)


def _build_headers(token: str | None, user_agent: str) -> dict[str, str]:
    headers = {"User-Agent": user_agent}
    if token:
        headers["Authorization"] = f"Token {token}"
    return headers


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


class SyncTransport:
    """Synchronous HTTP transport with a bounded retry loop."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._policy = RetryPolicy(retry or RetryConfig())
        self._headers = _build_headers(token, user_agent)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(base_url=base_url, timeout=timeout)

    def send(self, spec: RequestSpec) -> httpx.Response:
        attempt = 0
        while True:
            attempt += 1
            status: int | None = None
            exc: Exception | None = None
            retry_after: float | None = None
            response: httpx.Response | None = None
            try:
                response = self._client.request(
                    spec.method, spec.path, json=spec.json, params=spec.params, headers=self._headers
                )
            except httpx.TransportError as transport_exc:
                exc = transport_exc
            else:
                if response.status_code < 400:
                    return response
                status = response.status_code
                retry_after = _retry_after(response)
            should_retry, delay = self._policy.next(attempt, status, exc, retry_after)
            if should_retry:
                _sleep(delay)
                continue
            if response is None:
                raise VndbNetworkError(str(exc)) from exc
            core.raise_for_status(response.status_code, response.text)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class AsyncTransport:
    """Asynchronous HTTP transport with a bounded retry loop."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._policy = RetryPolicy(retry or RetryConfig())
        self._headers = _build_headers(token, user_agent)
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def send(self, spec: RequestSpec) -> httpx.Response:
        attempt = 0
        while True:
            attempt += 1
            status: int | None = None
            exc: Exception | None = None
            retry_after: float | None = None
            response: httpx.Response | None = None
            try:
                response = await self._client.request(
                    spec.method, spec.path, json=spec.json, params=spec.params, headers=self._headers
                )
            except httpx.TransportError as transport_exc:
                exc = transport_exc
            else:
                if response.status_code < 400:
                    return response
                status = response.status_code
                retry_after = _retry_after(response)
            should_retry, delay = self._policy.next(attempt, status, exc, retry_after)
            if should_retry:
                await _asleep(delay)
                continue
            if response is None:
                raise VndbNetworkError(str(exc)) from exc
            core.raise_for_status(response.status_code, response.text)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
