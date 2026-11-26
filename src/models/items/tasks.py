from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from models.basic_metadata.creator import Creator
from .item_collection_item import ItemCollectionItem
from .item_tag import ItemTag

if TYPE_CHECKING:
    from models import ItemCollection, ItemType


class ItemBase(SQLModel):
    item_type_id: UUID = Field(default=None, foreign_key="ItemType.id")
    license: UUID = Field(default=None, foreign_key="license.id")
    status: UUID = Field(default=None, foreign_key="status.id")
    themenbereich: UUID = Field(foreign_key="themenbereich.id")
    author_id: UUID = Field(foreign_key="creator.author_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Item(ItemBase, table=True):
    __tablename__ = "Item"
    __table_args__ = (
        UniqueConstraint("version_group_id", "version_number", name="uq_item_version"),
        UniqueConstraint("previous_item_id", name="uq_item_previous_version"),
        CheckConstraint("version_number >= 1", name="ck_item_version_positive"),
    )

    item_id: UUID = Field(default_factory=uuid4, primary_key=True)
    version_group_id: UUID = Field(default_factory=uuid4, index=True, nullable=False)
    version_number: int = Field(default=1, nullable=False)
    previous_item_id: UUID | None = Field(default=None, foreign_key="Item.item_id")
    change_note: str | None = Field(default=None)
    author: Creator = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    tag_links: list[ItemTag] = Relationship(passive_deletes="all")
    collections: list["ItemCollection"] = Relationship(
        back_populates="items",
        link_model=ItemCollectionItem,
    )
