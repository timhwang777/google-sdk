"""Contract tests for auth public API."""

import inspect

from google_sdk.auth import oauth, service_account
from google_sdk.auth.token_store import TokenStore


def test_service_account_signature():
    sig = inspect.signature(service_account)
    params = sig.parameters
    assert "key_path" in params
    assert "scopes" in params
    assert "subject" in params


def test_oauth_signature():
    sig = inspect.signature(oauth)
    params = sig.parameters
    assert "client_secrets" in params
    assert "scopes" in params
    assert "token_store" in params


def test_token_store_abc_has_required_methods():
    abstract_methods = TokenStore.__abstractmethods__
    assert "load" in abstract_methods
    assert "save" in abstract_methods
    assert "delete" in abstract_methods


def test_token_store_load_signature():
    sig = inspect.signature(TokenStore.load)
    assert "key" in sig.parameters


def test_token_store_save_signature():
    sig = inspect.signature(TokenStore.save)
    assert "key" in sig.parameters
    assert "token" in sig.parameters


def test_token_store_delete_signature():
    sig = inspect.signature(TokenStore.delete)
    assert "key" in sig.parameters
