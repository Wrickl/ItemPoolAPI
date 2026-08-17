from typing import Optional

from pydantic import BaseModel, Field


class LicenseCreate(BaseModel):
    """
    Schema fuer die Erstellung einer neuen Lizenz ueber die API.

    - Erforderliche Felder: name, description
    """
    name: str = Field(..., description="Name der Lizenz")
    description: Optional[str] = Field(default=None, description="Beschreibung der Lizenz")


class LicenseUpdate(BaseModel):
    pass


class LicenseResponse(BaseModel):
    """Response-Modell fuer eine erstellte oder gelesene Lizenz."""

    license_id: Optional[int]
    name: Optional[str]
    description: Optional[str]
