"""Hier werden die Datenmodelle der Komplexen JSON Types abgelegt."""
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ComplexTypeBase(SQLModel):
    """ Ein KomplexType beschreibt über das JSON Format die Struktur eines komplexen JSON Objektes,
     um die Weiterverarbeitung zu erleichtern. """
    name: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="Name des komplexen Typs",
    )
    description: str | None = Field(
        default=None,
        description="Beschreibung des komplexen Typs",
    )
    json_schema: Optional[dict] = Field(sa_column=Column(JSON),
                                            description="Beschreibung des komplexen Typs in Form eines JSON Schemas")


class ComplexType(ComplexTypeBase, table=True):
    __tablename__ = "complex_type"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
