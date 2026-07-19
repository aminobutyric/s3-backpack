import asyncio
from pathlib import Path

from starlette.requests import Request

from app.main import app
from app.web import object_browser


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

    page = asyncio.run(object_browser(request))
    html = page.body.decode()
    static_dir = Path(__file__).resolve().parent.parent / "static"
    stylesheet = (static_dir / "app.css").read_text()
    script = (static_dir / "app.js").read_text()

    assert page.status_code == 200
    assert "S3 Gateway" in html
    assert "Connect to gateway" in html
    assert "/static/app.css" in html
    assert "/static/app.js" in html
    assert ".object-section" in stylesheet
    assert "X-API-Key" in script
    assert "sessionStorage" in script
