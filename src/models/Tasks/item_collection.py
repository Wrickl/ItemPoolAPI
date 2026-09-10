from datetime import UTC, datetime

from sqlmodel import JSON, Column, Field, SQLModel


class ItemCollectionBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    item_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ItemCollection(ItemCollectionBase, table=True):
    __tablename__ = "ItemCollection"

    collection_id: int | None = Field(default=None, primary_key=True)
