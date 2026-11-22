from uuid import UUID

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class ItemTag(SQLModel, table=True):
    __tablename__ = "ItemTag"
    __table_args__ = (Index("ix_item_tag_name_item_id", "name", "item_id"),)

    item_id: UUID = Field(
        foreign_key="Item.item_id", primary_key=True, ondelete="CASCADE"
    )
    name: str = Field(primary_key=True, max_length=128)
