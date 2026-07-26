from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import browse, delete, disks, upload
from app.ui.routes import router as ui_router

app = FastAPI(
    title="S3 Backpack",
    version="0.2.0",
    description="Build and verify portable local mirrors of cloud S3 data.",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(ui_router)
app.include_router(upload.router)
app.include_router(browse.router)
app.include_router(delete.router)
app.include_router(disks.router)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
