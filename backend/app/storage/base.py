"""
Storage backend abstraction.

Every concrete backend (Garage in v1, cloud S3 in v1.1) implements this
interface. No code outside `storage/` should import a concrete backend
directly — everything else (api/, compression/) imports only this
interface. That's what makes swapping backends a config change instead
of a rewrite.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass
class ObjectInfo:
    key: str
    size: int
    last_modified: str  # ISO 8601
    etag: str


@dataclass(frozen=True)
class StoredObject:
    data: bytes
    content_type: str
    metadata: dict[str, str]


class StorageBackend(ABC):
    """S3-compatible storage backend interface.

    Methods are synchronous by design — boto3 itself is sync. Keeping this
    interface sync avoids depending on aioboto3 and keeps unit tests simple to
    write and run.
    """

    @abstractmethod
    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectInfo:
        """Upload an object. Overwrites if key already exists."""
        raise NotImplementedError

    @abstractmethod
    def get_object(self, key: str) -> StoredObject:
        """Download an object's full content. Raises FileNotFoundError if missing."""
        raise NotImplementedError

    @abstractmethod
    def list_objects(self, prefix: str = "") -> list[ObjectInfo]:
        """List objects, optionally filtered by key prefix."""
        raise NotImplementedError

    @abstractmethod
    def delete_object(self, key: str) -> None:
        """Delete an object. Should not raise if key does not exist."""
        raise NotImplementedError

    @abstractmethod
    def object_exists(self, key: str) -> bool:
        """Check whether an object exists without downloading it."""
        raise NotImplementedError
