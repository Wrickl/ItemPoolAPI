from uuid import UUID

from sqlmodel import Field, SQLModel


class ContentSectionContentPiece(SQLModel, table=True):
    __tablename__ = "ContentSectionContentPiece"

    content_section_id: UUID = Field(
        foreign_key="content_section.id",
        primary_key=True,
    )
    content_piece_id: UUID = Field(
        foreign_key="ContentPiece.id",
        primary_key=True,
    )
