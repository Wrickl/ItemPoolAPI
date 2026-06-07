from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.Enums.License import License
from ...models.Enums.Questionstypes import Questiontypes
from ...models.Enums.Status import Status


class ItemCreate(BaseModel):
    """
    Schema für die Erstellung eines neuen Items über die API.

    - Erforderliche Felder: fragestellung, question_type, license, status, author_id
    - Optionale Felder: solution, item_metadata, tags_id, database_id
    """
    fragestellung: str = Field(..., min_length=1, description="Die Aufgabenstellung")
    question_type: Questiontypes = Field(..., description="Typ der Frage (z.B. sql, multiple_choice)")
    license: License = Field(..., description="Lizenz des Items")
    status: Status = Field(default=Status.Draft, description="Status des Items")
    author_id: UUID = Field(..., description="UUID des Autors/Creators")
    solution: Optional[str] = Field(default=None, description="Musterlösung (optional)")
    item_metadata: Optional[dict] = Field(default=None, description="Schema-freie Metadaten (JSON)")
    tags_id: Optional[int] = Field(default=None, description="ID der Tags (optional)")
    database_id: Optional[int] = Field(default=None, description="ID der zugehörigen Datenbank (optional)")


class ItemResponse(BaseModel):
    """Response-Modell für ein erstelltes oder abgerufenes Item."""
    item_id: Optional[int]
    fragestellung: str
    question_type: Questiontypes
    license: License
    status: Status
    author_id: UUID
    solution: Optional[str]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

