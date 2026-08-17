from typing import Optional

from sqlmodel import Field, SQLModel


class StatusBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name des Status",

    )
    description: Optional[str] = Field(
        default=None,
        description="Beschreibung des Status",
    )

    # TODO Inklusive Testsfälle und Automatisch Daten befüllung


class Status(StatusBase, table=True):
    __tablename__ = "status"
    status_id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
