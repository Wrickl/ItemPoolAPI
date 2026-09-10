from pydantic import BaseModel, Field


class StatusCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Status.
    - Erforderliche Felder: name, description
    """

    name: str = Field(..., description="Name des Status")
    description: str | None = Field(default=None, description="Beschreibung des Status")


class StatusUpdate(BaseModel):
    pass


class StatusResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Status."""

    status_id: int | None
    name: str | None
    description: str | None
