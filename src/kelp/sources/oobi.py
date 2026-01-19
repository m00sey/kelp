"""OOBI HTTP data source for fetching KELs from witnesses/watchers."""

import re
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx

from kelp.cesr.events import Event
from kelp.cesr.parser import CESRParser

from .base import DataSource


class OOBISource(DataSource):
    """Data source that fetches KELs via OOBI endpoints."""

    def __init__(self, oobi_url: str, timeout: float = 30.0):
        """Initialize the OOBI data source.

        Args:
            oobi_url: The OOBI URL to fetch from
            timeout: HTTP request timeout in seconds
        """
        self.oobi_url = oobi_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._aid = self._extract_aid(oobi_url)
        self._parser = CESRParser()

    def _extract_aid(self, url: str) -> str | None:
        """Extract the AID from an OOBI URL."""
        # OOBI URLs typically have format: /oobi/{aid}/... or /oobi/{aid}
        match = re.search(r"/oobi/([A-Za-z0-9_-]{44})", url)
        if match:
            return match.group(1)
        return None

    @property
    def identifier(self) -> str | None:
        """The identifier this OOBI is for."""
        return self._aid

    @property
    def source_description(self) -> str:
        """Human-readable description of this data source."""
        parsed = urlparse(self.oobi_url)
        host = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
        if self._aid:
            return f"OOBI: {host} ({self._aid[:16]}...)"
        return f"OOBI: {host}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def fetch_events(self, identifier: str | None = None) -> list[Event]:
        """Fetch all events from the OOBI endpoint.

        Args:
            identifier: Optional AID to filter events (ignored for OOBI,
                        as the OOBI URL already specifies the identifier)

        Returns:
            List of Event objects
        """
        client = await self._get_client()

        try:
            response = await client.get(self.oobi_url)
            response.raise_for_status()

            # Parse the CESR response
            data = response.content
            events = self._parser.parse(data)

            # Filter by identifier if specified
            if identifier:
                events = [e for e in events if e.identifier == identifier]

            return events

        except httpx.HTTPStatusError as e:
            raise OOBIFetchError(f"HTTP error fetching OOBI: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise OOBIFetchError(f"Request error fetching OOBI: {e}") from e

    async def stream_events(self, identifier: str | None = None) -> AsyncIterator[Event]:
        """Stream events as they are parsed.

        Note: For HTTP OOBI, this is not truly streaming - we fetch all
        data first, then yield events. True streaming would require SSE
        or WebSocket support.

        Args:
            identifier: Optional AID to filter events

        Yields:
            Event objects
        """
        events = await self.fetch_events(identifier)
        for event in events:
            yield event

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "OOBISource":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class OOBIFetchError(Exception):
    """Error fetching from OOBI endpoint."""

    pass
