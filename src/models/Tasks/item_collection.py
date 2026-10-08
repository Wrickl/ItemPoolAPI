from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from models.Tasks.item_collection_item import ItemCollectionItem

if TYPE_CHECKING:
    from .tasks import Item


class ItemCollectionBase(SQLModel):
    name: str = Field(index=True, unique=True, max_length=255, description="Name der Item Collection")
    description: str | None = Field(default=None, description="Beschreibung der Item Collection")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ItemCollection(ItemCollectionBase, table=True):
    __tablename__ = "ItemCollection"
    collection_id: UUID = Field(default_factory=uuid4, primary_key=True)
    items: list["Item"] = Relationship(
        back_populates="collections",
        link_model=ItemCollectionItem,
    )
