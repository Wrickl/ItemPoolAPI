from encodings.rot_13 import rot13
from uuid import UUID

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from Util.item_type import build_item_type_detail
from database import get_session
from models import ContentPiece, ContentSection, ContentSectionContentPiece, ItemType
from schemas import ItemTypeDetailRead
from schemas.Tasks.content_section import ContentSectionResponse, ContentSectionCreate

router = APIRouter()


def deduplicate_uuids(values: list[UUID]) -> list[UUID]:
    seen: set[UUID] = set()
    unique_values: list[UUID] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def load_content_piece_ids_by_section(session: Session, section_ids: list[UUID]) -> dict[UUID, list[UUID]]:
    if not section_ids:
        return {}

    rows = session.exec(
        select(ContentSectionContentPiece).where(
            ContentSectionContentPiece.content_section_id.in_(section_ids)
        )
    ).all()

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


@router.get("/getAllContentSections", response_model=list[ContentSectionResponse], tags=["ContentSection"])
def get_all_content_sections(session: Session = Depends(get_session)):
    """Gibt alle ContentSections zurück."""
    content_sections = session.exec(select(ContentSection)).all()
    section_ids = [content_section.id for content_section in content_sections if content_section.id is not None]
    content_piece_ids_by_section = load_content_piece_ids_by_section(session, section_ids)
    return [
        build_content_section_response(content_section, content_piece_ids_by_section.get(content_section.id,
                                                                                         []) if content_section.id else [])
        for content_section in content_sections
    ]


@router.get("/getContentSectionsById/{content_section_id}", response_model=ContentSectionResponse,
            tags=["ContentSection"])
def get_content_sections_by_id(content_section_id: UUID, session: Session = Depends(get_session)):
    """Gibt eine ContentSection anhand ihrer ID zurück."""
    content_section = session.get(ContentSection, content_section_id)
    if content_section is None:
        raise HTTPException(
            status_code=404,
            detail=f"ContentSection {content_section_id} nicht gefunden",
        )
    content_piece_ids = load_content_piece_ids_by_section(session, [content_section_id]).get(content_section_id, [])
    return build_content_section_response(content_section, content_piece_ids)


@router.post("/createContentSection", response_model=ContentSectionResponse, tags=["ContentSection"])
def create_content_section(content_section_data: ContentSectionCreate, session: Session = Depends(get_session)):
    """Erstellt eine neue ContentSection."""
    requested_content_piece_ids = deduplicate_uuids(content_section_data.contentPieces or [])

    if requested_content_piece_ids:
        existing_content_piece_ids = set(
            session.exec(
                select(ContentPiece.id).where(ContentPiece.id.in_(requested_content_piece_ids))
            ).all()
        )
        missing_content_piece_ids = [
            content_piece_id
            for content_piece_id in requested_content_piece_ids
            if content_piece_id not in existing_content_piece_ids
        ]
        if missing_content_piece_ids:
            raise HTTPException(
                status_code=404,
                detail=(
                        "Folgende ContentPieces wurden nicht gefunden: "
                        + ", ".join(str(content_piece_id) for content_piece_id in missing_content_piece_ids)
                ),
            )

    content_section = ContentSection(
        name=content_section_data.name,
        description=content_section_data.description,
    )

    try:
        session.add(content_section)
        session.flush()
        session.add_all(
            [
                ContentSectionContentPiece(content_section_id=content_section.id,content_piece_id=content_piece_id)
                for content_piece_id in requested_content_piece_ids
            ]
        )
        session.commit()
        session.refresh(content_section)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409,detail="ContentSection konnte nicht angelegt werden.") from exc
    return build_content_section_response(content_section, requested_content_piece_ids)

@router.get("/getContentSectionsForItemType/{item_type_id}", response_model=list[ContentSectionResponse],
            tags=["ContentSection"])
