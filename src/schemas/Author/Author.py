from uuid import UUID

from pydantic import ConfigDict
from sqlmodel import SQLModel


class CreatorCreate(SQLModel):
    name: str
    contact: str | None = None
    role: int
    organisation_id: UUID


class CreatorRead(SQLModel):
    author_id: UUID
    name: str
    contact: str | None = None
    role: int
    organisation_id: UUID
    model_config = ConfigDict(from_attributes=True)


class CreatorUpdate(SQLModel):
    pass


class CreatorResponse(SQLModel):
    author_id: UUID
    name: str
    contact: str | None = None
    role: int
