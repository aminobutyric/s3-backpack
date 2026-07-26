from pydantic import BaseModel, Field


class ObjectResponse(BaseModel):
    key: str
    size: int = Field(ge=0)
    last_modified: str
    etag: str


class ObjectListResponse(BaseModel):
    objects: list[ObjectResponse]


class UploadResponse(ObjectResponse):
    original_key: str
    original_size: int = Field(ge=0)
    compression: str | None = None
    saved_bytes: int = Field(ge=0)
    savings_percent: float = Field(ge=0, le=100)


class DeleteResponse(BaseModel):
    key: str
    deleted: bool = True


class DiskResponse(BaseModel):
    name: str
    path: str
    device_type: str
    parent_path: str | None
    root_device_path: str
    size: int = Field(ge=0)
    filesystem: str | None
    filesystem_version: str | None
    label: str | None
    uuid: str | None
    mountpoints: list[str]
    removable: bool
    read_only: bool
    transport: str | None
    model: str | None
    serial: str | None
    system_disk: bool
    ready: bool
    blocking_reasons: list[str]


class DiskInventoryResponse(BaseModel):
    disks: list[DiskResponse]
