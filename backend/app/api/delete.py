from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_api_key
from app.models.schemas import DeleteResponse
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/api/objects", tags=["objects"])


@router.delete("/{key:path}", response_model=DeleteResponse, dependencies=[Depends(require_api_key)])
async def delete_object(
    key: str,
    storage: Annotated[StorageBackend, Depends(get_storage_backend)],
) -> DeleteResponse:
    storage.delete_object(key)
    return DeleteResponse(key=key)
