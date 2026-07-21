from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

# Tabs live here as data, not markup — add a tab by adding a line, no other
# file needs to change unless the tab needs its own panel template.
TABS = [
    {"id": "browse", "label": "Browse"},
    {"id": "upload", "label": "Upload"},
]


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"tabs": TABS, "active_tab": TABS[0]["id"]},
    )
