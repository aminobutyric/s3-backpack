import asyncio
from collections.abc import Mapping
from datetime import UTC, datetime
from io import BytesIO

import pytest
import zstandard
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.config import Settings, get_settings
from app.api.browse import download_object, list_objects
from app.api.delete import delete_object
from app.api.upload import upload_object
from app.auth.dependencies import require_api_key
from app.compression.metadata import build_compression_metadata
from app.storage.base import ObjectInfo, StorageBackend, StoredObject


class InMemoryStorage(StorageBackend):
    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        self.objects[key] = StoredObject(
            data=data,
            content_type=content_type,
            metadata=dict(metadata or {}),
        )
        return self._info(key)

    def get_object(self, key: str) -> StoredObject:
        try:
            return self.objects[key]
        except KeyError as exc:
            raise FileNotFoundError(key) from exc

    def list_objects(self, prefix: str = "") -> list[ObjectInfo]:
        return [self._info(key) for key in sorted(self.objects) if key.startswith(prefix)]

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def object_exists(self, key: str) -> bool:
        return key in self.objects

    def _info(self, key: str) -> ObjectInfo:
        return ObjectInfo(
            key=key,
            size=len(self.objects[key].data),
            last_modified=datetime(2026, 7, 18, tzinfo=UTC).isoformat(),
            etag=f"etag-{key}",
        )


@pytest.fixture
def storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        s3_endpoint_url="http://garage.test:3900",
        s3_access_key="access",
        s3_secret_key="secret",
        s3_bucket="default-bucket",
        api_key="test-api-key",
    )


def test_crud_api_requires_api_key(settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc:
        require_api_key(api_key=None, settings=settings)

    assert exc.value.status_code == 401


def test_crud_route_handlers_upload_list_download_delete(
    storage: InMemoryStorage,
) -> None:
    file = UploadFile(filename="readme.txt", file=BytesIO(b"hello garage"))

    upload = asyncio.run(
        upload_object(file=file, storage=storage, key="docs/readme.txt")
    )
    assert upload.key == "docs/readme.txt"
    assert upload.size == 12

    listed = asyncio.run(list_objects(storage=storage, prefix="docs/"))
    assert [obj.key for obj in listed.objects] == ["docs/readme.txt"]

    downloaded = asyncio.run(download_object(key="docs/readme.txt", storage=storage))
    assert downloaded.body == b"hello garage"

    deleted = asyncio.run(delete_object(key="docs/readme.txt", storage=storage))
    assert deleted.key == "docs/readme.txt"
    assert deleted.deleted is True

    with pytest.raises(HTTPException) as exc:
        asyncio.run(download_object(key="docs/readme.txt", storage=storage))
    assert exc.value.status_code == 404


def test_upload_compresses_text_and_reports_actual_stored_object(
    storage: InMemoryStorage,
) -> None:
    original = b"same structured log record\n" * 400
    file = UploadFile(filename="events.log", file=BytesIO(original))

    uploaded = asyncio.run(upload_object(file=file, storage=storage, key=None))

    assert uploaded.key == "events.log.zst"
    assert uploaded.original_key == "events.log"
    assert uploaded.original_size == len(original)
    stored = storage.objects["events.log.zst"]
    assert uploaded.size == len(stored.data)
    assert uploaded.compression == "zstd"
    assert uploaded.saved_bytes == uploaded.original_size - uploaded.size
    assert uploaded.savings_percent > 90
    assert zstandard.ZstdDecompressor().decompress(stored.data) == original
    assert stored.metadata["s3gw-compression"] == "zstd"
    assert stored.metadata["s3gw-original-key"] == "events.log"


def test_download_transparently_decompresses_gateway_zstd(
    storage: InMemoryStorage,
) -> None:
    original = b"same structured log record\n" * 400
    file = UploadFile(
        filename="events.log",
        file=BytesIO(original),
        headers=Headers({"content-type": "text/plain; charset=utf-8"}),
    )
    uploaded = asyncio.run(upload_object(file=file, storage=storage, key=None))

    downloaded = asyncio.run(download_object(key=uploaded.key, storage=storage))

    assert downloaded.body == original
    assert downloaded.headers["content-type"] == "text/plain; charset=utf-8"
    assert downloaded.headers["content-disposition"] == (
        "attachment; filename*=UTF-8''events.log"
    )


def test_download_leaves_legacy_zstd_without_metadata_compressed(
    storage: InMemoryStorage,
) -> None:
    compressed = zstandard.ZstdCompressor(level=3).compress(b"legacy content")
    storage.put_object("legacy.txt.zst", compressed, "application/zstd")

    downloaded = asyncio.run(
        download_object(key="legacy.txt.zst", storage=storage)
    )

    assert downloaded.body == compressed
    assert downloaded.headers["content-type"] == "application/zstd"
    assert downloaded.headers["content-disposition"] == (
        "attachment; filename*=UTF-8''legacy.txt.zst"
    )


def test_download_rejects_corrupt_gateway_zstd(storage: InMemoryStorage) -> None:
    metadata = build_compression_metadata(
        method="zstd",
        original_key="broken.txt",
        original_content_type="text/plain",
        original_size=100,
    )
    storage.put_object("broken.txt.zst", b"not zstd", "application/zstd", metadata)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(download_object(key="broken.txt.zst", storage=storage))

    assert exc.value.status_code == 500
