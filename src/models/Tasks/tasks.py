from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

from models.creator import Creator

if TYPE_CHECKING:
    from src.models.Tasks.content_types import ItemContent, ItemType

class ItemBase(SQLModel):
    item_type_id: UUID = Field(default=None, foreign_key="ItemType.id")
    license: UUID = Field(default=None, foreign_key="license.id")
    status: UUID = Field(default=None, foreign_key="status.id")
    themenbereich: UUID = Field(foreign_key="themenbereich.id")
    author_id: UUID = Field(foreign_key="creator.id")
    solution_content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    interaction_content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON) )
    stimuli_content: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    item_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    #TODO Implement tags table and relationship
    #tags_id: UUID | None = Field(default=None, foreign_key="tags.id")


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: UUID = Field(default=None, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    item_type: Optional["ItemType"] = Relationship(back_populates="items")
    content_values: list["ItemContent"] = Relationship(back_populates="item")
