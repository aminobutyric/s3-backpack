"""
Garage backend implementation (v1's only storage backend).

Garage speaks the S3 API, so this is a thin boto3 client wrapper.
Nothing Garage-specific (endpoint quirks, path-style addressing) should
leak past this file — callers only ever see `StorageBackend`.
"""

from collections.abc import Mapping
from typing import Any, cast

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.storage.base import ObjectInfo, StorageBackend, StoredObject


class GarageBackend(StorageBackend):
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "garage",
    ):
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            # Garage requires path-style addressing (no bucket subdomains).
            config=Config(s3={"addressing_style": "path"}),
        )

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        request: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }
        if metadata:
            request["Metadata"] = dict(metadata)
        self._client.put_object(**request)
        head = self._client.head_object(Bucket=self.bucket, Key=key)
        return ObjectInfo(
            key=key,
            size=head["ContentLength"],
            last_modified=head["LastModified"].isoformat(),
            etag=head["ETag"].strip('"'),
        )

    def get_object(self, key: str) -> StoredObject:
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=key)
            return StoredObject(
                data=cast(bytes, resp["Body"].read()),
                content_type=resp.get("ContentType", "application/octet-stream"),
                metadata=dict(resp.get("Metadata", {})),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise FileNotFoundError(f"Object not found: {key}") from e
            raise

    def list_objects(self, prefix: str = "") -> list[ObjectInfo]:
        paginator = self._client.get_paginator("list_objects_v2")
        results: list[ObjectInfo] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                results.append(
                    ObjectInfo(
                        key=obj["Key"],
                        size=obj["Size"],
                        last_modified=obj["LastModified"].isoformat(),
                        etag=obj["ETag"].strip('"'),
                    )
                )
        return results

    def delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def object_exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise
