from pydantic import BaseModel, Field


class ThemenbereichCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Themenbereichs.
    - Erforderliches Feld: name
    """

    name: str = Field(..., description="Name des Themenbereichs")
    description: str | None = Field(
        default=None, description="Beschreibung des Themenbereichs"
    )


class ThemenbereichUpdate(BaseModel):
    """
    Schema fuer das Update eines bestehenden Themenbereichs.
    - Erforderliches Feld: name
    """

    name: str = Field(..., description="Name des Themenbereichs")
    description: str | None = Field(
        default=None, description="Beschreibung des Themenbereichs"
    )


class ThemenbereichResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen Themenbereich."""

    themenbereich_id: int
    name: str
    description: str | None
