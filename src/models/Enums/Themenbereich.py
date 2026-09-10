from sqlmodel import Field, SQLModel


class ThemenbereichBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name des Themenbereichs",
    )
    description: str | None = Field(
        default=None,
        description="Beschreibung des Themenbereichs",
    )


class Themenbereich(ThemenbereichBase, table=True):
    __tablename__ = "themenbereich"
    themenbereich_id: int | None = Field(
        default=None,
        primary_key=True,
    )
