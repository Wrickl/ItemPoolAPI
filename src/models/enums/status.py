from uuid import uuid4, UUID

from sqlmodel import Field, SQLModel


class StatusBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name des Status",
    )
    description: str | None = Field(
        default=None,
        description="Beschreibung des Status",
    )

class Status(StatusBase, table=True):
    __tablename__ = "status"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
