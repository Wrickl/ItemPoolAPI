from pydantic import BaseModel, Field


class ThemenbereichCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Themenbereichs.
    - Erforderliche Felder: name, description
    """

    name: str = Field(..., description="Name des Themenbereichs")
    description: str | None = Field(
        default=None, description="Beschreibung des Themenbereichs"
    )


class ThemenbereichUpdate(BaseModel):
    pass


class ThemenbereichResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Themenbereich."""

    themenbereich_id: int | None
    name: str | None
    description: str | None
