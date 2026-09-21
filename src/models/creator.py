from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .organisation import Organisation
    from .Tasks.tasks import Item


class CreatorBase(SQLModel):
    contact: str | None = Field(default=None, max_length=255)
    name: str = Field(..., max_length=255)
    ### Todo Rechte Rollen Konzept erstellen
    role: int
    organisation_id: UUID = Field(foreign_key="Organisation.id")


class Creator(CreatorBase, table=True):
    __tablename__ = "creator"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    organisation: "Organisation" = Relationship(back_populates="creators")
    items: list["Item"] = Relationship(back_populates="author")
