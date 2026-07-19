from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.auth.dependencies import require_api_key
from app.compression import compress_upload
from app.models.schemas import UploadResponse
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/api/objects", tags=["objects"])


@router.post("", response_model=UploadResponse, dependencies=[Depends(require_api_key)])
async def upload_object(
    file: Annotated[UploadFile, File()],
    storage: Annotated[StorageBackend, Depends(get_storage_backend)],
    key: Annotated[str | None, Form()] = None,
) -> UploadResponse:
    object_key = key or file.filename
    if not object_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An object key or filename is required.",
        )

    data = file.file.read()
    content_type = file.content_type or "application/octet-stream"
    result = compress_upload(object_key, data, content_type)
    info = storage.put_object(result.key, result.data, result.content_type)
    savings_percent = (
        round((result.saved_bytes / result.original_size) * 100, 2)
        if result.original_size
        else 0
    )
    return UploadResponse(
        **asdict(info),
        original_key=result.original_key,
        original_size=result.original_size,
        compression=result.compression,
        saved_bytes=result.saved_bytes,
        savings_percent=savings_percent,
    )
