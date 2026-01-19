"""KERI LMDB database reader (Phase 3)."""

from collections.abc import AsyncIterator
from pathlib import Path

from kelp.cesr.events import Event

from .base import DataSource


class LMDBSource(DataSource):
    """Data source that reads KELs from KERI LMDB databases.

    Note: This is a placeholder for Phase 3 implementation.
    """

    def __init__(self, db_path: str | Path):
        """Initialize the LMDB data source.

        Args:
            db_path: Path to the KERI LMDB database directory
        """
        self.db_path = Path(db_path)

    @property
    def source_description(self) -> str:
        """Human-readable description of this data source."""
        return f"LMDB: {self.db_path.name}"

    async def fetch_events(self, identifier: str | None = None) -> list[Event]:
        """Fetch events from the LMDB database.

        Args:
            identifier: Optional AID to filter events by

        Returns:
            List of Event objects
        """
        raise NotImplementedError("LMDB source is not yet implemented (Phase 3)")

    async def stream_events(self, _identifier: str | None = None) -> AsyncIterator[Event]:
        """Stream events from the database.

        Args:
            identifier: Optional AID to filter events

        Yields:
            Event objects
        """
        raise NotImplementedError("LMDB source is not yet implemented (Phase 3)")
        yield  # Make this a generator
