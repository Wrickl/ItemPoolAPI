from typing import Optional

from pydantic import BaseModel, Field


class DatabaseCreate(BaseModel):
    """Schema fuer die Erstellung einer Datenbank-Definition ueber die API."""

    ddl_string: Optional[str] = Field(default=None, description="DDL-String der Datenbank")
    version: Optional[str] = Field(default=None, description="Version des Schemas")
    dialect: Optional[str] = Field(default=None, description="SQL-Dialekt, z.B. PostgreSQL")
    description: Optional[str] = Field(default=None, description="Freitext-Beschreibung")


class DatabaseResponse(BaseModel):
    """Response-Modell fuer eine erstellte oder gelesene Datenbank-Definition."""

    database_id: Optional[int]
    ddl_string: Optional[str]
    version: Optional[str]
    dialect: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True

