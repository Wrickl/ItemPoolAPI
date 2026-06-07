from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .Organisation import Organisation
    from .Tasks.Tasks import Item


class CreatorBase(SQLModel):
    email: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    role: int
    organisation_id: UUID = Field(foreign_key="Organisation.id")


class Creator(CreatorBase, table=True):
    __tablename__ = "Author"
    author_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
    )
    organisation: "Organisation" = Relationship(
        back_populates="creators"
    )
    items: List["Item"] = Relationship(
        back_populates="author"
    )
