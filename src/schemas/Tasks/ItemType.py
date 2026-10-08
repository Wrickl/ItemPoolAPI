from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ItemTypeCreate(BaseModel):
    name: str = Field(..., description="Name des Item Typs")
    description: str | None = Field(default=None, description="Beschreibung des Item Typs")
    content_section_ids: list[UUID] = Field(
        default_factory=list,
        description="List der ContentSection fuer diesen ItemType",
    )


class ItemTypeRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    content_section_ids: list[UUID] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
