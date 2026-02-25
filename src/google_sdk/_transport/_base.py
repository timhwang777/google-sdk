"""Abstract transport protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Protocol for HTTP transport implementations."""

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Any:
        """Execute an HTTP request and return the response."""
        ...

    def close(self) -> None:
        """Close the transport and release resources."""
        ...


@runtime_checkable
class AsyncTransportProtocol(Protocol):
    """Protocol for async HTTP transport implementations."""

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Any:
        """Execute an async HTTP request and return the response."""
        ...

    async def close(self) -> None:
        """Close the transport and release resources."""
        ...
