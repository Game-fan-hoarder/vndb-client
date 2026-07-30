from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from vndb_client.core import PageWalk
from vndb_client.fields import field_spec
from vndb_client.filters.predicate import Predicate, resolve_filters
from vndb_client.models import Page, VndbModel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from vndb_client.client import AsyncClient, Client

ModelT = TypeVar("ModelT", bound=VndbModel)

#: Page size both paginating methods request by default — the API's maximum.
#: Deliberately not validated client-side: this default encodes today's maximum
#: as a choice rather than as a rule this client must keep in sync with VNDB.
MAX_RESULTS_PER_PAGE = 100


def _truncated(page: Page[ModelT], keep: int) -> Page[ModelT]:
    """Copy ``page`` with its results sliced to ``keep``, leaving ``more`` untouched."""
    return page.model_copy(update={"results": page.results[:keep]})


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

    def pages(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int = MAX_RESULTS_PER_PAGE,
        start_page: int = 1,
        limit: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> Iterator[Page[ModelT]]:
        """Walk the query's result set, yielding one ``Page`` per request.

        Requests are issued lazily: nothing is sent until the returned
        generator is first advanced. The walk stops when the API reports no
        further pages, when ``limit`` is reached, or when a page comes back
        empty while still claiming more pages exist.

        Args:
            filters: As :meth:`query`.
            fields: As :meth:`query`.
            sort: As :meth:`query`.
            reverse: As :meth:`query`.
            results: Records per request, defaulting to the API's maximum of
                100 so a full walk costs the fewest requests. Not validated
                client-side; an out-of-range value produces a 400 from the API.
            start_page: 1-based page to begin at. Use it to resume a long walk
                that failed part-way rather than restarting it. There is
                deliberately no ``page`` parameter: the walk owns the counter.
            limit: Maximum number of *records* (not pages) to emit in total.
                ``None`` walks every matching record. When the limit falls
                inside a page, that page is yielded with its ``results``
                truncated so the walk's record total equals ``limit`` exactly;
                the page's ``more`` flag is left as the API reported it, since
                it describes the server's state and not this iteration's.
            count: As :meth:`query`. When ``True`` the API populates
                ``Page.count`` on every page, not just the first.
            user: As :meth:`query`.
            compact_filters: As :meth:`query`.
            normalized_filters: As :meth:`query`.

        Yields:
            One ``Page`` per issued request, in page order.

        Raises:
            ValueError: If ``start_page`` is below 1 or ``limit`` is not
                positive. Raised on call, not on first iteration.
        """
        walk = PageWalk(start_page=start_page, limit=limit)
        return self._walk(
            walk,
            filters=filters,
            fields=fields,
            sort=sort,
            reverse=reverse,
            results=results,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )

    def iterate(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int = MAX_RESULTS_PER_PAGE,
        start_page: int = 1,
        limit: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> Iterator[ModelT]:
        """Walk the query's result set, yielding individual records.

        The flattened form of :meth:`pages`, which it delegates to; every
        parameter and stopping rule documented there applies unchanged, and
        ``limit`` caps records here too.

        Yields:
            Each matching record, in API order.

        Raises:
            ValueError: If ``start_page`` is below 1 or ``limit`` is not
                positive. Raised on call, not on first iteration.
        """
        pages = self.pages(
            filters=filters,
            fields=fields,
            sort=sort,
            reverse=reverse,
            results=results,
            start_page=start_page,
            limit=limit,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )
        return (record for page in pages for record in page.results)

    def _walk(
        self,
        walk: PageWalk,
        *,
        filters: Predicate | list[Any] | str | None,
        fields: str | None,
        sort: str | None,
        reverse: bool | None,
        results: int,
        count: bool | None,
        user: str | None,
        compact_filters: bool | None,
        normalized_filters: bool | None,
    ) -> Iterator[Page[ModelT]]:
        """Drive the request loop, deferring every stop/truncate decision to ``walk``."""
        page_no = walk.start_page
        yielded = 0
        while True:
            page = self.query(
                filters=filters,
                fields=fields,
                sort=sort,
                reverse=reverse,
                results=results,
                page=page_no,
                count=count,
                user=user,
                compact_filters=compact_filters,
                normalized_filters=normalized_filters,
            )
            available = len(page.results)
            keep = walk.take(yielded, available)
            yield _truncated(page, keep) if keep < available else page
            yielded += keep
            if not walk.should_continue(more=page.more, yielded=yielded, available=available):
                return
            page_no += 1


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

    def pages(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int = MAX_RESULTS_PER_PAGE,
        start_page: int = 1,
        limit: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> AsyncIterator[Page[ModelT]]:
        """Walk the query's result set, yielding one ``Page`` per request.

        The asynchronous mirror of :meth:`QueryResource.pages`, for use with
        ``async for``. Requests are issued lazily: nothing is sent until the
        returned generator is first advanced. The walk stops when the API
        reports no further pages, when ``limit`` is reached, or when a page
        comes back empty while still claiming more pages exist.

        Args:
            filters: As :meth:`query`.
            fields: As :meth:`query`.
            sort: As :meth:`query`.
            reverse: As :meth:`query`.
            results: Records per request, defaulting to the API's maximum of
                100 so a full walk costs the fewest requests. Not validated
                client-side; an out-of-range value produces a 400 from the API.
            start_page: 1-based page to begin at. Use it to resume a long walk
                that failed part-way rather than restarting it. There is
                deliberately no ``page`` parameter: the walk owns the counter.
            limit: Maximum number of *records* (not pages) to emit in total.
                ``None`` walks every matching record. When the limit falls
                inside a page, that page is yielded with its ``results``
                truncated so the walk's record total equals ``limit`` exactly;
                the page's ``more`` flag is left as the API reported it, since
                it describes the server's state and not this iteration's.
            count: As :meth:`query`. When ``True`` the API populates
                ``Page.count`` on every page, not just the first.
            user: As :meth:`query`.
            compact_filters: As :meth:`query`.
            normalized_filters: As :meth:`query`.

        Yields:
            One ``Page`` per issued request, in page order.

        Raises:
            ValueError: If ``start_page`` is below 1 or ``limit`` is not
                positive. Raised on call, not on first iteration.
        """
        walk = PageWalk(start_page=start_page, limit=limit)
        return self._walk(
            walk,
            filters=filters,
            fields=fields,
            sort=sort,
            reverse=reverse,
            results=results,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )

    def iterate(
        self,
        *,
        filters: Predicate | list[Any] | str | None = None,
        fields: str | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        results: int = MAX_RESULTS_PER_PAGE,
        start_page: int = 1,
        limit: int | None = None,
        count: bool | None = None,
        user: str | None = None,
        compact_filters: bool | None = None,
        normalized_filters: bool | None = None,
    ) -> AsyncIterator[ModelT]:
        """Walk the query's result set, yielding individual records.

        The flattened form of :meth:`pages`, which it delegates to; every
        parameter and stopping rule documented there applies unchanged, and
        ``limit`` caps records here too.

        Yields:
            Each matching record, in API order.

        Raises:
            ValueError: If ``start_page`` is below 1 or ``limit`` is not
                positive. Raised on call, not on first iteration.
        """
        pages = self.pages(
            filters=filters,
            fields=fields,
            sort=sort,
            reverse=reverse,
            results=results,
            start_page=start_page,
            limit=limit,
            count=count,
            user=user,
            compact_filters=compact_filters,
            normalized_filters=normalized_filters,
        )
        return _flatten(pages)

    async def _walk(
        self,
        walk: PageWalk,
        *,
        filters: Predicate | list[Any] | str | None,
        fields: str | None,
        sort: str | None,
        reverse: bool | None,
        results: int,
        count: bool | None,
        user: str | None,
        compact_filters: bool | None,
        normalized_filters: bool | None,
    ) -> AsyncIterator[Page[ModelT]]:
        """Drive the request loop, deferring every stop/truncate decision to ``walk``."""
        page_no = walk.start_page
        yielded = 0
        while True:
            page = await self.query(
                filters=filters,
                fields=fields,
                sort=sort,
                reverse=reverse,
                results=results,
                page=page_no,
                count=count,
                user=user,
                compact_filters=compact_filters,
                normalized_filters=normalized_filters,
            )
            available = len(page.results)
            keep = walk.take(yielded, available)
            yield _truncated(page, keep) if keep < available else page
            yielded += keep
            if not walk.should_continue(more=page.more, yielded=yielded, available=available):
                return
            page_no += 1


async def _flatten(pages: AsyncIterator[Page[ModelT]]) -> AsyncIterator[ModelT]:
    """Flatten an asynchronous page walk into its individual records."""
    async for page in pages:
        for record in page.results:
            yield record
