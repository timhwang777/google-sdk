"""Token storage backends for OAuth credentials."""

from __future__ import annotations

import json
import os
import stat
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from google_sdk.exceptions import TokenStoreError

DEFAULT_TOKEN_PATH = Path.home() / ".config" / "google-sdk" / "tokens.json"


class TokenData(BaseModel):
    """Serializable token representation."""

    token: str
    refresh_token: str | None = None
    token_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] = Field(default_factory=list)
    expiry: datetime | None = None


class TokenStore(ABC):
    """Abstract base class for token storage backends."""

    @abstractmethod
    def load(self, key: str) -> TokenData | None:
        """Load token data for the given key."""

    @abstractmethod
    def save(self, key: str, token: TokenData) -> None:
        """Save token data under the given key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete token data for the given key."""


class FileTokenStore(TokenStore):
    """Default token store — persists tokens to a JSON file.

    File is created with 0o600 permissions (owner read/write only).
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path else DEFAULT_TOKEN_PATH

    def _load_all(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise TokenStoreError(f"Failed to read token store: {e}") from e

    def _save_all(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, default=str))
        os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)

    def load(self, key: str) -> TokenData | None:
        data = self._load_all()
        raw = data.get(key)
        if raw is None:
            return None
        return TokenData.model_validate(raw)

    def save(self, key: str, token: TokenData) -> None:
        data = self._load_all()
        data[key] = token.model_dump(mode="json")
        self._save_all(data)

    def delete(self, key: str) -> None:
        data = self._load_all()
        data.pop(key, None)
        self._save_all(data)


class EnvTokenStore(TokenStore):
    """Read-only token store that loads from environment variables.

    Environment variable format: GOOGLE_TOKEN_<KEY>=<json>
    """

    def load(self, key: str) -> TokenData | None:
        env_key = f"GOOGLE_TOKEN_{key.upper().replace('-', '_').replace('/', '_')}"
        raw = os.environ.get(env_key)
        if raw is None:
            return None
        try:
            return TokenData.model_validate(json.loads(raw))
        except (json.JSONDecodeError, Exception) as e:
            raise TokenStoreError(f"Failed to parse token from env {env_key}: {e}") from e

    def save(self, key: str, token: TokenData) -> None:
        raise TokenStoreError("EnvTokenStore is read-only — cannot save tokens")

    def delete(self, key: str) -> None:
        raise TokenStoreError("EnvTokenStore is read-only — cannot delete tokens")


class KeyringTokenStore(TokenStore):
    """Optional token store backed by the system keyring.

    Requires: pip install google-sdk[keyring]
    """

    SERVICE_NAME = "google-sdk"

    def __init__(self) -> None:
        try:
            import keyring  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "KeyringTokenStore requires the 'keyring' package. "
                "Install it with: pip install google-sdk[keyring]"
            ) from e

    def load(self, key: str) -> TokenData | None:
        import keyring

        raw = keyring.get_password(self.SERVICE_NAME, key)
        if raw is None:
            return None
        return TokenData.model_validate(json.loads(raw))

    def save(self, key: str, token: TokenData) -> None:
        import keyring

        keyring.set_password(self.SERVICE_NAME, key, json.dumps(token.model_dump(mode="json")))

    def delete(self, key: str) -> None:
        import keyring

        keyring.delete_password(self.SERVICE_NAME, key)
