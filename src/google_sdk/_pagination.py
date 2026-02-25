"""Pagination iterators for Google API list responses."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")

FetchPage = Callable[[str | None], Any]
AsyncFetchPage = Callable[[str | None], Coroutine[Any, Any, Any]]


class PageIterator(Generic[T]):
    """Sync iterator that fetches pages on demand.

    Example::

        for file in client.drive.list_files():
            print(file.name)

        # Manual page access
        pages = client.drive.list_files().pages
        first_page = next(pages)
    """

    def __init__(
        self,
        fetch_page: FetchPage,
        item_type: type[T],
        *,
        response_key: str = "files",
    ) -> None:
        self._fetch_page = fetch_page
        self._item_type = item_type
        self._response_key = response_key
        self._buffer: list[T] = []
        self._next_token: str | None = None
        self._started = False
        self._exhausted = False

    def _load_next_page(self) -> None:
        if self._exhausted:
            return
        if self._started and self._next_token is None:
            self._exhausted = True
            return
        self._started = True
        data = self._fetch_page(self._next_token)
        items_data = data.get(self._response_key, [])
        self._buffer.extend(
            self._item_type.model_validate(item)
            if hasattr(self._item_type, "model_validate")
            else self._item_type(item)
            for item in items_data
        )
        self._next_token = data.get("nextPageToken")
        if not self._next_token:
            self._exhausted = True

    def __iter__(self) -> Iterator[T]:
        while True:
            if not self._buffer:
                if self._exhausted:
                    return
                self._load_next_page()
                if not self._buffer:
                    return
            yield self._buffer.pop(0)

    def __next__(self) -> T:
        if not self._buffer:
            if self._exhausted:
                raise StopIteration
            self._load_next_page()
        if not self._buffer:
            raise StopIteration
        return self._buffer.pop(0)

    @property
    def pages(self) -> Iterator[list[T]]:
        """Iterate over pages rather than individual items."""
        while not self._exhausted:
            self._load_next_page()
            if not self._buffer:
                return
            page = list(self._buffer)
            self._buffer.clear()
            yield page


class AsyncPageIterator(Generic[T]):
    """Async iterator that fetches pages on demand.

    Example::

        async for file in client.drive.list_files():
            print(file.name)

        # Manual page access
        async for page in client.drive.list_files().pages:
            process_batch(page)
    """

    def __init__(
        self,
        fetch_page: AsyncFetchPage,
        item_type: type[T],
        *,
        response_key: str = "files",
    ) -> None:
        self._fetch_page = fetch_page
        self._item_type = item_type
        self._response_key = response_key
        self._buffer: list[T] = []
        self._next_token: str | None = None
        self._started = False
        self._exhausted = False

    async def _load_next_page(self) -> None:
        if self._exhausted:
            return
        if self._started and self._next_token is None:
            self._exhausted = True
            return
        self._started = True
        data = await self._fetch_page(self._next_token)
        items_data = data.get(self._response_key, [])
        self._buffer.extend(
            self._item_type.model_validate(item)
            if hasattr(self._item_type, "model_validate")
            else self._item_type(item)
            for item in items_data
        )
        self._next_token = data.get("nextPageToken")
        if not self._next_token:
            self._exhausted = True

    def __aiter__(self) -> AsyncIterator[T]:
        return self._aiter()

    async def _aiter(self) -> AsyncIterator[T]:
        while True:
            if not self._buffer:
                if self._exhausted:
                    return
                await self._load_next_page()
                if not self._buffer:
                    return
            yield self._buffer.pop(0)

    @property
    def pages(self) -> AsyncIterator[list[T]]:
        """Iterate over pages rather than individual items."""
        return self._pages_aiter()

    async def _pages_aiter(self) -> AsyncIterator[list[T]]:
        while not self._exhausted:
            await self._load_next_page()
            if not self._buffer:
                return
            page = list(self._buffer)
            self._buffer.clear()
            yield page
