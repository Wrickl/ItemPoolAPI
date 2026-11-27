from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from models import ContentPiece, ContentSection, ContentSectionContentPiece
from schemas import ContentSectionResponse


def deduplicate_uuids(values: list[UUID]) -> list[UUID]:
    return list(dict.fromkeys(values))


def validate_content_piece_ids(session: Session, requested_ids: list[UUID]) -> None:
    if not requested_ids:
        return
    existing_ids = set(
        session.exec(select(ContentPiece.id).where(ContentPiece.id.in_(requested_ids))).all()
    )
    missing_ids = [piece_id for piece_id in requested_ids if piece_id not in existing_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail="Folgende ContentPieces wurden nicht gefunden: "
            + ", ".join(str(piece_id) for piece_id in missing_ids),
        )


def load_content_piece_ids_by_section(session: Session, section_ids: list[UUID]) -> dict[UUID, list[UUID]]:
    if not section_ids:
        return {}

    rows = session.exec(
        select(ContentSectionContentPiece).where(
            ContentSectionContentPiece.content_section_id.in_(section_ids)
        )).all()

    content_piece_ids_by_section: dict[UUID, list[UUID]] = {section_id: [] for section_id in section_ids}
    for row in rows:
        content_piece_ids_by_section.setdefault(row.content_section_id, []).append(row.content_piece_id)
    return content_piece_ids_by_section


def build_content_section_response(content_section: ContentSection,
                                   content_piece_ids: list[UUID] | None = None) -> ContentSectionResponse:
    if content_section.id is None:
        raise HTTPException(status_code=500, detail="ContentSection ohne ID gefunden")

    return ContentSectionResponse(
        id=content_section.id,
        name=content_section.name,
        description=content_section.description,
        contentPieces=content_piece_ids or [],
    )


def build_content_section_responses(
    session: Session, sections: Sequence[ContentSection]) -> list[ContentSectionResponse]:

    section_ids = [section.id for section in sections if section.id is not None]
    piece_ids = load_content_piece_ids_by_section(session, section_ids)
    return [
        build_content_section_response(section, piece_ids.get(section.id, []) if section.id else [])
        for section in sections
    ]


def add_content_section_pieces(session: Session, section_id: UUID, piece_ids: list[UUID]) -> None:

    session.add_all(
        ContentSectionContentPiece(content_section_id=section_id, content_piece_id=piece_id)
        for piece_id in piece_ids
    )
