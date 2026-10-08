"""Hier werden die Datenmodelle der Content Section abgelegt."""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from .content_section_content_piece import ContentSectionContentPiece
from .content_section_item_type import ContentSectionItemType

if TYPE_CHECKING:
    from models.Tasks.contentPiece import ContentPiece
    from .content_types import ItemType


class ContentSectionBase(SQLModel):
    """Eine Content Section beschreibt einen übergeordneten Bereich in dem Content Pieces zusammengefasst werden können."""
    name: str = Field(index=True, unique=True, max_length=255, description="Name der Content Section")
    description: str | None = Field(default=None, description="Beschreibung der Content Section")


class ContentSection(ContentSectionBase, table=True):
    __tablename__ = "content_section"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content_pieces: list["ContentPiece"] = Relationship(
        back_populates="content_sections",
        link_model=ContentSectionContentPiece,
    )
    item_types: list["ItemType"] = Relationship(
        back_populates="content_sections",
        link_model=ContentSectionItemType,
    )
