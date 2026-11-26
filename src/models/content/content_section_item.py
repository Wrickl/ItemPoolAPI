from uuid import UUID

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class ContentSectionItem(SQLModel, table=True):
    __tablename__ = "ContentSectionItem"
    __table_args__ = (Index("ix_content_section_item_item_id", "item_id"),)

    content_section_id: UUID = Field(
        foreign_key="content_section.id",
        primary_key=True,
    )
    item_id: UUID = Field(
        foreign_key="Item.item_id",
        primary_key=True,
    )
