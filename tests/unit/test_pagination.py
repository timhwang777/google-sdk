"""Tests for PageIterator and AsyncPageIterator."""

import pytest

from google_sdk._models.base import BaseResource
from google_sdk._pagination import AsyncPageIterator, PageIterator


def make_pages(pages: list[list[dict]], response_key: str = "files"):
    """Create a fetch_page function from a list of pages."""
    tokens = [f"token_{i}" for i in range(len(pages))]

    def fetch_page(page_token: str | None) -> dict:
        idx = 0 if page_token is None else int(page_token.split("_")[1])
        items = pages[idx]
        next_token = tokens[idx + 1] if idx + 1 < len(pages) else None
        return (
            {response_key: items, "nextPageToken": next_token}
            if next_token
            else {response_key: items}
        )

    return fetch_page


# ── Sync PageIterator ────────────────────────────────────────────────────────


def test_page_iterator_yields_items():
    pages = [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    fetch = make_pages(pages)
    it = PageIterator(fetch, BaseResource)
    items = list(it)
    assert len(items) == 3
    assert items[0].id == "1"
    assert items[2].id == "3"


def test_page_iterator_empty():
    fetch = make_pages([[]])
    it = PageIterator(fetch, BaseResource)
    assert list(it) == []


def test_page_iterator_single_page():
    fetch = make_pages([[{"id": "a"}, {"id": "b"}]])
    it = PageIterator(fetch, BaseResource)
    assert len(list(it)) == 2


def test_page_iterator_stops_on_no_next_token():
    pages = [[{"id": "1"}]]
    fetch = make_pages(pages)
    it = PageIterator(fetch, BaseResource)
    items = list(it)
    assert len(items) == 1


def test_page_iterator_pages_property():
    pages = [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    fetch = make_pages(pages)
    it = PageIterator(fetch, BaseResource)
    all_pages = list(it.pages)
    assert len(all_pages) == 2
    assert len(all_pages[0]) == 2
    assert len(all_pages[1]) == 1


# ── Async PageIterator ───────────────────────────────────────────────────────


def make_async_pages(pages: list[list[dict]], response_key: str = "files"):
    tokens = [f"token_{i}" for i in range(len(pages))]

    async def fetch_page(page_token: str | None) -> dict:
        idx = 0 if page_token is None else int(page_token.split("_")[1])
        items = pages[idx]
        next_token = tokens[idx + 1] if idx + 1 < len(pages) else None
        return (
            {response_key: items, "nextPageToken": next_token}
            if next_token
            else {response_key: items}
        )

    return fetch_page


@pytest.mark.asyncio
async def test_async_page_iterator_yields_items():
    pages = [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    fetch = make_async_pages(pages)
    it = AsyncPageIterator(fetch, BaseResource)
    items = []
    async for item in it:
        items.append(item)
    assert len(items) == 3


@pytest.mark.asyncio
async def test_async_page_iterator_empty():
    fetch = make_async_pages([[]])
    it = AsyncPageIterator(fetch, BaseResource)
    items = []
    async for item in it:
        items.append(item)
    assert items == []


@pytest.mark.asyncio
async def test_async_page_iterator_pages():
    pages = [[{"id": "1"}, {"id": "2"}], [{"id": "3"}]]
    fetch = make_async_pages(pages)
    it = AsyncPageIterator(fetch, BaseResource)
    all_pages = []
    async for page in it.pages:
        all_pages.append(page)
    assert len(all_pages) == 2
    assert len(all_pages[0]) == 2
    assert len(all_pages[1]) == 1
