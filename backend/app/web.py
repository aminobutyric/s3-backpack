from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(include_in_schema=False)

@router.get("/", response_class=HTMLResponse)
async def object_browser(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="browse.html",
        context={},
    )