from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .ContentPiece import ContentPieceReadTemplate


class FlexibleContentBlock(BaseModel):
    """Verweist auf ein flexibles ContentPiece und speichert den konkreten Wert."""

    content_piece_id: int = Field(
        ..., ge=1, description="ID eines ContentPiece aus dem flexiblen Content-Type-System", )
    value: Any = Field(..., description="Inhalt fuer das referenzierte ContentPiece")


class ExportContentPiece(BaseModel):
    """Vollständig angereicherter Content-Type für Exporte."""

    content_piece_id: int = Field(..., description="ID des ContentPiece")
    is_required: bool = Field(
        ..., description="Ob das ContentPiece für den ItemType verpflichtend ist"
    )
    content_piece_name: str = Field(..., description="Name des ContentPiece")
    content_piece_description: str | None = Field(
        default=None, description="Beschreibung des ContentPiece"
    )
    data_type_id: int = Field(..., description="ID des Datentyps")
    data_type_name: str = Field(..., description="Name des Datentyps")


class EnrichedContentBlock(BaseModel):
    """Erweiterter Content-Block mit vollständigen ContentPiece-Informationen für Exports."""

    content_piece: ExportContentPiece = Field(
        ..., description="Vollständiges ContentPiece-Objekt"
    )
    value: Any = Field(..., description="Wert des ContentPiece")


class ItemCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Items.
    """

    license: UUID = Field(..., description="ID der zugehoerigen License")
    author_id: UUID = Field(..., description="UUID des Autors/Creators")
    themenbereich_id: int | None = Field(
        default=None, description="ID des zugehoerigen Themenbereichs (optional)"
    )
    status_id: UUID = Field(..., description="ID des zugehoerigen Status")
    # tags_id: UUID | None = Field(default=None, description="ID der Tags (optional)")
    item_type_id: UUID | None = Field(
        default=None, description="ID des ItemTypes (optional)"
    )


class ItemResponse(BaseModel):
    """Response-Modell fuer ein erstelltes oder abgerufenes Item."""

    item_id: UUID
    license: UUID | None
    status: UUID | None
    author_id: UUID
    # tags_id: UUID | None
    item_type_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class ItemWithAuthorResponse(BaseModel):
    """Response-Modell fuer Items inklusive Author-Name (server-side join)."""

    item_id: UUID
    license: UUID
    status: UUID
    author_id: UUID
    author_name: str | None
    # tags_id: UUID | None
    item_type_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemExportResponse(BaseModel):
    """Export-Response-Modell mit Namen statt IDs und angereicherten Content-Pieces."""

    item_id: UUID
    license: str | None = Field(None, description="Name der Lizenz statt ID")
    status: str | None = Field(None, description="Name des Status statt ID")
    item_type: str | None = Field(None, description="Name des ItemType statt ID")
    author_id: UUID
    author_name: str | None
    themenbereich: str | None = Field(
        default=None, description="Name des Themenbereichs statt ID"
    )
    themenbereich_id: UUID
    # tags_id: UUID | None = None
    created_at: datetime = Field(..., description="Erstellungsdatum")


class ItemTemplateContentSectionResponse(BaseModel):
    """Template-Ansicht einer ContentSection inklusive ihrer ContentPieces."""

    id: UUID
    name: str
    description: str | None = None
    content_pieces: list[ContentPieceReadTemplate] = Field(default_factory=list)


class ItemTemplateResponse(BaseModel):
    """Response-Modell für ein Item-Template, das alle Sections eines ItemTypes mit ihren ContentPieces enthält."""

    item_type_id: UUID
    item_type_name: str
    item_type_description: str | None = None
    license_id: UUID | None | str = Field(
        default=None,
        description="Blanko-Feld fuer die spätere Lizenzzuordnung",
    )
    status_id: UUID | None| str  = Field(
        default=None,
        description="Blanko-Feld fuer die spätere Statuszuordnung",
    )
    themenbereich_id: UUID | None | str = Field(
        default=None,
        description="Blanko-Feld fuer die spätere Themenbereichszuordnung",
    )
    content_sections: list[ItemTemplateContentSectionResponse] = Field(
        default_factory=list,
        description="Liste der Sections des ItemTypes inklusive ihrer ContentPieces",
    )
