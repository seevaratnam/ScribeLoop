"""Base repository protocol for data access abstraction."""

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    """Generic repository protocol for CRUD operations."""

    def get(self, id: str) -> T | None:
        """Get entity by ID."""
        ...

    def save(self, entity: T) -> None:
        """Save entity."""
        ...

    def delete(self, id: str) -> None:
        """Delete entity by ID."""
        ...

    def list_all(self) -> list[T]:
        """List all entities."""
        ...
