"""Service registry for google-sdk."""

from __future__ import annotations


class ServiceRegistry:
    """Registry for SDK service classes."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a service class."""

        def decorator(service_cls: type) -> type:
            cls._registry[name] = service_cls
            return service_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> type | None:
        return cls._registry.get(name)

    @classmethod
    def all(cls) -> dict[str, type]:
        return dict(cls._registry)
