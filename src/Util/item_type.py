import os

from fastapi import HTTPException
from sqlmodel import Session

from models import ContentPiece, DataType, ItemType
from models.complextype import ComplexType
from schemas import (
    ContentPieceRead,
    ContentPieceReadFull,
    ContentSectionRead,
    DataTypeRead,
    ItemTypeDetailRead,
)


def get_configured_upload_data_types() -> list[str]:
    raw = os.getenv("CLI_UPLOAD_DATA_TYPE", "").strip()
    if not raw:
        return []

    upload_types: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        normalized = token.strip().upper()
        if not normalized or normalized in seen:
            continue
        upload_types.append(normalized)
        seen.add(normalized)
    return upload_types


def build_content_piece_read(content_piece: ContentPiece) -> ContentPieceRead:
    if content_piece.id is None:
        raise HTTPException(status_code=500, detail="ContentPiece ohne ID gefunden")
    return ContentPieceRead(
        id=content_piece.id,
        name=content_piece.name,
        description=content_piece.description,
        data_type_id=content_piece.data_type_id,
        data_type_name=content_piece.data_type.name
        if content_piece.data_type
        else None,
        complex_type_id=content_piece.complex_type_id
        if content_piece.complex_type_id else None,
    )


def build_data_type_read(data_type: DataType) -> DataTypeRead:
    if data_type.data_type_id is None:
        raise HTTPException(status_code=500, detail="DataType ohne ID gefunden")
    return DataTypeRead(
        data_type_id=data_type.data_type_id,
        name=data_type.name,
        description=data_type.description,
        source=data_type.source,
    )


def build_item_type_detail(item_type: ItemType, session: Session) -> ItemTypeDetailRead:
    if item_type.id is None:
        raise HTTPException(status_code=500, detail="ItemType ohne ID gefunden")
    content_sections = [
        ContentSectionRead(
            id=content_section.id,
            name=content_section.name,
            description=content_section.description,
        )
        for content_section in item_type.content_sections
        if content_section.id is not None
    ]
    return ItemTypeDetailRead(
        id=item_type.id,
        name=item_type.name,
        description=item_type.description,
        content_sections=content_sections,
    )


def build_full_content_piece_read(content_piece:ContentPiece, session: Session) -> ContentPieceReadFull:
    if content_piece.id is None:
        raise HTTPException(status_code=500, detail="ContentPiece ohne ID gefunden")
    if content_piece.complex_type_id is None:
        return ContentPieceReadFull(
            id=content_piece.id,
            name=content_piece.name,
            description=content_piece.description,
            data_type_id=content_piece.data_type_id,
            data_type_name=content_piece.data_type.name
            if content_piece.data_type
            else None,
            complex_type_id=None,
            complex_schema=None,)
    else:
        schema = session.get(ComplexType, content_piece.complex_type_id)
        return ContentPieceReadFull(
            id=content_piece.id,
            name=content_piece.name,
            description=content_piece.description,
            data_type_id=content_piece.data_type_id,
            data_type_name=content_piece.data_type.name
            if content_piece.data_type
            else None,
            complex_type_id=content_piece.complex_type_id,
            complex_schema=schema.json_schema if schema else None,)

