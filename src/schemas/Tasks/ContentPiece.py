from uuid import UUID

from pydantic import BaseModel, Field


class ContentPieceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    data_type_id: int
    complex_type_id: UUID | None = None


class ContentPieceRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    data_type_id: int
    data_type_name: str | None = None
    complex_type_id: UUID | None = None


class ContentPieceReadFull (BaseModel):
    id: UUID
    name: str
    data_type_id: int
    description: str | None = None
    data_type_name: str | None = None
    complex_type_id: UUID | None = None
    complex_schema: dict | None = None

class ContentPieceReadTemplate (BaseModel):
    id: UUID
    name: str
    description: str | None = None
    data_type_id: int
    data_type_name: str | None = None
    complex_type_id: UUID | None = None
    complex_schema: dict | None = None