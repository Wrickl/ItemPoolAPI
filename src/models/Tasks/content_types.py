from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel
from .content_section_item_type import ContentSectionItemType

if TYPE_CHECKING:
    from .contentPiece import ContentPiece
    from .contentsection import ContentSection
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

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content_sections: list["ContentSection"] = Relationship(
        back_populates="item_types",
        link_model=ContentSectionItemType,
    )
    items: list["Item"] = Relationship(back_populates="item_type")

