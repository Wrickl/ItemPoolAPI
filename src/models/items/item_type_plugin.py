from uuid import UUID

from sqlmodel import Field, SQLModel


class ItemTypePlugin(SQLModel, table=True):
    __tablename__ = "ItemTypePlugin"

    item_type_id: UUID = Field(foreign_key="ItemType.id", primary_key=True)
    plugin_name: str = Field(primary_key=True, max_length=255)
    content_section_id: UUID = Field(foreign_key="content_section.id")
    content_piece_id: UUID = Field(foreign_key="ContentPiece.id")
    output_content_piece_id: UUID = Field(foreign_key="ContentPiece.id")
