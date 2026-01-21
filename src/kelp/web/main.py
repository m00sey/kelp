"""FastAPI application for KELP web UI."""

import json
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kelp.sources.oobi import OOBIFetchError, OOBISource


@dataclass
class TabState:
    """State for a single tab."""

    id: str
    name: str  # Display name (hostname from URL)
    events: list = field(default_factory=list)
    source_url: str = ""
    selected_index: int = 0
    is_witness: bool = False
    show_all_aids: bool = False
    url_aid: str | None = None

    @property
    def max_sequence(self) -> int | None:
        """Get the maximum sequence number from events."""
        if not self.events:
            return None
        return max(e.sequence for e in self.events)


@dataclass
class AppState:
    """Global application state managing multiple tabs."""

    tabs: dict[str, TabState] = field(default_factory=dict)
    active_tab_id: str | None = None
    tab_order: list[str] = field(default_factory=list)

    def get_active_tab(self) -> TabState | None:
        """Get the currently active tab."""
        if self.active_tab_id and self.active_tab_id in self.tabs:
            return self.tabs[self.active_tab_id]
        return None

    def create_tab(self, name: str = "New Tab") -> TabState:
        """Create a new tab and make it active."""
        tab_id = str(uuid.uuid4())[:8]
        tab = TabState(id=tab_id, name=name)
        self.tabs[tab_id] = tab
        self.tab_order.append(tab_id)
        self.active_tab_id = tab_id
        return tab

    def close_tab(self, tab_id: str) -> str | None:
        """Close a tab and return the ID of the new active tab."""
        if tab_id not in self.tabs or len(self.tabs) <= 1:
            return self.active_tab_id

        # Find adjacent tab to switch to
        idx = self.tab_order.index(tab_id)
        del self.tabs[tab_id]
        self.tab_order.remove(tab_id)

        # Switch to previous tab, or first if closing first tab
        new_idx = max(0, idx - 1)
        self.active_tab_id = self.tab_order[new_idx]
        return self.active_tab_id

    def get_tabs_in_order(self) -> list[TabState]:
        """Get tabs in display order."""
        return [self.tabs[tid] for tid in self.tab_order if tid in self.tabs]


def _tab_name_from_url(url: str) -> str:
    """Extract hostname from URL for tab name."""
    try:
        parsed = urlparse(url)
        if parsed.hostname:
            return parsed.hostname
    except Exception:
        pass
    return "New Tab"


