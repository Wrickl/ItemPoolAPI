"""Hier werden die Datenbankmodelle für ContentPiece definiert. Ein ContentPiece ist ein Baustein mit einem definierten DataType, der in verschiedenen ItemTypes verwendet werden kann."""

from os import getenv
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Session
from .content_section_content_piece import ContentSectionContentPiece

if TYPE_CHECKING:
    from .content_types import DataType
    from .contentsection import ContentSection
    from ..complextype import ComplexType


class ContentPieceBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)
    data_type_id: int = Field(foreign_key="DataType.data_type_id")
    complex_type_id: UUID | None = Field(default=None, foreign_key="complex_type.id")


class ContentPiece(ContentPieceBase, table=True):
    __tablename__ = "ContentPiece"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    data_type: "DataType" = Relationship(back_populates="content_pieces")
    complex_type: "ComplexType" = Relationship()
    content_sections: list["ContentSection"] = Relationship(
        back_populates="content_pieces",
        link_model=ContentSectionContentPiece,
    )

    def validate_complex_type(self, session: Session) -> None:
        """Validiert, dass complex_type_id nur für bestimmte DataTypes gesetzt sein darf.

        Die erlaubten DataTypes werden über die ENV-Variable ALLOWED_COMPLEX_TYPE_DATATYPES
        definiert (kommasepariert, z.B. "JSON,JSONB").
        Raises:
            ValueError: Wenn complex_type_id gesetzt ist, aber DataType nicht erlaubt ist
        """
        allowed_datatypes = getenv("ALLOWED_COMPLEX_TYPE_DATATYPES", "JSON,JSONB").split(",")
        allowed_datatypes = [dt.strip().upper() for dt in allowed_datatypes]

        if self.complex_type_id is not None:
            # Lade den DataType falls nicht bereits geladen
            if not hasattr(self, 'data_type') or self.data_type is None:
                from .content_types import DataType
                loaded_data_type = session.get(DataType, self.data_type_id)
                if loaded_data_type is not None:
                    self.data_type = loaded_data_type

            if self.data_type and self.data_type.name.upper() not in allowed_datatypes:
                raise ValueError(
                    f"ComplexType kann nur für folgende DataTypes gesetzt werden: {', '.join(allowed_datatypes)}. "
                    f"Aktueller DataType: {self.data_type.name}"
                )