def get_content_sections_for_item_type(item_type_id: UUID, session: Session = Depends(get_session)):
    """Gibt alle ContentSections für einen bestimmten ItemType zurück."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404,detail=f"ItemType {item_type_id} nicht gefunden")
    content_sections = item_type.content_sections
    section_ids = [content_section.id for content_section in content_sections if content_section.id is not None]
    content_piece_ids_by_section = load_content_piece_ids_by_section(session, section_ids)
    return [
        build_content_section_response(content_section, content_piece_ids_by_section.get(content_section.id,[]) if content_section.id else [])
        for content_section in content_sections
    ]

@router.put("/updateContentSection/{content_section_id}", response_model=ContentSectionResponse, tags=["ContentSection"])
def update_content_section(content_section_id: UUID, content_section_data: ContentSectionCreate, session: Session = Depends(get_session)):
    """Aktualisiert eine bestehende ContentSection anhand ihrer ID."""
    content_section = session.get(ContentSection, content_section_id)
    if content_section is None:
        raise HTTPException(status_code=404, detail=f"ContentSection {content_section_id} nicht gefunden")
    requested_content_piece_ids = deduplicate_uuids(content_section_data.contentPieces or [])
    if requested_content_piece_ids:
        existing_content_piece_ids = set(
            session.exec(
                select(ContentPiece.id).where(ContentPiece.id.in_(requested_content_piece_ids))
            ).all()
        )
        missing_content_piece_ids = [
            content_piece_id
            for content_piece_id in requested_content_piece_ids
            if content_piece_id not in existing_content_piece_ids
        ]
        if missing_content_piece_ids:
            raise HTTPException(
                status_code=404,
                detail=(
                        "Folgende ContentPieces wurden nicht gefunden: "
                        + ", ".join(str(content_piece_id) for content_piece_id in missing_content_piece_ids)
                ),
            )
    content_section.name = content_section_data.name
    content_section.description = content_section_data.description
    try:
        session.add(content_section)
        session.flush()
        session.exec(delete(ContentSectionContentPiece).where(ContentSectionContentPiece.content_section_id == content_section_id))
        session.add_all(
            [
                ContentSectionContentPiece(content_section_id=content_section.id,content_piece_id=content_piece_id)
                for content_piece_id in requested_content_piece_ids
            ]
        )
        session.commit()
        session.refresh(content_section)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409,detail="ContentSection konnte nicht aktualisiert werden.") from exc

    return build_content_section_response(content_section, requested_content_piece_ids)
@router.delete("/deleteContentSection/{content_section_id}", status_code=204, tags=["ContentSection"])
def delete_content_section(content_section_id: UUID, session: Session = Depends(get_session)):
    """Löscht eine ContentSection anhand ihrer ID."""
    content_section = session.get(ContentSection, content_section_id)
    if content_section is None:
        raise HTTPException(status_code=404, detail=f"ContentSection {content_section_id} nicht gefunden")
    ## TODO Implement Conflict if content section is in use in item type, if yes, raise 409
    session.delete(content_section)
    session.commit()
    return {"message": f"ContentSection {content_section_id} erfolgreich gelöscht"}
@router.post("/assignContentSectionsToItemType/{item_type_id}/{content_section_id_to_assing}",
             response_model=ItemTypeDetailRead,tags=["ContentSection"])
async def assign_content_section_to_item_type(item_type_id: UUID, content_section_id_to_assing: UUID,session: Session = Depends(get_session)):
    """Ordnet einem ItemType beliebig viele ContentSections zu."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404,detail=f"ItemType {item_type_id} nicht gefunden")
    content_section = session.get(ContentSection, content_section_id_to_assing)
    if content_section is None:
        raise HTTPException(status_code=404,detail=f"ContentSection mit ID {content_section_id_to_assing} nicht gefunden")
    if content_section_id_to_assing in item_type.content_sections:
        raise HTTPException(status_code=400,detail=f"ContentSection mit ID {content_section_id_to_assing} ist bereits dem ItemType {item_type_id} zugeordnet")
    session.add(item_type)
    session.commit()
    session.refresh(item_type)
    return build_item_type_detail(item_type, session)
