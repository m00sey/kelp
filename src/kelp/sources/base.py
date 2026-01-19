"""Abstract base class for data sources."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from kelp.cesr.events import Event


class DataSource(ABC):
    """Abstract base class for KEL data sources."""

    @abstractmethod
    async def fetch_events(self, identifier: str | None = None) -> list[Event]:
        """Fetch events, optionally filtered by identifier.

        Args:
            identifier: Optional AID to filter events by

        Returns:
            List of Event objects
        """
        pass

    @abstractmethod
    async def stream_events(self, identifier: str | None = None) -> AsyncIterator[Event]:
        """Stream events as they are fetched.

        Args:
            identifier: Optional AID to filter events by

        Yields:
            Event objects as they are parsed
        """
        pass

    @property
    @abstractmethod
    def source_description(self) -> str:
        """Human-readable description of this data source."""
        pass

    async def close(self) -> None:  # noqa: B027
        """Clean up any resources. Default implementation does nothing."""
