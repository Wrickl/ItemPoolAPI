from datetime import datetime
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...models.Enums.Questiontypes import QuestionTypes


class FlexibleContentBlock(BaseModel):
    """Verweist auf ein flexibles ContentPiece und speichert den konkreten Wert."""

    content_piece_id: int = Field(..., ge=1, description="ID eines ContentPiece aus dem flexiblen Content-Type-System")
    value: Any = Field(..., description="Inhalt fuer das referenzierte ContentPiece")


class ItemCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Items ueber die API.

    - Erforderliche Felder: fragestellung, question_type, license, status_id, author_id
    - Pflichtfelder fuer flexible Fragebestandteile: interaction_content, stimuli_content
    - Optionale Felder: solution, tags_id, database_id
    - Pflicht-Metadatum: item_metadata.bloomlevel
    """

    fragestellung: str = Field(..., description="Die Aufgabenstellung")
    question_type: QuestionTypes = Field(..., description="Typ der Frage (z.B. FREITEXT, MULTIPLECHOICE)")
    license: int = Field(default=None, description="ID der zugehoerigen License")
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
    item_metadata: dict = Field(..., description="Schema-freie Metadaten (JSON), muss `bloomlevel` enthalten")
    themenbereich_id: Optional[int] = Field(default=None, description="ID des zugehoerigen Themenbereichs (optional)")
    status_id: int = Field(default=None, description="ID des zugehoerigen Status")
    tags_id: Optional[int] = Field(default=None, description="ID der Tags (optional)")
    database_id: Optional[int] = Field(default=None, description="ID der zugehoerigen Datenbank (optional)")

    @model_validator(mode="after")
    def validate_item(self):
        if isinstance(self.fragestellung, str) and not self.fragestellung.strip():
            raise ValueError("`fragestellung` muss ein nicht-leerer String sein")

        bloomlevel = self.item_metadata.get("bloomlevel")
        if bloomlevel is None or (isinstance(bloomlevel, str) and not bloomlevel.strip()):
            raise ValueError("`item_metadata.bloomlevel` muss gesetzt sein")
        return self


class ItemResponse(BaseModel):
    """Response-Modell fuer ein erstelltes oder abgerufenes Item."""

    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: Optional[int]  # TODO Anpassen damit der Name dort ausgegeben wird
    status: Optional[int]  # TODO Anpassen damit der Name dort ausgegeben wird
    author_id: UUID
    solution: list[dict[str, Any]]
    interaction_content: list[dict[str, Any]]
    stimuli_content: list[dict[str, Any]]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ItemWithAuthorResponse(BaseModel):
    """Response-Modell fuer Items inklusive Author-Name (server-side join)."""

    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: Optional[int]  # TODO Anpassen damit der Name dort ausgegeben wird
    status: Optional[int]  # TODO Anpassen damit der Name dort ausgegeben wird
    author_id: UUID
    author_name: Optional[str]
    solution: list[dict[str, Any]]
    interaction_content: list[dict[str, Any]]
    stimuli_content: list[dict[str, Any]]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
