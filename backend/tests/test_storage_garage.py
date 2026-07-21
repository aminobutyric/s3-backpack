"""
Integration tests for the Garage storage backend.

Run against a real Garage instance:
    ./scripts/init-garage-config.sh   # first time only
    docker compose up -d garage
    cp .env.example .env              # then fill in real values
    pytest backend/tests/test_storage_garage.py

Tests are skipped automatically if S3_ACCESS_KEY / S3_SECRET_KEY aren't set
in the environment, so `pytest` still passes cleanly without Garage running —
the real coverage only happens with Garage up and .env sourced.
"""

import os
import uuid
from datetime import UTC, datetime
from io import BytesIO

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from app.storage.base import ObjectInfo, StoredObject
from app.storage.garage import GarageBackend

TEST_BUCKET = "default-bucket"


@pytest.fixture
def backend() -> GarageBackend:
    return GarageBackend(
        endpoint_url="http://garage.test:3900",
        access_key="test-access-key",
        secret_key="test-secret-key",
        bucket=TEST_BUCKET,
    )


@pytest.fixture
def stubber(backend: GarageBackend):
    with Stubber(backend._client) as stub:
        yield stub


@pytest.fixture
def test_key() -> str:
    return f"test/{uuid.uuid4()}.txt"


def test_put_object_returns_head_metadata(backend, stubber, test_key):
    modified = datetime(2026, 7, 18, 12, 30, tzinfo=UTC)
    stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": TEST_BUCKET,
            "Key": test_key,
            "Body": b"hello garage",
            "ContentType": "text/plain",
        },
    )
    stubber.add_response(
        "head_object",
        {
            "ContentLength": 12,
            "LastModified": modified,
            "ETag": '"abc123"',
        },
        {"Bucket": TEST_BUCKET, "Key": test_key},
    )

    result = backend.put_object(test_key, b"hello garage", content_type="text/plain")

    assert result == ObjectInfo(
        key=test_key,
        size=12,
        last_modified=modified.isoformat(),
        etag="abc123",
    )


def test_put_object_sends_user_metadata(backend, stubber, test_key):
    modified = datetime(2026, 7, 18, 12, 30, tzinfo=UTC)
    metadata = {"s3gw-compression": "zstd", "s3gw-original-size": "12"}
    stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": TEST_BUCKET,
            "Key": test_key,
            "Body": b"compressed",
            "ContentType": "application/zstd",
            "Metadata": metadata,
        },
    )
    stubber.add_response(
        "head_object",
        {
            "ContentLength": 10,
            "LastModified": modified,
            "ETag": '"abc123"',
        },
        {"Bucket": TEST_BUCKET, "Key": test_key},
    )

    backend.put_object(
        test_key,
        b"compressed",
        content_type="application/zstd",
        metadata=metadata,
    )


def test_get_object_reads_body(backend, stubber, test_key):
    stubber.add_response(
        "get_object",
        {
            "Body": StreamingBody(BytesIO(b"hello garage"), 12),
            "ContentType": "text/plain",
            "Metadata": {"source": "test"},
        },
        {"Bucket": TEST_BUCKET, "Key": test_key},
    )

    assert backend.get_object(test_key) == StoredObject(
        data=b"hello garage",
        content_type="text/plain",
        metadata={"source": "test"},
    )


def test_list_objects_with_prefix(backend, stubber):
    modified = datetime(2026, 7, 18, 12, 30, tzinfo=UTC)
    stubber.add_response(
        "list_objects_v2",
        {
            "IsTruncated": False,
            "Name": TEST_BUCKET,
            "Prefix": "test/",
            "KeyCount": 1,
            "MaxKeys": 1000,
            "Contents": [
                {
                    "Key": "test/example.txt",
                    "Size": 4,
                    "LastModified": modified,
                    "ETag": '"etag-value"',
                }
            ],
        },
        {"Bucket": TEST_BUCKET, "Prefix": "test/"},
    )

    assert backend.list_objects(prefix="test/") == [
        ObjectInfo(
            key="test/example.txt",
            size=4,
            last_modified=modified.isoformat(),
            etag="etag-value",
        )
    ]


def test_delete_object(backend, stubber, test_key):
    stubber.add_response(
        "delete_object",
        {},
        {"Bucket": TEST_BUCKET, "Key": test_key},
    )

    backend.delete_object(test_key)


def test_object_exists(backend, stubber, test_key):
    stubber.add_response(
        "head_object",
        {"ContentLength": 4, "LastModified": datetime.now(UTC), "ETag": '"etag"'},
        {"Bucket": TEST_BUCKET, "Key": test_key},
    )

    assert backend.object_exists(test_key)


def test_object_exists_returns_false_for_missing_key(backend, stubber, test_key):
    stubber.add_client_error(
        "head_object",
        service_error_code="404",
        service_message="Not Found",
        http_status_code=404,
        expected_params={"Bucket": TEST_BUCKET, "Key": test_key},
    )

    assert not backend.object_exists(test_key)


def test_get_nonexistent_object_raises(backend, stubber):
    stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        service_message="Not Found",
        http_status_code=404,
        expected_params={"Bucket": TEST_BUCKET, "Key": "does/not/exist.txt"},
    )

    with pytest.raises(FileNotFoundError):
        backend.get_object("does/not/exist.txt")


real_garage = pytest.mark.skipif(
    not os.getenv("S3_ACCESS_KEY") or not os.getenv("S3_SECRET_KEY"),
    reason="S3_ACCESS_KEY / S3_SECRET_KEY not set — start Garage and export .env to run these",
)


@pytest.fixture
def real_backend():
    return GarageBackend(
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:3900"),
        access_key=os.environ["S3_ACCESS_KEY"],
        secret_key=os.environ["S3_SECRET_KEY"],
        bucket=os.getenv("S3_BUCKET", "default-bucket"),
    )


@real_garage
def test_real_garage_put_and_get_object(real_backend, test_key):
    content = b"hello garage"
    metadata = {"source": "integration-test"}
    real_backend.put_object(
        test_key,
        content,
        content_type="text/plain",
        metadata=metadata,
    )
    stored = real_backend.get_object(test_key)
    assert stored.data == content
    assert stored.content_type == "text/plain"
    assert stored.metadata == metadata


@real_garage
def test_real_garage_object_exists(real_backend, test_key):
    assert not real_backend.object_exists(test_key)
    real_backend.put_object(test_key, b"data")
    assert real_backend.object_exists(test_key)


@real_garage
def test_real_garage_list_objects_with_prefix(real_backend, test_key):
    real_backend.put_object(test_key, b"data")
    results = real_backend.list_objects(prefix="test/")
    assert any(obj.key == test_key for obj in results)


@real_garage
def test_real_garage_delete_object(real_backend, test_key):
    real_backend.put_object(test_key, b"data")
    real_backend.delete_object(test_key)
    assert not real_backend.object_exists(test_key)


@real_garage
def test_real_garage_get_nonexistent_object_raises(real_backend):
    with pytest.raises(FileNotFoundError):
        real_backend.get_object("does/not/exist.txt")
