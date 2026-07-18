from fastapi import FastAPI

from app.api import browse, delete, upload

app = FastAPI(
    title="Self-Hosted S3 Gateway",
    version="0.1.0",
    description="Garage-backed S3-compatible gateway with authenticated CRUD APIs.",
)

app.include_router(upload.router)
app.include_router(browse.router)
app.include_router(delete.router)


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
