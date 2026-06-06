from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from vndb_client.fields import field_spec
from vndb_client.filters.predicate import Predicate, resolve_filters
from vndb_client.models import Page, VndbModel

if TYPE_CHECKING:
    from vndb_client.client import AsyncClient, Client

ModelT = TypeVar("ModelT", bound=VndbModel)


class QueryResource(Generic[ModelT]):
    """A typed, synchronous query resource bound to one VNDB endpoint + model."""

    def __init__(self, client: Client, endpoint: str, model: type[ModelT]) -> None:
        self._client = client
        self._endpoint = endpoint
        self._model = model

    def query(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> Page[ModelT]:
        """Query the endpoint and return a typed ``Page``.

        Args:
            filters: Filter predicate, raw list, or a compact filter string
                returned from a previous ``Page`` (round-tripping).
            fields: Comma-separated field list; defaults to ``field_spec`` for
                the bound model.
            sort: Field name to sort by.
            reverse: Reverse the sort order when ``True``.
            results: Maximum number of results to return.
            page: Page number (1-based).
            count: When ``True`` the API populates ``Page.count``.
            user: User ID for endpoints that require one (e.g. ulist).
            compact_filters: Request flag asking the API to echo the compact
                filter string back in the returned ``Page``.
            normalized_filters: Request flag asking the API to echo the
                normalised filter list back in the returned ``Page``.
        """
        return self._client._query(
            self._endpoint,
            self._model,
            filters=resolve_filters(filters),
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )


class AsyncQueryResource(Generic[ModelT]):
    """A typed, asynchronous query resource bound to one VNDB endpoint + model."""

    def __init__(self, client: AsyncClient, endpoint: str, model: type[ModelT]) -> None:
        self._client = client
        self._endpoint = endpoint
        self._model = model

    async def query(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> Page[ModelT]:
        """Query the endpoint and return a typed ``Page``.

        Args:
            filters: Filter predicate, raw list, or a compact filter string
                returned from a previous ``Page`` (round-tripping).
            fields: Comma-separated field list; defaults to ``field_spec`` for
                the bound model.
            sort: Field name to sort by.
            reverse: Reverse the sort order when ``True``.
            results: Maximum number of results to return.
            page: Page number (1-based).
            count: When ``True`` the API populates ``Page.count``.
            user: User ID for endpoints that require one (e.g. ulist).
            compact_filters: Request flag asking the API to echo the compact
                filter string back in the returned ``Page``.
            normalized_filters: Request flag asking the API to echo the
                normalised filter list back in the returned ``Page``.
        """
        return await self._client._query(
            self._endpoint,
            self._model,
            filters=resolve_filters(filters),
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )
