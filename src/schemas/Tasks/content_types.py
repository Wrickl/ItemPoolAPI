from uuid import UUID

from pydantic import BaseModel, Field

from .item_type import ItemTypePluginAssignment


class ContentSectionRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None


class ItemTypeContentSectionAssign(BaseModel):
    content_section_ids: list[UUID] = Field(min_length=1)


class ItemTypeDetailRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    content_sections: list[ContentSectionRead] = Field(default_factory=list)
    plugins: list[ItemTypePluginAssignment] = Field(default_factory=list)
