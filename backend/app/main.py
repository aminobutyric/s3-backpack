from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import browse, delete, upload
from app.ui.routes import router as ui_router

app = FastAPI(
    title="Self-Hosted S3 Gateway",
    version="0.1.0",
    description="Garage-backed S3-compatible gateway with authenticated CRUD APIs.",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(ui_router)
app.include_router(upload.router)
app.include_router(browse.router)
app.include_router(delete.router)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
