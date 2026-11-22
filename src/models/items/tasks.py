from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from models.creator import Creator
from .item_collection_item import ItemCollectionItem
from .item_tag import ItemTag

if TYPE_CHECKING:
    from src.models.items.content_types import ItemType
    from src.models.items.item_collection import ItemCollection


class ItemBase(SQLModel):
    item_type_id: UUID = Field(default=None, foreign_key="ItemType.id")
    license: UUID = Field(default=None, foreign_key="license.id")
    status: UUID = Field(default=None, foreign_key="status.id")
    themenbereich: UUID = Field(foreign_key="themenbereich.id")
    author_id: UUID = Field(foreign_key="creator.author_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    tag_links: list[ItemTag] = Relationship(passive_deletes="all")
    collections: list["ItemCollection"] = Relationship(
        back_populates="items",
        link_model=ItemCollectionItem,
    )
