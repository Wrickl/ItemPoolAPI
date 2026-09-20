from uuid import UUID

from pydantic import BaseModel, Field


class OrganisationCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Organisation.
    """

    #id : UUID = Field(..., description="Eindeutige ID der Organisation")
    name: str | None  = Field(default=None, description="Name der Organisation")
    contact: str | None = Field(default=None, description="Kontaktinformationen der Organisation")
    faculty: str | None = Field(default=None, description="Fakultät der Organisation")
    ### TODO sollte es erforderliche (required Felder geben)?
class OrganisationUpdate(BaseModel):
    """
    Schema fuer das Update einer bestehenden Organisation.
    """

    name: str | None  = Field(default=None, description="Name der Organisation")
    contact: str | None = Field(default=None, description="Kontaktinformationen der Organisation")
    faculty: str | None = Field(default=None, description="Fakultät der Organisation")


class OrganisationResponse(BaseModel):
    """Response-Modell fuer eine erstellte oder gelesene Organisation."""

    id: UUID
    name: str | None
    contact: str | None
    faculty: str | None
