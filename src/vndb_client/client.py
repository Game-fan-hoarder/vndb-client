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
from vndb_client.entities.ulist import UNSET, UlistEntry, UnsetType
from vndb_client.entities.vn import VN
from vndb_client.meta import (
    AuthInfo,
    Stats,
    UlistLabel,
    User,
    parse_labels,
    parse_one,
    parse_user_map,
)
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
        cache_ttl: float | None = None,
        cache_maxsize: int = 128,
    ) -> None:
        self._transport = SyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
            cache_ttl=cache_ttl,
            cache_maxsize=cache_maxsize,
        )
        self.vn: QueryResource[VN] = QueryResource(self, "vn", VN)
        self.release: QueryResource[Release] = QueryResource(self, "release", Release)
        self.producer: QueryResource[Producer] = QueryResource(self, "producer", Producer)
        self.character: QueryResource[Character] = QueryResource(self, "character", Character)
        self.staff: QueryResource[Staff] = QueryResource(self, "staff", Staff)
        self.tag: QueryResource[Tag] = QueryResource(self, "tag", Tag)
        self.trait: QueryResource[Trait] = QueryResource(self, "trait", Trait)
        self.quote: QueryResource[Quote] = QueryResource(self, "quote", Quote)
        self.ulist: QueryResource[UlistEntry] = QueryResource(self, "ulist", UlistEntry)

    def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = self._transport.send(spec)
        return core.parse_page(core.decode_json(response), model)

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = self._transport.send(spec)
        return core.decode_json(response)

    def stats(self) -> Stats:
        """Return database-wide totals from the ``/stats`` endpoint.

        Returns:
            The site-wide entity counts.
        """
        return parse_one(Stats, self._get("stats"))

    def authinfo(self) -> AuthInfo:
        """Return identity and permissions for the current token (``/authinfo``).

        Returns:
            The authenticated token's id, username, and granted permissions.
        """
        return parse_one(AuthInfo, self._get("authinfo"))

    def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        """Look up users by id or name via the ``/user`` endpoint.

        Args:
            q: A single user id/name, or a list of them.
            fields: Optional comma-separated extra fields to request.

        Returns:
            A mapping from each query term to its ``User``, or ``None`` if unknown.
        """
        return parse_user_map(self._get("user", params={"q": q, "fields": fields}))

    def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        """List the ulist labels for a user (``/ulist_labels``).

        Args:
            user: The user id whose labels to fetch; defaults to the token's user.
            fields: Optional comma-separated extra fields to request.

        Returns:
            The user's labels.
        """
        return parse_labels(self._get("ulist_labels", params={"user": user, "fields": fields}))

    def schema(self) -> dict[str, Any]:
        """Return the raw VNDB API schema document (``/schema``).

        Returns:
            The schema as a plain JSON-decoded dict.
        """
        return cast("dict[str, Any]", self._get("schema"))

    def _write(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> None:
        spec = core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)
        self._transport.send(spec)

    def set_ulist(
        self,
        vn_id: str,
        *,
        vote: int | None | UnsetType = UNSET,
        notes: str | None | UnsetType = UNSET,
        started: str | None | UnsetType = UNSET,
        finished: str | None | UnsetType = UNSET,
        labels: list[int] | None = None,
        labels_set: list[int] | None = None,
        labels_unset: list[int] | None = None,
    ) -> None:
        """Create or update the authenticated user's ulist entry for a VN.

        Each scalar argument defaults to ``UNSET`` (the field is omitted from the
        request); pass ``None`` to clear it, or a value to set it.

        Args:
            vn_id: The VN id (e.g. ``"v17"``).
            vote: Vote in 10-100, ``None`` to clear, or ``UNSET`` to leave as-is.
            notes: Free-text notes, ``None`` to clear, or ``UNSET`` to leave as-is.
            started: Start date ``YYYY-MM-DD``, ``None`` to clear, or ``UNSET``.
            finished: Finish date ``YYYY-MM-DD``, ``None`` to clear, or ``UNSET``.
            labels: Replace the entry's labels with this exact list of label ids.
            labels_set: Label ids to add.
            labels_unset: Label ids to remove.
        """
        body: dict[str, Any] = {}
        if vote is not UNSET:
            body["vote"] = vote
        if notes is not UNSET:
            body["notes"] = notes
        if started is not UNSET:
            body["started"] = started
        if finished is not UNSET:
            body["finished"] = finished
        if labels is not None:
            body["labels"] = labels
        if labels_set is not None:
            body["labels_set"] = labels_set
        if labels_unset is not None:
            body["labels_unset"] = labels_unset
        self._write("PATCH", f"ulist/{vn_id}", json=body)

    def delete_ulist(self, vn_id: str) -> None:
        """Remove the authenticated user's ulist entry for ``vn_id``."""
        self._write("DELETE", f"ulist/{vn_id}")

    def set_rlist(self, release_id: str, *, status: int) -> None:
        """Set the authenticated user's rlist status for a release.

        Args:
            release_id: The release id (e.g. ``"r123"``).
            status: The rlist status; accepts an ``int`` or an ``RListStatus`` value.
        """
        self._write("PATCH", f"rlist/{release_id}", json={"status": status})

    def delete_rlist(self, release_id: str) -> None:
        """Remove the authenticated user's rlist entry for ``release_id``."""
        self._write("DELETE", f"rlist/{release_id}")

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
        cache_ttl: float | None = None,
        cache_maxsize: int = 128,
    ) -> None:
        self._transport = AsyncTransport(
            token=token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            retry=retry,
            http_client=http_client,
            cache_ttl=cache_ttl,
            cache_maxsize=cache_maxsize,
        )
        self.vn: AsyncQueryResource[VN] = AsyncQueryResource(self, "vn", VN)
        self.release: AsyncQueryResource[Release] = AsyncQueryResource(self, "release", Release)
        self.producer: AsyncQueryResource[Producer] = AsyncQueryResource(self, "producer", Producer)
        self.character: AsyncQueryResource[Character] = AsyncQueryResource(self, "character", Character)
        self.staff: AsyncQueryResource[Staff] = AsyncQueryResource(self, "staff", Staff)
        self.tag: AsyncQueryResource[Tag] = AsyncQueryResource(self, "tag", Tag)
        self.trait: AsyncQueryResource[Trait] = AsyncQueryResource(self, "trait", Trait)
        self.quote: AsyncQueryResource[Quote] = AsyncQueryResource(self, "quote", Quote)
        self.ulist: AsyncQueryResource[UlistEntry] = AsyncQueryResource(self, "ulist", UlistEntry)

    async def _query(self, endpoint: str, model: type[ModelT], **params: Any) -> Page[ModelT]:
        spec = core.build_query_request(endpoint, **params)
        response = await self._transport.send(spec)
        return core.parse_page(core.decode_json(response), model)

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        clean = {key: value for key, value in (params or {}).items() if value is not None}
        spec = core.RequestSpec(method="GET", path=f"/{path.lstrip('/')}", params=clean or None)
        response = await self._transport.send(spec)
        return core.decode_json(response)

    async def stats(self) -> Stats:
        """Return database-wide totals from the ``/stats`` endpoint.

        Returns:
            The site-wide entity counts.
        """
        return parse_one(Stats, await self._get("stats"))

    async def authinfo(self) -> AuthInfo:
        """Return identity and permissions for the current token (``/authinfo``).

        Returns:
            The authenticated token's id, username, and granted permissions.
        """
        return parse_one(AuthInfo, await self._get("authinfo"))

    async def get_user(self, q: str | list[str], *, fields: str | None = None) -> dict[str, User | None]:
        """Look up users by id or name via the ``/user`` endpoint.

        Args:
            q: A single user id/name, or a list of them.
            fields: Optional comma-separated extra fields to request.

        Returns:
            A mapping from each query term to its ``User``, or ``None`` if unknown.
        """
        return parse_user_map(await self._get("user", params={"q": q, "fields": fields}))

    async def ulist_labels(self, user: str | None = None, *, fields: str | None = None) -> list[UlistLabel]:
        """List the ulist labels for a user (``/ulist_labels``).

        Args:
            user: The user id whose labels to fetch; defaults to the token's user.
            fields: Optional comma-separated extra fields to request.

        Returns:
            The user's labels.
        """
        return parse_labels(await self._get("ulist_labels", params={"user": user, "fields": fields}))

    async def schema(self) -> dict[str, Any]:
        """Return the raw VNDB API schema document (``/schema``).

        Returns:
            The schema as a plain JSON-decoded dict.
        """
        return cast("dict[str, Any]", await self._get("schema"))

    async def _write(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> None:
        spec = core.RequestSpec(method=method, path=f"/{path.lstrip('/')}", json=json)
        await self._transport.send(spec)

    async def set_ulist(
        self,
        vn_id: str,
        *,
        vote: int | None | UnsetType = UNSET,
        notes: str | None | UnsetType = UNSET,
        started: str | None | UnsetType = UNSET,
        finished: str | None | UnsetType = UNSET,
        labels: list[int] | None = None,
        labels_set: list[int] | None = None,
        labels_unset: list[int] | None = None,
    ) -> None:
        """Create or update the authenticated user's ulist entry for a VN.

        Each scalar argument defaults to ``UNSET`` (the field is omitted from the
        request); pass ``None`` to clear it, or a value to set it.

        Args:
            vn_id: The VN id (e.g. ``"v17"``).
            vote: Vote in 10-100, ``None`` to clear, or ``UNSET`` to leave as-is.
            notes: Free-text notes, ``None`` to clear, or ``UNSET`` to leave as-is.
            started: Start date ``YYYY-MM-DD``, ``None`` to clear, or ``UNSET``.
            finished: Finish date ``YYYY-MM-DD``, ``None`` to clear, or ``UNSET``.
            labels: Replace the entry's labels with this exact list of label ids.
            labels_set: Label ids to add.
            labels_unset: Label ids to remove.
        """
        body: dict[str, Any] = {}
        if vote is not UNSET:
            body["vote"] = vote
        if notes is not UNSET:
            body["notes"] = notes
        if started is not UNSET:
            body["started"] = started
        if finished is not UNSET:
            body["finished"] = finished
        if labels is not None:
            body["labels"] = labels
        if labels_set is not None:
            body["labels_set"] = labels_set
        if labels_unset is not None:
            body["labels_unset"] = labels_unset
        await self._write("PATCH", f"ulist/{vn_id}", json=body)

    async def delete_ulist(self, vn_id: str) -> None:
        """Remove the authenticated user's ulist entry for ``vn_id``."""
        await self._write("DELETE", f"ulist/{vn_id}")

    async def set_rlist(self, release_id: str, *, status: int) -> None:
        """Set the authenticated user's rlist status for a release.

        Args:
            release_id: The release id (e.g. ``"r123"``).
            status: The rlist status; accepts an ``int`` or an ``RListStatus`` value.
        """
        await self._write("PATCH", f"rlist/{release_id}", json={"status": status})

    async def delete_rlist(self, release_id: str) -> None:
        """Remove the authenticated user's rlist entry for ``release_id``."""
        await self._write("DELETE", f"rlist/{release_id}")

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
