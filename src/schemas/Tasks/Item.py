from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FlexibleContentBlock(BaseModel):
    """Verweist auf ein flexibles ContentPiece und speichert den konkreten Wert."""

    content_piece_id: int = Field(
        ...,
        ge=1,
        description="ID eines ContentPiece aus dem flexiblen Content-Type-System",
    )
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
    Schema fuer die Erstellung eines neuen Items ueber die API.

    - Erforderliche Felder: license, status_id, author_id
    - Pflichtfelder fuer flexible Fragebestandteile: interaction_content, stimuli_content
    - Optionale Felder: solution, tags_id, item_metadata
    """

    license: int = Field(..., description="ID der zugehoerigen License")
    author_id: UUID = Field(..., description="UUID des Autors/Creators")
    solution: list[FlexibleContentBlock] | None = Field(
        default=None,
        min_length=1,
        description="Optionale flexible Loesungsbloecke auf Basis des Content-Type-Systems",
    )
    interaction_content: list[FlexibleContentBlock] = Field(
        ...,
        min_length=1,
        description="Flexible Interaction-Bloecke, die Teil der eigentlichen Aufgabeninteraktion sind",
    )
    stimuli_content: list[FlexibleContentBlock] = Field(
        ...,
        min_length=1,
        description="Flexible Stimuli-Bloecke, die z. B. Material/Prompt-Kontext fuer die Aufgabe liefern",
    )
    item_metadata: dict = Field(
        default_factory=dict,
        description="Schema-freie Metadaten (JSON), vollkommen flexibel",
    )
    themenbereich_id: int | None = Field(
        default=None, description="ID des zugehoerigen Themenbereichs (optional)"
    )
    status_id: int = Field(..., description="ID des zugehoerigen Status")
    tags_id: int | None = Field(default=None, description="ID der Tags (optional)")
    item_type_id: int | None = Field(
        default=None, description="ID des ItemTypes (optional)"
    )


class ItemResponse(BaseModel):
    """Response-Modell fuer ein erstelltes oder abgerufenes Item."""

    item_id: int | None
    license: int | None
    status: int | None
    author_id: UUID
    solution: list[dict[str, Any]]
    interaction_content: list[dict[str, Any]]
    stimuli_content: list[dict[str, Any]]
    item_metadata: dict | None
    tags_id: int | None
    item_type_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ItemWithAuthorResponse(BaseModel):
    """Response-Modell fuer Items inklusive Author-Name (server-side join)."""

    item_id: int | None
    license: int | None
    status: int | None
    author_id: UUID
    author_name: str | None
    solution: list[dict[str, Any]]
    interaction_content: list[dict[str, Any]]
    stimuli_content: list[dict[str, Any]]
    item_metadata: dict | None
    tags_id: int | None
    item_type_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemExportResponse(BaseModel):
    """Export-Response-Modell mit Namen statt IDs und angereicherten Content-Pieces."""

    item_id: int | None
    license: str | None = Field(None, description="Name der Lizenz statt ID")
    status: str | None = Field(None, description="Name des Status statt ID")
    item_type: str | None = Field(None, description="Name des ItemType statt ID")
    author_id: UUID
    author_name: str | None
    themenbereich: str | None = Field(
        default=None, description="Name des Themenbereichs statt ID"
    )
    solution: list[EnrichedContentBlock] = Field(
        default_factory=list,
        description="Angereicherte Solution-Blöcke mit vollständigen ContentPiece-Info",
    )
    interaction_content: list[EnrichedContentBlock] = Field(
        default_factory=list, description="Angereicherte Interaction-Blöcke"
    )
    stimuli_content: list[EnrichedContentBlock] = Field(
        default_factory=list, description="Angereicherte Stimuli-Blöcke"
    )
    item_metadata: dict | None = None
    themenbereich_id: int | None = None
    tags_id: int | None = None
    created_at: datetime = Field(..., description="Erstellungsdatum")
