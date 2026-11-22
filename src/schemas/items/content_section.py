from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentSectionCreate(BaseModel):
    """
    Schema fuer die Erstellung einer neuen Content Section
    - Erforderliche Felder: name
    """

    name: str = Field(..., description="Name der Content Section")
    description: str | None = Field(default=None, description="Beschreibung der Content Section")
    contentPieces: list[UUID] = Field(
        default_factory=list,
        description="Liste der ContentPiece IDs, die dieser Content Section zugeordnet werden sollen",
    )


class ContentSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    contentPieces: list[UUID] = Field(default_factory=list)
