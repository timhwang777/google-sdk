"""Tests for BaseResource and PageResponse models."""

from google_sdk._models.base import BaseResource, PageResponse


def test_base_resource_defaults():
    r = BaseResource()
    assert r.id == ""
    assert r.kind is None


def test_base_resource_extra_fields():
    """BaseResource should accept unknown fields."""
    r = BaseResource(id="1", kind="drive#file", unknownField="hello")
    assert r.id == "1"
    assert r.kind == "drive#file"


def test_base_resource_populate_by_name():
    """BaseResource should accept both snake_case and camelCase."""
    r = BaseResource.model_validate({"id": "1", "kind": "drive#file"})
    assert r.id == "1"


def test_page_response_defaults():
    pr = PageResponse[BaseResource](items=[])
    assert pr.items == []
    assert pr.next_page_token is None


def test_page_response_next_page_token_alias():
    """nextPageToken alias should be accepted."""
    data = {"items": [], "nextPageToken": "abc123"}
    pr = PageResponse[BaseResource].model_validate(data)
    assert pr.next_page_token == "abc123"


def test_page_response_with_items():
    items = [BaseResource(id="1"), BaseResource(id="2")]
    pr = PageResponse[BaseResource](items=items)
    assert len(pr.items) == 2
    assert pr.items[0].id == "1"
