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
    license_id: int | None = Field(
        default=None,
        primary_key=True,
    )
