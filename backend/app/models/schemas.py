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
