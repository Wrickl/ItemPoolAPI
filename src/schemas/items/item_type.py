from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ItemTypePluginAssignment(BaseModel):
    plugin_name: str = Field(min_length=1, max_length=255)
    content_section_id: UUID
    content_piece_id: UUID


class ItemTypeCreate(BaseModel):
    name: str = Field(..., description="Name des Item Typs")
    description: str | None = Field(default=None, description="Beschreibung des Item Typs")
    content_section_ids: list[UUID] = Field(
        default_factory=list,
        description="List der ContentSection fuer diesen ItemType",
    )
    plugins: list[ItemTypePluginAssignment] = Field(default_factory=list)


class ItemTypeRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    content_section_ids: list[UUID] = Field(default_factory=list)
    plugins: list[ItemTypePluginAssignment] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
