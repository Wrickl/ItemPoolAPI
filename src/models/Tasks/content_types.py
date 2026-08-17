from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Column, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .tasks import Item


class DataTypeBase(SQLModel):
    name: str = Field(sa_column=Column(String(128), unique=True, nullable=False))
    description: Optional[str] = Field(default=None, max_length=255)
    source: str = Field(default="database", max_length=50)


class DataType(DataTypeBase, table=True):
    __tablename__ = "DataType"

    data_type_id: Optional[int] = Field(default=None, primary_key=True)
    content_pieces: List["ContentPiece"] = Relationship(back_populates="data_type")


class ItemTypeBase(SQLModel):
    name: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    description: Optional[str] = Field(default=None)


class ItemType(ItemTypeBase, table=True):
    __tablename__ = "ItemType"

    item_type_id: Optional[int] = Field(default=None, primary_key=True)
    content_piece_assignments: List["ItemTypeContentPiece"] = Relationship(back_populates="item_type")
    items: List["Item"] = Relationship(back_populates="item_type")


class ContentPieceBase(SQLModel):
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    data_type_id: int = Field(foreign_key="DataType.data_type_id")


class ContentPiece(ContentPieceBase, table=True):
    __tablename__ = "ContentPiece"

    content_piece_id: Optional[int] = Field(default=None, primary_key=True)
    data_type: DataType = Relationship(back_populates="content_pieces")
    item_type_assignments: List["ItemTypeContentPiece"] = Relationship(back_populates="content_piece")


class ItemTypeContentPieceBase(SQLModel):
    item_type_id: int = Field(foreign_key="ItemType.item_type_id")
    content_piece_id: int = Field(foreign_key="ContentPiece.content_piece_id")
    position: int = Field(default=0, ge=0)
    is_required: bool = Field(default=False)


class ItemTypeContentPiece(ItemTypeContentPieceBase, table=True):
    __tablename__ = "ItemTypeContentPiece"

    item_type_content_piece_id: Optional[int] = Field(default=None, primary_key=True)
    item_type: ItemType = Relationship(back_populates="content_piece_assignments")
    content_piece: ContentPiece = Relationship(back_populates="item_type_assignments")
    item_contents: List["ItemContent"] = Relationship(back_populates="item_type_content_piece")


class ItemContentBase(SQLModel):
    item_id: int = Field(foreign_key="Item.item_id")
    item_type_content_piece_id: int = Field(foreign_key="ItemTypeContentPiece.item_type_content_piece_id")
    value: Any = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(JSON(), "sqlite"), nullable=True),
    )


class ItemContent(ItemContentBase, table=True):
    __tablename__ = "ItemContent"

    item_content_id: Optional[int] = Field(default=None, primary_key=True)
    item: "Item" = Relationship(back_populates="content_values")
    item_type_content_piece: ItemTypeContentPiece = Relationship(back_populates="item_contents")
