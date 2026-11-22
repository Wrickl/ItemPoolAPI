from uuid import UUID

from pydantic import BaseModel, Field


class LicenseCreate(BaseModel):
    """
    Schema fuer die Erstellung einer neuen Lizenz
    - Erforderliche Felder: name, description
    """

    name: str = Field(..., description="Name der Lizenz")
    description: str | None = Field(default=None, description="Beschreibung der Lizenz")


class LicenseUpdate(BaseModel):
    pass


class LicenseResponse(BaseModel):
    """Response-Modell fuer eine erstellte oder gelesene Lizenz."""

    id: UUID
    name: str
    description: str | None
