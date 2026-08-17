from typing import Optional

from pydantic import BaseModel, Field


class StatusCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Status ueber die API.

    - Erforderliche Felder: name, description
    """
    name: str = Field(..., description="Name des Status")
    description: Optional[str] = Field(default=None, description="Beschreibung des Status")


class StatusUpdate(BaseModel):
    pass


class StatusResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Status."""

    status_id: Optional[int]
    name: Optional[str]
    description: Optional[str]
