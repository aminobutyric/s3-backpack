from functools import lru_cache

from app.config import Settings, get_settings
from app.storage.base import ObjectInfo, StorageBackend
from app.storage.garage import GarageBackend


@lru_cache
def _build_backend(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    region: str,
) -> GarageBackend:
    return GarageBackend(
        endpoint_url=endpoint_url,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        region=region,
    )


def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    return _build_backend(
        settings.s3_endpoint_url,
        settings.s3_access_key,
        settings.s3_secret_key,
        settings.s3_bucket,
        settings.s3_region,
    )


__all__ = ["GarageBackend", "ObjectInfo", "StorageBackend", "get_storage_backend"]
