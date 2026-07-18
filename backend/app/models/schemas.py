from pydantic import BaseModel, Field


class ObjectResponse(BaseModel):
    key: str
    size: int = Field(ge=0)
    last_modified: str
    etag: str


class ObjectListResponse(BaseModel):
    objects: list[ObjectResponse]


class DeleteResponse(BaseModel):
    key: str
    deleted: bool = True
