from typing import Optional

from pydantic import BaseModel, Field

from ..contentblocks import ContentBlock


class DatabaseCreate(BaseModel):
    """Schema fuer die Erstellung einer Datenbank-Definition ueber die API."""
    """TODO Anpassung mit Block definitionen für DDL-String, Datenbankschema als Bild und als Mermaid (o.ä) String"""
    ddl_string: Optional[str] = Field(default=None, description="DDL-String der Datenbank")
    version: Optional[str] = Field(default=None, description="Version des SQL-Dialekts z.B. PostgreSQL 17.10")
    dialect: Optional[str] = Field(default=None, description="SQL-Dialekt, z.B. PostgreSQL")
    weitere_eigenschaften: list[ContentBlock] = []


class DatabaseUpdate(BaseModel):
    pass


class DatabaseResponse(BaseModel):
    """Response-Modell fuer eine erstellte oder gelesene Datenbank-Definition."""

    database_id: Optional[int]
    ddl_string: Optional[str]
    version: Optional[str]
    dialect: Optional[str]
    weitere_eigenschaften: list[ContentBlock]

    model_config = {
        "from_attributes": True
    }