def jq_filter_match(jq_expr: str, data: dict) -> bool:
    """Check if data matches a jq filter expression."""
    try:
        result = subprocess.run(
            ["jq", "-e", jq_expr],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            timeout=1,
        )
        # -e flag makes jq exit with 1 if result is false/null
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="KELP",
        description="Key Event Log Parser - Browse KERI Key Event Logs",
        version="0.1.0",
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Templates
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    # Add custom filters to Jinja2
    templates.env.filters["tojson_pretty"] = lambda x: json.dumps(x, indent=2)

    # In-memory state with multi-tab support
    state = AppState()
    # Create initial tab
    state.create_tab()

    def _is_witness_url(url: str) -> bool:
        """Check if the OOBI URL is a witness endpoint."""
        return url.rstrip("/").endswith("/witness")

    def _group_events_by_aid(events: list, all_events: list | None = None) -> dict:
        """Group events by their AID (identifier).

        Args:
            events: Events to group
            all_events: If provided, indices will reference this list instead
        """
        # Build index lookup if we have the full list
        index_lookup = {}
        if all_events:
            for i, e in enumerate(all_events):
                index_lookup[id(e)] = i

        grouped = {}
        for i, event in enumerate(events):
            aid = event.identifier
            # Events without identifier (like rpy) use their type label
            if not aid:
                label = event.type_label
                # Handle irregular plurals
                if label.endswith("y"):
                    aid = f"{label[:-1]}ies"
                else:
                    aid = f"{label}s"
            if aid not in grouped:
                grouped[aid] = []
            # Use original index if available, otherwise use enumerated index
            idx = index_lookup.get(id(event), i)
            grouped[aid].append({"event": event, "index": idx})
        return grouped

    def _get_display_events(tab: TabState) -> list:
        """Get events filtered by show_all_aids setting for a tab."""
        events = tab.events
        if tab.is_witness and tab.url_aid and not tab.show_all_aids:
            events = [e for e in events if e.identifier == tab.url_aid]
        return sorted(events, key=lambda e: e.sequence)

    def _get_tab_context(tab: TabState, request: Request) -> dict:
        """Build template context for a tab."""
        display_events = _get_display_events(tab)
        return {
            "request": request,
            "events": display_events,
            "events_by_aid": _group_events_by_aid(display_events, tab.events) if tab.is_witness else None,
            "is_witness": tab.is_witness,
            "show_all_aids": tab.show_all_aids,
            "url_aid": tab.url_aid,
            "source_url": tab.source_url,
            "selected_index": tab.selected_index,
            "selected_event": (
                display_events[tab.selected_index]
                if display_events and tab.selected_index < len(display_events)
                else None
            ),
            "tabs": state.get_tabs_in_order(),
            "active_tab_id": state.active_tab_id,
        }

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Render the main page."""
        # Ensure at least one tab exists
        if not state.tabs:
            state.create_tab()
        tab = state.get_active_tab()
        return templates.TemplateResponse(
            "index.html",
            _get_tab_context(tab, request),
        )

    @app.post("/load", response_class=HTMLResponse)
    async def load_oobi(request: Request, oobi_url: str = Form(...)):
        """Load events from an OOBI URL into the active tab."""
        oobi_url = oobi_url.strip()
        tab = state.get_active_tab()
        try:
            source = OOBISource(oobi_url)
            events = await source.fetch_events()
            await source.close()

            # Update tab state
            tab.events = sorted(events, key=lambda e: e.sequence)
            tab.source_url = oobi_url
            tab.selected_index = 0
            tab.is_witness = _is_witness_url(oobi_url)
            tab.show_all_aids = False
            tab.url_aid = source.identifier
            tab.name = _tab_name_from_url(oobi_url)

            # Get filtered display events
            display_events = _get_display_events(tab)

            # Build response with OOB tab bar update
            context = _get_tab_context(tab, request)
            context["message"] = f"Loaded {len(display_events)} events"

            return templates.TemplateResponse(
                "partials/main_content_with_tab_bar.html",
                context,
            )
        except OOBIFetchError as e:
            return templates.TemplateResponse(
                "partials/error.html",
                {"request": request, "error": str(e)},
            )
        except Exception as e:
            return templates.TemplateResponse(
                "partials/error.html",
                {"request": request, "error": str(e)},
            )

    @app.get("/event/{index}", response_class=HTMLResponse)
    async def get_event(request: Request, index: int):
        """Get event detail by index in the active tab."""
        tab = state.get_active_tab()
        if 0 <= index < len(tab.events):
            tab.selected_index = index
            event = tab.events[index]
            return templates.TemplateResponse(
                "partials/event_detail.html",
                {"request": request, "event": event, "index": index},
            )
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "Event not found"},
        )

    @app.get("/events", response_class=HTMLResponse)
    async def get_events(
        request: Request,
        filter_type: str | None = None,
        jq_filter: str | None = None,
    ):
        """Get filtered event list for the active tab."""
        tab = state.get_active_tab()
        events = _get_display_events(tab)
        if filter_type and filter_type != "all":
            events = [e for e in events if e.type == filter_type]

        # Apply jq filter if provided
        if jq_filter and jq_filter.strip():
            filtered = []
            for event in events:
                if jq_filter_match(jq_filter, event.data):
                    filtered.append(event)
            events = filtered

        return templates.TemplateResponse(
            "partials/event_list.html",
            {
                "request": request,
                "events": events,
                "events_by_aid": _group_events_by_aid(events, tab.events) if tab.is_witness else None,
                "is_witness": tab.is_witness,
                "show_all_aids": tab.show_all_aids,
                "selected_index": tab.selected_index,
                "filter_type": filter_type or "all",
                "jq_filter": jq_filter or "",
            },
        )

    @app.post("/toggle-all-aids", response_class=HTMLResponse)
    async def toggle_all_aids(request: Request):
        """Toggle showing all AIDs for witness endpoints in the active tab."""
        tab = state.get_active_tab()
        tab.show_all_aids = not tab.show_all_aids
        tab.selected_index = 0

        return templates.TemplateResponse(
            "partials/main_content.html",
            _get_tab_context(tab, request),
        )

    @app.post("/clear", response_class=HTMLResponse)
    async def clear_events(request: Request):
        """Clear loaded events in the active tab and return to empty state."""
        tab = state.get_active_tab()
        tab.events = []
        tab.source_url = ""
        tab.selected_index = 0
        tab.is_witness = False
        tab.show_all_aids = False
        tab.url_aid = None
        tab.name = "New Tab"

        return templates.TemplateResponse(
            "partials/main_content_with_tab_bar.html",
            _get_tab_context(tab, request),
        )

    # Tab management endpoints
    @app.post("/tab/new", response_class=HTMLResponse)
    async def new_tab(request: Request):
        """Create a new tab and make it active."""
        tab = state.create_tab()
        return templates.TemplateResponse(
            "partials/tab_content.html",
            _get_tab_context(tab, request),
        )

    @app.get("/tab/{tab_id}", response_class=HTMLResponse)
    async def switch_tab(request: Request, tab_id: str):
        """Switch to an existing tab."""
        if tab_id in state.tabs:
            state.active_tab_id = tab_id
        tab = state.get_active_tab()
        return templates.TemplateResponse(
            "partials/tab_content.html",
            _get_tab_context(tab, request),
        )

    @app.post("/tab/{tab_id}/close", response_class=HTMLResponse)
    async def close_tab(request: Request, tab_id: str):
        """Close a tab and switch to an adjacent one."""
        state.close_tab(tab_id)
        tab = state.get_active_tab()
        return templates.TemplateResponse(
            "partials/tab_content.html",
            _get_tab_context(tab, request),
        )

    return app


# Create default app instance
app = create_app()
