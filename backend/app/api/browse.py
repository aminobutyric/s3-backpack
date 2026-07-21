from dataclasses import asdict
from pathlib import PurePosixPath
from typing import Annotated
from urllib.parse import quote

import zstandard
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.auth.dependencies import require_api_key
from app.compression.metadata import parse_compression_metadata
from app.compression.text import decompress_text
from app.models.schemas import ObjectListResponse, ObjectResponse
from app.storage import StorageBackend, get_storage_backend

router = APIRouter(prefix="/api/objects", tags=["objects"])

MAX_DECOMPRESSED_DOWNLOAD_BYTES = 512 * 1024 * 1024


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
        stored = storage.get_object(key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Object not found: {key}",
        ) from exc

    data = stored.data
    content_type = stored.content_type
    download_key = key
    compression = parse_compression_metadata(stored.metadata)
    if compression and compression.method == "zstd":
        if compression.original_size > MAX_DECOMPRESSED_DOWNLOAD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Decompressed object exceeds the download size limit.",
            )
        try:
            data = decompress_text(data, compression.original_size)
        except zstandard.ZstdError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stored object could not be decompressed.",
            ) from exc
        if len(data) != compression.original_size:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stored object metadata does not match its content.",
            )
        content_type = compression.original_content_type
        download_key = compression.original_key

    filename = PurePosixPath(download_key).name or "download"
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"
        },
    )
