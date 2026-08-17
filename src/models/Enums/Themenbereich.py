from typing import Optional

from sqlmodel import Field, SQLModel


class ThemenbereichBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name des Themenbereichs",
    )
    description: Optional[str] = Field(
        default=None,
        description="Beschreibung des Themenbereichs",
    )

    # TODO Inklusive Testsfälle und Automatisch Daten befüllung


class Themenbereich(ThemenbereichBase, table=True):
    __tablename__ = "themenbereich"
    themenbereich_id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
