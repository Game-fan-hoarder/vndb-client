from __future__ import annotations

from types import TracebackType
from typing import Any, TypeVar, cast

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
from vndb_client.entities.character import Character
from vndb_client.entities.producer import Producer
from vndb_client.entities.quote import Quote
from vndb_client.entities.release import Release
from vndb_client.entities.staff import Staff
from vndb_client.entities.tag import Tag
from vndb_client.entities.trait import Trait
from vndb_client.entities.vn import VN
from vndb_client.exceptions import VndbParseError
from vndb_client.meta import AuthInfo, Stats, UlistLabel, User
from vndb_client.models import Page
from vndb_client.resource import AsyncQueryResource, QueryResource

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
        self.vn: QueryResource[VN] = QueryResource(self, "vn", VN)
        self.release: QueryResource[Release] = QueryResource(self, "release", Release)
        self.producer: QueryResource[Producer] = QueryResource(self, "producer", Producer)
        self.character: QueryResource[Character] = QueryResource(self, "character", Character)
        self.staff: QueryResource[Staff] = QueryResource(self, "staff", Staff)
        self.tag: QueryResource[Tag] = QueryResource(self, "tag", Tag)
        self.trait: QueryResource[Trait] = QueryResource(self, "trait", Trait)
        self.quote: QueryResource[Quote] = QueryResource(self, "quote", Quote)

    def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = self._transport.send(spec)
        try:
            raw = response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc
        return core.parse_page(raw, model)

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = self._transport.send(spec)
        try:
            return response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc

    def stats(self) -> Stats:
        return Stats.model_validate(self._get("stats"))

    def authinfo(self) -> AuthInfo:
        return AuthInfo.model_validate(self._get("authinfo"))

    def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        raw = self._get("user", params={"q": q, "fields": fields})
        result: dict[str, User | None] = {}
        for key, value in raw.items():
            result[key] = User.model_validate(value) if value is not None else None
        return result

    def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        raw = self._get("ulist_labels", params={"user": user, "fields": fields})
        return [UlistLabel.model_validate(item) for item in raw["labels"]]

    def schema(self) -> dict[str, Any]:
        return cast("dict[str, Any]", self._get("schema"))

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
        self.vn: AsyncQueryResource[VN] = AsyncQueryResource(self, "vn", VN)
        self.release: AsyncQueryResource[Release] = AsyncQueryResource(self, "release", Release)
        self.producer: AsyncQueryResource[Producer] = AsyncQueryResource(self, "producer", Producer)
        self.character: AsyncQueryResource[Character] = AsyncQueryResource(self, "character", Character)
        self.staff: AsyncQueryResource[Staff] = AsyncQueryResource(self, "staff", Staff)
        self.tag: AsyncQueryResource[Tag] = AsyncQueryResource(self, "tag", Tag)
        self.trait: AsyncQueryResource[Trait] = AsyncQueryResource(self, "trait", Trait)
        self.quote: AsyncQueryResource[Quote] = AsyncQueryResource(self, "quote", Quote)

    async def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = await self._transport.send(spec)
        try:
            raw = response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc
        return core.parse_page(raw, model)

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = await self._transport.send(spec)
        try:
            return response.json()
        except ValueError as exc:
            raise VndbParseError(str(exc)) from exc

    async def stats(self) -> Stats:
        return Stats.model_validate(await self._get("stats"))

    async def authinfo(self) -> AuthInfo:
        return AuthInfo.model_validate(await self._get("authinfo"))

    async def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        raw = await self._get("user", params={"q": q, "fields": fields})
        result: dict[str, User | None] = {}
        for key, value in raw.items():
            result[key] = User.model_validate(value) if value is not None else None
        return result

    async def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        raw = await self._get("ulist_labels", params={"user": user, "fields": fields})
        return [UlistLabel.model_validate(item) for item in raw["labels"]]

    async def schema(self) -> dict[str, Any]:
        return cast("dict[str, Any]", await self._get("schema"))

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
