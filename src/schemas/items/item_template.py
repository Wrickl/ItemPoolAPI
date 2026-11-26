from uuid import UUID

from pydantic import BaseModel, Field

from schemas.content.content_piece import ContentPieceReadTemplate


class ItemTemplateContentSectionResponse(BaseModel):
    """Template-Ansicht einer ContentSection inklusive ihrer ContentPieces."""

    id: UUID
    name: str
    description: str | None = None
    content_pieces: list[ContentPieceReadTemplate] = Field(default_factory=list)


class ItemTemplateResponse(BaseModel):
    """Ausfüllbare Vorlage für ein Item eines ItemTypes."""

    item_type_id: UUID
    item_type_name: str
    item_type_description: str | None = None
    license: UUID | None = None
    author_id: UUID | None = None
    status_id: UUID | None = None
    themenbereich_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    content_sections: list[ItemTemplateContentSectionResponse] = Field(
        default_factory=list,
        description="Liste der Sections des ItemTypes inklusive ihrer ContentPieces",
    )
