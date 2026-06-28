from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel

from ...models.author import CreatorBase


class CreatorCreate(CreatorBase):
    pass


class CreatorRead(SQLModel):
    author_id: UUID
    name: str | None = None
    email: str | None = None
    role: int
    organisation_name: str | None = None
    model_config = ConfigDict(from_attributes=True)
