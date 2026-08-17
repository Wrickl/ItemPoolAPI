from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DataTypeRead(BaseModel):
    data_type_id: int
    name: str
    description: Optional[str] = None
    source: str

    model_config = ConfigDict(from_attributes=True)


class DataTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    source: str = Field(default="manual", min_length=1, max_length=50)


class ItemTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ItemTypeRead(BaseModel):
    item_type_id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContentPieceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    data_type_id: int


class ContentPieceRead(BaseModel):
    content_piece_id: int
    name: str
    description: Optional[str] = None
    data_type_id: int
    data_type_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ItemTypeContentPieceAssign(BaseModel):
    content_piece_id: int
    position: int = Field(default=0, ge=0)
    is_required: bool = False


class ItemTypeContentPieceRead(BaseModel):
    item_type_content_piece_id: int
    item_type_id: int
    content_piece_id: int
    position: int
    is_required: bool
    content_piece_name: str
    content_piece_description: Optional[str] = None
    data_type_id: int
    data_type_name: str


class ItemTypeDetailRead(BaseModel):
    item_type_id: int
    name: str
    description: Optional[str] = None
    content_pieces: list[ItemTypeContentPieceRead] = Field(default_factory=list)

#
# class FlexibleItemContentCreate(BaseModel):
#     item_type_content_piece_id: int
#     value: Any
#
#
# class FlexibleItemCreate(BaseModel):
#     author_id: UUID
#     license: License
#     status: Optional[int] = None
#     item_type_id: int
#     item_metadata: dict = Field(default_factory=dict)
#     tags_id: Optional[int] = None
#     database_id: Optional[int] = None
#     content: list[FlexibleItemContentCreate] = Field(default_factory=list)
#
#
# class FlexibleItemContentRead(BaseModel):
#     item_content_id: int
#     item_type_content_piece_id: int
#     content_piece_id: int
#     content_piece_name: str
#     data_type_id: int
#     data_type_name: str
#     position: int
#     is_required: bool
#     value: Any
#
#
# class FlexibleItemRead(BaseModel):
#     item_id: int
#     author_id: UUID
#     license: License
#     status: Optional[int] = None
#     item_type_id: int
#     item_type_name: str
#     item_metadata: dict = Field(default_factory=dict)
#     tags_id: Optional[int] = None
#     database_id: Optional[int] = None
#     created_at: datetime
#     content: list[FlexibleItemContentRead] = Field(default_factory=list)
