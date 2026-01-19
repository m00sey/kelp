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
    state = {"events": [], "source_url": "", "selected_index": 0}

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Render the main page."""
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "events": state["events"],
                "source_url": state["source_url"],
                "selected_index": state["selected_index"],
                "selected_event": (
                    state["events"][state["selected_index"]]
                    if state["events"] and state["selected_index"] < len(state["events"])
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

            # Sort events by sequence number
            events = sorted(events, key=lambda e: e.sequence)

            state["events"] = events
            state["source_url"] = oobi_url
            state["selected_index"] = 0

            return templates.TemplateResponse(
                "partials/main_content.html",
                {
                    "request": request,
                    "events": events,
                    "source_url": oobi_url,
                    "selected_index": 0,
                    "selected_event": events[0] if events else None,
                    "message": f"Loaded {len(events)} events",
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
        events = state["events"]
        if filter_type and filter_type != "all":
            events = [e for e in events if e.type == filter_type]

        # Sort by sequence number
        events = sorted(events, key=lambda e: e.sequence)

        return templates.TemplateResponse(
            "partials/event_list.html",
            {
                "request": request,
                "events": events,
                "selected_index": state["selected_index"],
                "filter_type": filter_type or "all",
            },
        )

    return app


# Create default app instance
app = create_app()
