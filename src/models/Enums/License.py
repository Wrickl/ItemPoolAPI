from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class LicenseBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name der Lizenz",
    )
    description: str | None = Field(
        default=None,
        description="Beschreibung der Lizenz",
    )

    # TODO Inklusive Testsfälle und Automatisch Daten befüllung


class License(LicenseBase, table=True):
    __tablename__ = "license"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
