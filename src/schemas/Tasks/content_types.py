from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DataTypeRead(BaseModel):
    data_type_id: int
    name: str
    description: str | None = None
    source: str

    model_config = ConfigDict(from_attributes=True)


class ItemTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ItemTypeRead(BaseModel):
    item_type_id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ContentPieceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    data_type_id: int


class ContentPieceRead(BaseModel):
    content_piece_id: int
    name: str
    description: str | None = None
    data_type_id: int
    data_type_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemTypeContentPieceAssign(BaseModel):
    content_piece_id: int
    usage_area: Literal["solution", "stimuli_content", "interaction_content"]
    is_required: bool = False


class ItemTypeContentPieceRead(BaseModel):
    item_type_content_piece_id: int
    item_type_id: int
    content_piece_id: int
    usage_area: Literal["solution", "stimuli_content", "interaction_content"]
    is_required: bool
    content_piece_name: str
    content_piece_description: str | None = None
    data_type_id: int
    data_type_name: str


class ItemTypeDetailRead(BaseModel):
    item_type_id: int
    name: str
    description: str | None = None
    content_pieces: list[ItemTypeContentPieceRead] = Field(default_factory=list)
