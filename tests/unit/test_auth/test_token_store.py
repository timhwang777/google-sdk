"""Tests for TokenStore implementations."""

import json
import stat

import pytest

from google_sdk.auth.token_store import EnvTokenStore, FileTokenStore, TokenData, TokenStore
from google_sdk.exceptions import TokenStoreError


def make_token(**kwargs) -> TokenData:
    defaults = {
        "token": "tok_abc",
        "refresh_token": "refresh_xyz",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client123",
        "client_secret": "secret456",
        "scopes": ["https://www.googleapis.com/auth/drive"],
        "expiry": None,
    }
    defaults.update(kwargs)
    return TokenData(**defaults)


# ── TokenStore ABC ──────────────────────────────────────────────────────────


def test_token_store_is_abstract():
    with pytest.raises(TypeError):
        TokenStore()  # type: ignore


# ── FileTokenStore ──────────────────────────────────────────────────────────


def test_file_token_store_save_load(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    token = make_token()
    store.save("key1", token)
    loaded = store.load("key1")
    assert loaded is not None
    assert loaded.token == "tok_abc"
    assert loaded.refresh_token == "refresh_xyz"


def test_file_token_store_creates_parent_dirs(tmp_path):
    path = tmp_path / "subdir" / "tokens.json"
    store = FileTokenStore(path)
    store.save("k", make_token())
    assert path.exists()


def test_file_token_store_permissions(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.save("k", make_token())
    mode = oct(stat.S_IMODE(path.stat().st_mode))
    assert mode == oct(0o600)


def test_file_token_store_missing_key_returns_none(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    assert store.load("nonexistent") is None


def test_file_token_store_missing_file_returns_none(tmp_path):
    path = tmp_path / "nonexistent.json"
    store = FileTokenStore(path)
    assert store.load("key") is None


def test_file_token_store_delete(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    token = make_token()
    store.save("key1", token)
    store.delete("key1")
    assert store.load("key1") is None


def test_file_token_store_scope_keyed(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    t1 = make_token(token="tok1")
    t2 = make_token(token="tok2")
    store.save("scope1", t1)
    store.save("scope2", t2)
    assert store.load("scope1").token == "tok1"
    assert store.load("scope2").token == "tok2"


# ── EnvTokenStore ────────────────────────────────────────────────────────────


def test_env_token_store_load(monkeypatch):
    token = make_token()
    monkeypatch.setenv("GOOGLE_TOKEN_KEY1", json.dumps(token.model_dump(mode="json")))
    store = EnvTokenStore()
    loaded = store.load("key1")
    assert loaded is not None
    assert loaded.token == "tok_abc"


def test_env_token_store_missing_returns_none(monkeypatch):
    store = EnvTokenStore()
    assert store.load("does_not_exist") is None


def test_env_token_store_save_raises():
    store = EnvTokenStore()
    with pytest.raises(TokenStoreError, match="read-only"):
        store.save("key", make_token())


def test_env_token_store_delete_raises():
    store = EnvTokenStore()
    with pytest.raises(TokenStoreError, match="read-only"):
        store.delete("key")
