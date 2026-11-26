from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints


def _reject_null_character(name: str) -> str:
    if "\x00" in name:
        raise ValueError("Ein Tag darf kein Nullzeichen enthalten")
    return name


def _validate_change_note(note: str) -> str:
    if "\x00" in note:
        raise ValueError("Eine Änderungsbeschreibung darf kein Nullzeichen enthalten")
    return note


TagName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=128),
    AfterValidator(_reject_null_character),
]
MAX_ITEM_TAGS = 100
ItemTagList = Annotated[list[TagName], Field(max_length=MAX_ITEM_TAGS)]

ChangeNote = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    AfterValidator(_validate_change_note),
]


class ItemTagsUpdate(BaseModel):
    tags: ItemTagList
    change_note: ChangeNote


class ItemTagsResponse(BaseModel):
    item_id: UUID
    tags: list[str]
    version_group_id: UUID
    version_number: int
    previous_item_id: UUID | None
    change_note: str | None
    is_current: bool
    current_item_id: UUID
    current_version_number: int


class ItemContentPieceCreate(BaseModel):
    id: UUID
    value: Any = Field(..., description="Inhalt des ContentPiece")


class ItemContentSectionCreate(BaseModel):
    id: UUID
    content_pieces: list[ItemContentPieceCreate]


class ItemContentPieceResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    data_type_id: int
    data_type_name: str | None = None
    complex_type_id: UUID | None = None
    complex_schema: dict | None = None
    value: Any = None


class ItemContentSectionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    content_pieces: list[ItemContentPieceResponse] = Field(default_factory=list)


class FlexibleContentBlock(BaseModel):
    """Verweist auf ein flexibles ContentPiece und speichert den konkreten Wert."""

    content_piece_id: UUID = Field(
        ..., description="UUID eines ContentPiece aus dem flexiblen Content-Type-System"
    )
    value: Any = Field(..., description="Inhalt fuer das referenzierte ContentPiece")


class ExportContentPiece(BaseModel):
    """Vollständig angereicherter Content-Type für Exporte."""

    content_piece_id: UUID = Field(..., description="UUID des ContentPiece")
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
    themenbereich_id: UUID = Field(
        ..., description="UUID des zugehoerigen Themenbereichs"
    )
    status_id: UUID = Field(..., description="ID des zugehoerigen Status")
    item_type_id: UUID = Field(
        ..., description="ID des ItemTypes, dessen Template ausgefüllt wurde"
    )
    content_sections: list[ItemContentSectionCreate] = Field(
        ..., description="Ausgefüllte ContentSections aus dem ItemType-Template"
    )
    tags: ItemTagList = Field(default_factory=list)


class ItemUpdate(ItemCreate):
    change_note: ChangeNote


class ItemVersionInfo(BaseModel):
    item_id: UUID
    version_group_id: UUID
    version_number: int
    previous_item_id: UUID | None
    change_note: str | None
    is_current: bool
    current_item_id: UUID
    current_version_number: int


class ItemResponse(ItemVersionInfo):
    """Response-Modell fuer ein erstelltes oder abgerufenes Item."""

    item_id: UUID
    license: UUID | None
    status: UUID | None
    status_id: UUID | None = None
    author_id: UUID
    item_type_id: UUID | None
    themenbereich_id: UUID | None = None
    content_sections: list[ItemContentSectionResponse] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemWithAuthorResponse(ItemVersionInfo):
    """Response-Modell fuer Items inklusive basic_metadata-Name (server-side join)."""

    item_id: UUID
    license: UUID
    status: UUID
    author_id: UUID
    author_name: str | None
    item_type_id: UUID
    themenbereich_id: UUID | None = None
    content_sections: list[ItemContentSectionResponse] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemExportResponse(ItemVersionInfo):
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
    content_sections: list[ItemContentSectionResponse] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(..., description="Erstellungsdatum")
