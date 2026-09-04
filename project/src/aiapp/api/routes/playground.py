"""A single-page playground served by the API itself: talk to the agent, approve tools, load documents, inspect memories.

The page is plain HTML and JavaScript with no build step. It calls the same
``/v1`` endpoints a real client would, with the bearer token typed into the
page, so nothing here bypasses authentication or tenant scoping.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["playground"])
PAGE = Path(__file__).resolve().parent.parent / "static" / "playground.html"


@router.get("/playground", include_in_schema=False, response_class=HTMLResponse)
async def playground() -> HTMLResponse:
    return HTMLResponse(PAGE.read_text(encoding="utf-8"))
