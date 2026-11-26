from uuid import UUID

from sqlmodel import Field, SQLModel


class ContentSectionItemType(SQLModel, table=True):
    __tablename__ = "ContentSectionItemType"

    content_section_id: UUID = Field(
        foreign_key="content_section.id",
        primary_key=True,
    )
    item_type_id: UUID = Field(
        foreign_key="ItemType.id",
        primary_key=True,
    )
