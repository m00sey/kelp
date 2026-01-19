"""FastAPI application for KELP web UI."""

import json
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from kelp.sources.oobi import OOBIFetchError, OOBISource

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

    # In-memory state (for simplicity; could use session/cache)
    state = {
        "events": [],
        "source_url": "",
        "selected_index": 0,
        "is_witness": False,
        "show_all_aids": False,
        "url_aid": None,  # AID extracted from URL
    }

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

    def _get_display_events() -> list:
        """Get events filtered by show_all_aids setting."""
        events = state["events"]
        if state["is_witness"] and state["url_aid"] and not state["show_all_aids"]:
            events = [e for e in events if e.identifier == state["url_aid"]]
        return sorted(events, key=lambda e: e.sequence)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Render the main page."""
        display_events = _get_display_events()
        is_witness = state["is_witness"]
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "events": display_events,
                "events_by_aid": _group_events_by_aid(display_events, state["events"]) if is_witness else None,
                "is_witness": is_witness,
                "show_all_aids": state["show_all_aids"],
                "url_aid": state["url_aid"],
                "source_url": state["source_url"],
                "selected_index": state["selected_index"],
                "selected_event": (
                    display_events[state["selected_index"]]
                    if display_events and state["selected_index"] < len(display_events)
                    else None
                ),
            },
        )

    @app.post("/load", response_class=HTMLResponse)
    async def load_oobi(request: Request, oobi_url: str = Form(...)):
        """Load events from an OOBI URL."""
        try:
            source = OOBISource(oobi_url)
            events = await source.fetch_events()
            await source.close()

            # Update state
            state["events"] = sorted(events, key=lambda e: e.sequence)
            state["source_url"] = oobi_url
            state["selected_index"] = 0
            state["is_witness"] = _is_witness_url(oobi_url)
            state["show_all_aids"] = False
            state["url_aid"] = source.identifier

            # Get filtered display events
            display_events = _get_display_events()
            is_witness = state["is_witness"]

            return templates.TemplateResponse(
                "partials/main_content.html",
                {
                    "request": request,
                    "events": display_events,
                    "events_by_aid": _group_events_by_aid(display_events, state["events"]) if is_witness else None,
                    "is_witness": is_witness,
                    "show_all_aids": state["show_all_aids"],
                    "url_aid": state["url_aid"],
                    "source_url": oobi_url,
                    "selected_index": 0,
                    "selected_event": display_events[0] if display_events else None,
                    "message": f"Loaded {len(display_events)} events",
                },
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
        """Get event detail by index."""
        if 0 <= index < len(state["events"]):
            state["selected_index"] = index
            event = state["events"][index]
            return templates.TemplateResponse(
                "partials/event_detail.html",
                {"request": request, "event": event, "index": index},
            )
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "Event not found"},
        )

    @app.get("/events", response_class=HTMLResponse)
    async def get_events(request: Request, filter_type: str | None = None):
        """Get filtered event list."""
        events = _get_display_events()
        if filter_type and filter_type != "all":
            events = [e for e in events if e.type == filter_type]

        is_witness = state["is_witness"]
        return templates.TemplateResponse(
            "partials/event_list.html",
            {
                "request": request,
                "events": events,
                "events_by_aid": _group_events_by_aid(events, state["events"]) if is_witness else None,
                "is_witness": is_witness,
                "show_all_aids": state["show_all_aids"],
                "selected_index": state["selected_index"],
                "filter_type": filter_type or "all",
            },
        )

    @app.post("/toggle-all-aids", response_class=HTMLResponse)
    async def toggle_all_aids(request: Request):
        """Toggle showing all AIDs for witness endpoints."""
        state["show_all_aids"] = not state["show_all_aids"]
        state["selected_index"] = 0

        display_events = _get_display_events()
        is_witness = state["is_witness"]

        return templates.TemplateResponse(
            "partials/main_content.html",
            {
                "request": request,
                "events": display_events,
                "events_by_aid": _group_events_by_aid(display_events, state["events"]) if is_witness else None,
                "is_witness": is_witness,
                "show_all_aids": state["show_all_aids"],
                "url_aid": state["url_aid"],
                "source_url": state["source_url"],
                "selected_index": 0,
                "selected_event": display_events[0] if display_events else None,
            },
        )

    return app


# Create default app instance
app = create_app()
