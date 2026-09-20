from pydantic import BaseModel, Field


class StatusCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Status.
    - Erforderliche Felder: name, description
    """

    name: str = Field(..., description="Name des Status")
    description: str | None = Field(default=None, description="Beschreibung des Status")


class StatusUpdate(BaseModel):
    name: str = Field(..., description="Name des Status")
    description: str | None = Field(default=None, description="Beschreibung des Status")


class StatusResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Status."""

    status_id: int
    name: str
    description: str | None
