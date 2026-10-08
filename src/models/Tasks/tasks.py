from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from models.creator import Creator
from .item_collection_item import ItemCollectionItem

if TYPE_CHECKING:
    from src.models.Tasks.content_types import ItemType
    from src.models.Tasks.item_collection import ItemCollection


class ItemBase(SQLModel):
    item_type_id: UUID = Field(default=None, foreign_key="ItemType.id")
    license: UUID = Field(default=None, foreign_key="license.id")
    status: UUID = Field(default=None, foreign_key="status.id")
    themenbereich: UUID = Field(foreign_key="themenbereich.id")
    author_id: UUID = Field(foreign_key="creator.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # TODO Implement tags table and relationship
    # tags_id: UUID | None = Field(default=None, foreign_key="tags.id")


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    collections: list["ItemCollection"] = Relationship(
        back_populates="items",
        link_model=ItemCollectionItem,
    )
