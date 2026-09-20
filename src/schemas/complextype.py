from pydantic import BaseModel, Field


class ComplexTypeCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen komplexen Typs
    - Erforderliche Felder: name, description
    """

    name: str = Field(..., description="Name des komplexen Typs")
    description: str | None = Field(default=None, description="Beschreibung des komplexen Typs")
    json_schema: dict = Field(..., description="Beschreibung des komplexen Typs in Form eines JSON Schemas")

class ComplexTypeUpdate(BaseModel):
    pass


class ComplexTypeResponse(BaseModel):
    """Response-Modell fuer einen erstellten oder gelesenen komplexen Typ."""

    complex_type_id: int | None
    name: str | None
    description: str | None
    json_schema: dict | None
