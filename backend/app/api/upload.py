from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.auth.dependencies import require_api_key
from app.models.schemas import ObjectResponse
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/api/objects", tags=["objects"])


@router.post("", response_model=ObjectResponse, dependencies=[Depends(require_api_key)])
async def upload_object(
    file: Annotated[UploadFile, File()],
    storage: Annotated[StorageBackend, Depends(get_storage_backend)],
    key: Annotated[str | None, Form()] = None,
) -> ObjectResponse:
    object_key = key or file.filename
    data = file.file.read()
    content_type = file.content_type or "application/octet-stream"
    info = storage.put_object(object_key, data, content_type)
    return ObjectResponse(**asdict(info))
