from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.auth.dependencies import require_api_key
from app.models.schemas import ObjectListResponse, ObjectResponse
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/api/objects", tags=["objects"])


@router.get("", response_model=ObjectListResponse, dependencies=[Depends(require_api_key)])
async def list_objects(
    storage: Annotated[StorageBackend, Depends(get_storage_backend)],
    prefix: Annotated[str, Query()] = "",
) -> ObjectListResponse:
    objects = storage.list_objects(prefix)
    return ObjectListResponse(objects=[ObjectResponse(**asdict(obj)) for obj in objects])


@router.get("/{key:path}", dependencies=[Depends(require_api_key)])
async def download_object(
    key: str,
    storage: Annotated[StorageBackend, Depends(get_storage_backend)],
) -> Response:
    try:
        data = storage.get_object(key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Object not found: {key}",
        ) from exc
    return Response(content=data, media_type="application/octet-stream")
