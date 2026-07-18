import asyncio
from datetime import UTC, datetime
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.config import Settings, get_settings
from app.api.browse import download_object, list_objects
from app.api.delete import delete_object
from app.api.upload import upload_object
from app.auth.dependencies import require_api_key
from app.storage.base import ObjectInfo, StorageBackend


class InMemoryStorage(StorageBackend):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put_object(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> ObjectInfo:
        self.objects[key] = data
        return self._info(key)

    def get_object(self, key: str) -> bytes:
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
            size=len(self.objects[key]),
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
