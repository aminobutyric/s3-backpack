import asyncio
from pathlib import Path

from starlette.requests import Request

from app.main import app
from app.ui.routes import index


def test_object_browser_and_static_assets_are_served() -> None:
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "root_path": "",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "router": app.router,
        }
    )

    page = asyncio.run(index(request))
    html = page.body.decode()
    static_dir = Path(__file__).resolve().parent.parent / "app" / "static"
    stylesheet = (static_dir / "style.css").read_text()
    script = (static_dir / "app.js").read_text()

    assert page.status_code == 200
    assert "S3 Backpack" in html
    assert "API key" in html
    assert "/static/style.css" in html
    assert "/static/app.js" in html
    assert ".objects-table" in stylesheet
    assert "X-API-Key" in script
    assert "sessionStorage" in script
    assert "localStorage" not in script
    assert 'type="file" multiple' in html
