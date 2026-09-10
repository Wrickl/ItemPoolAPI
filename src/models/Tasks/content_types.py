from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .tasks import Item


class DataTypeBase(SQLModel):
    name: str = Field(sa_column=Column(String(128), unique=True, nullable=False))
    description: str | None = Field(default=None, max_length=255)
    source: str = Field(default="database", max_length=50)


class DataType(DataTypeBase, table=True):
    __tablename__ = "DataType"

    data_type_id: int | None = Field(default=None, primary_key=True)
    content_pieces: list["ContentPiece"] = Relationship(back_populates="data_type")


class ItemTypeBase(SQLModel):
    name: str = Field(sa_column=Column(String(255), unique=True, nullable=False))
    description: str | None = Field(default=None)


class ItemType(ItemTypeBase, table=True):
    __tablename__ = "ItemType"

    item_type_id: int | None = Field(default=None, primary_key=True)
    content_piece_assignments: list["ItemTypeContentPiece"] = Relationship(
        back_populates="item_type"
    )
    items: list["Item"] = Relationship(back_populates="item_type")


class ContentPieceBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)
    data_type_id: int = Field(foreign_key="DataType.data_type_id")


class ContentPiece(ContentPieceBase, table=True):
    __tablename__ = "ContentPiece"

    content_piece_id: int | None = Field(default=None, primary_key=True)
    data_type: DataType = Relationship(back_populates="content_pieces")
    item_type_assignments: list["ItemTypeContentPiece"] = Relationship(
        back_populates="content_piece"
    )


class ItemTypeContentPieceBase(SQLModel):
    item_type_id: int = Field(foreign_key="ItemType.item_type_id")
    content_piece_id: int = Field(foreign_key="ContentPiece.content_piece_id")
    usage_area: str = Field(max_length=32)
    is_required: bool = Field(default=False)


class ItemTypeContentPiece(ItemTypeContentPieceBase, table=True):
    __tablename__ = "ItemTypeContentPiece"

    item_type_content_piece_id: int | None = Field(default=None, primary_key=True)
    item_type: ItemType = Relationship(back_populates="content_piece_assignments")
    content_piece: ContentPiece = Relationship(back_populates="item_type_assignments")
    item_contents: list["ItemContent"] = Relationship(
        back_populates="item_type_content_piece"
    )


class ItemContentBase(SQLModel):
    item_id: int = Field(foreign_key="Item.item_id")
    item_type_content_piece_id: int = Field(
        foreign_key="ItemTypeContentPiece.item_type_content_piece_id"
    )
    value: Any = Field(
        default=None,
        sa_column=Column(JSONB().with_variant(JSON(), "sqlite"), nullable=True),
    )


class ItemContent(ItemContentBase, table=True):
    __tablename__ = "ItemContent"

    item_content_id: int | None = Field(default=None, primary_key=True)
    item: "Item" = Relationship(back_populates="content_values")
    item_type_content_piece: ItemTypeContentPiece = Relationship(
        back_populates="item_contents"
    )
