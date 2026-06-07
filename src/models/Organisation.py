from typing import List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel
if TYPE_CHECKING:
    from .Author import Creator


class OrganisationBase(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    contact: str | None = Field(default=None, max_length=255)
    faculty: str | None = Field(default=None, max_length=255)

class Organisation(OrganisationBase, table=True):
    __tablename__ = "Organisation"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True
    )
    creators: List["Creator"] = Relationship(
        back_populates="organisation"
    )
