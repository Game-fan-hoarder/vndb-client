from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from vndb_client.fields import field_spec
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
        filters: Any = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool = False,
    ) -> Page[ModelT]:
        return self._client._query(
            self._endpoint,
            self._model,
            filters=filters,
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
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
        filters: Any = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int | None = None,
        page: int | None = None,
        count: bool = False,
    ) -> Page[ModelT]:
        return await self._client._query(
            self._endpoint,
            self._model,
            filters=filters,
            fields=fields if fields is not None else field_spec(self._model),
            sort=sort,
            reverse=reverse,
            results=results,
            page=page,
            count=count,
        )
