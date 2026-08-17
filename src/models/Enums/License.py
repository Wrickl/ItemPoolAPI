from typing import Optional

from sqlmodel import Field, SQLModel


class LicenseBase(SQLModel):
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name der Lizenz",

    )
    description: Optional[str] = Field(
        default=None,
        description="Beschreibung der Lizenz",
    )

    # TODO Inklusive Testsfälle und Automatisch Daten befüllung


class License(LicenseBase, table=True):
    __tablename__ = "license"
    license_id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

# class License(str, enum.Enum):
#     CC0 = "CC0"
#     CC_BY = "CC_BY"
#     CC_BY_SA = "CC_BY_SA"
#     CC_BY_ND = "CC_BY_ND"
#     CC_BY_NC = "CC_BY_NC"
#     CC_BY_NC_SA = "CC_BY_NC_SA"
#     CC_BY_NC_ND = "CC_BY_NC_ND"

# TODO Für Ausarbeitung: Prüfen ob alle diese Lizenzen wirklich benötigt und sinnvoll sind
