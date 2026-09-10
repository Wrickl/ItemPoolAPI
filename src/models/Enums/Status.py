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

    # TODO Inklusive Testsfälle und Automatisch Daten befüllung


class Status(StatusBase, table=True):
    __tablename__ = "status"
    status_id: int | None = Field(
        default=None,
        primary_key=True,
    )
