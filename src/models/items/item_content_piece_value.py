from typing import Any
from uuid import UUID

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ItemContentPieceValue(SQLModel, table=True):
    __tablename__ = "ItemContentPieceValue"

    item_id: UUID = Field(foreign_key="Item.item_id", primary_key=True)
    content_section_id: UUID = Field(
        foreign_key="content_section.id",
        primary_key=True,
    )
    content_piece_id: UUID = Field(
        foreign_key="ContentPiece.id",
        primary_key=True,
    )
    value: Any = Field(sa_column=Column(JSON, nullable=True))
