from __future__ import annotations

from types import TracebackType
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from vndb_client import core
from vndb_client._transport import AsyncTransport, SyncTransport
from vndb_client.config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    PROD_BASE_URL,
    RetryConfig,
)
from vndb_client.exceptions import VndbParseError
from vndb_client.models import Page

ModelT = TypeVar("ModelT", bound=BaseModel)


class Client:
    """Synchronous VNDB Kana API client."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = SyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
        )

    def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = self._transport.send(spec)
        try:
            raw = response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc
        return core.parse_page(raw, model)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncClient:
    """Asynchronous VNDB Kana API client."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = PROD_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        retry: RetryConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
        )

    async def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = await self._transport.send(spec)
        try:
            raw = response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc
        return core.parse_page(raw, model)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
