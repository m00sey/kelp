"""Local CESR file reader (Phase 2)."""

from collections.abc import AsyncIterator
from pathlib import Path

from kelp.cesr.events import Event
from kelp.cesr.parser import CESRParser

from .base import DataSource


class FileSource(DataSource):
    """Data source that reads KELs from local CESR files."""

    def __init__(self, file_path: str | Path):
        """Initialize the file data source.

        Args:
            file_path: Path to the CESR file
        """
        self.file_path = Path(file_path)
        self._parser = CESRParser()

    @property
    def source_description(self) -> str:
        """Human-readable description of this data source."""
        return f"File: {self.file_path.name}"

    async def fetch_events(self, identifier: str | None = None) -> list[Event]:
        """Read and parse events from the CESR file.

        Args:
            identifier: Optional AID to filter events by

        Returns:
            List of Event objects
        """
        data = self.file_path.read_bytes()
        events = self._parser.parse(data)

        if identifier:
            events = [e for e in events if e.identifier == identifier]

        return events

    async def stream_events(self, identifier: str | None = None) -> AsyncIterator[Event]:
        """Stream events from the file.

        Args:
            identifier: Optional AID to filter events

        Yields:
            Event objects
        """
        events = await self.fetch_events(identifier)
        for event in events:
            yield event
