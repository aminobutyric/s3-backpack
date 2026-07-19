from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import browse, delete, upload
from app.web import router as web_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Self-Hosted S3 Gateway",
    version="0.1.0",
    description="Garage-backed S3-compatible gateway with authenticated CRUD APIs.",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(upload.router)
app.include_router(browse.router)
app.include_router(delete.router)
app.include_router(web_router)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
