from typing import Optional

from pydantic import BaseModel, Field


class ThemenbereichCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Themenbereichs ueber die API.

    - Erforderliche Felder: name, description
    """
    name: str = Field(..., description="Name des Themenbereichs")
    description: Optional[str] = Field(default=None, description="Beschreibung des Themenbereichs")


class ThemenbereichUpdate(BaseModel):
    pass


class ThemenbereichResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Themenbereich."""

    themenbereich_id: Optional[int]
    name: Optional[str]
    description: Optional[str]
