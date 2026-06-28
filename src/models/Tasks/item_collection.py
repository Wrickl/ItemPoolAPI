from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Column, JSON


class ItemCollectionBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=255)
    item_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ItemCollection(ItemCollectionBase, table=True):
    __tablename__ = "ItemCollection"

    collection_id: Optional[int] = Field(default=None, primary_key=True)