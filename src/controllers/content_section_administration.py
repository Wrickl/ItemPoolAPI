from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from util.content_section import (
    add_content_section_pieces,
    build_content_section_response,
    build_content_section_responses,
    deduplicate_uuids,
    load_content_piece_ids_by_section,
    validate_content_piece_ids,
)
from util.item_type import build_item_type_detail
from database import get_session
from models import (
    ContentSection,
    ContentSectionContentPiece,
    ContentSectionItem,
    ContentSectionItemType,
    ItemType,
)
from models.items.item_type_plugin import ItemTypePlugin
from models.error import ResourceInUseException
from schemas import ItemTypeDetailRead
from schemas.items.content_section import ContentSectionResponse, ContentSectionCreate
from services.PluginSystem import METADATA_SECTION_NAME

router = APIRouter(tags=["ContentSection"])


@router.get("/getAllContentSections", response_model=list[ContentSectionResponse])
def get_all_content_sections(session: Session = Depends(get_session)):
    """Gibt alle ContentSections zurück."""
    content_sections = session.exec(select(ContentSection)).all()
    return build_content_section_responses(session, content_sections)


@router.get("/getContentSectionsById/{content_section_id}", response_model=ContentSectionResponse)
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


@router.post("/createContentSection", response_model=ContentSectionResponse)
def create_content_section(content_section_data: ContentSectionCreate, session: Session = Depends(get_session)):
    """Erstellt eine neue ContentSection."""
    if content_section_data.name == METADATA_SECTION_NAME:
        raise HTTPException(status_code=400, detail="Die Plugin-Metadaten-Section ist reserviert")
    requested_content_piece_ids = deduplicate_uuids(content_section_data.contentPieces or [])

    validate_content_piece_ids(session, requested_content_piece_ids)

    content_section = ContentSection(
        name=content_section_data.name,
        description=content_section_data.description,
    )

    try:
        session.add(content_section)
        session.flush()
        add_content_section_pieces(session, content_section.id, requested_content_piece_ids)
        session.commit()
        session.refresh(content_section)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="ContentSection konnte nicht angelegt werden.") from exc
    return build_content_section_response(content_section, requested_content_piece_ids)


@router.get("/getContentSectionsForItemType/{item_type_id}", response_model=list[ContentSectionResponse])
def get_content_sections_for_item_type(item_type_id: UUID, session: Session = Depends(get_session)):
    """Gibt alle ContentSections für einen bestimmten ItemType zurück."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden")
    return build_content_section_responses(session, item_type.content_sections)


@router.put("/updateContentSection/{content_section_id}", response_model=ContentSectionResponse)
def update_content_section(content_section_id: UUID, content_section_data: ContentSectionCreate,
                           session: Session = Depends(get_session)):
    """Aktualisiert eine bestehende ContentSection anhand ihrer ID."""
    content_section = session.get(ContentSection, content_section_id)
    if content_section is None:
        raise HTTPException(status_code=404, detail=f"ContentSection {content_section_id} nicht gefunden")
    if content_section.name == METADATA_SECTION_NAME or content_section_data.name == METADATA_SECTION_NAME:
        raise HTTPException(status_code=400, detail="Die Plugin-Metadaten-Section wird automatisch verwaltet")
    requested_content_piece_ids = deduplicate_uuids(content_section_data.contentPieces or [])
    assignments = session.exec(
        select(ItemTypePlugin).where(ItemTypePlugin.content_section_id == content_section_id)
    ).all()
    if any(assignment.content_piece_id not in requested_content_piece_ids for assignment in assignments):
        raise HTTPException(status_code=409, detail="Ein zugeordnetes Plugin benötigt dieses ContentPiece")
    validate_content_piece_ids(session, requested_content_piece_ids)
    content_section.name = content_section_data.name
    content_section.description = content_section_data.description
    try:
        session.add(content_section)
        session.flush()
        session.exec(delete(ContentSectionContentPiece).where(
            ContentSectionContentPiece.content_section_id == content_section_id))
        add_content_section_pieces(session, content_section.id, requested_content_piece_ids)
        session.commit()
        session.refresh(content_section)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="ContentSection konnte nicht aktualisiert werden.") from exc

    return build_content_section_response(content_section, requested_content_piece_ids)


@router.delete("/deleteContentSection/{content_section_id}", status_code=204)
def delete_content_section(content_section_id: UUID, session: Session = Depends(get_session)):
    """Löscht eine ContentSection anhand ihrer ID."""
    content_section = session.get(ContentSection, content_section_id)
    if content_section is None:
        raise HTTPException(status_code=404, detail=f"ContentSection {content_section_id} nicht gefunden")
    if content_section.name == METADATA_SECTION_NAME:
        raise HTTPException(status_code=400, detail="Die Plugin-Metadaten-Section wird automatisch verwaltet")

    item_type_usage = session.scalar(
        select(func.count())
        .select_from(ContentSectionItemType)
        .where(ContentSectionItemType.content_section_id == content_section_id)
    )
    item_usage = session.scalar(
        select(func.count())
        .select_from(ContentSectionItem)
        .where(ContentSectionItem.content_section_id == content_section_id)
    )
    usage_count = item_type_usage + item_usage
    if usage_count:
        raise ResourceInUseException(usage_count)

    session.delete(content_section)
    session.commit()
    return {"message": f"ContentSection {content_section_id} erfolgreich gelöscht"}


@router.post("/assignContentSectionsToItemType/{item_type_id}/{content_section_id_to_assing}",
             response_model=ItemTypeDetailRead)
async def assign_content_section_to_item_type(item_type_id: UUID, content_section_id_to_assing: UUID,
                                              session: Session = Depends(get_session)):
    """Ordnet einem ItemType beliebig viele ContentSections zu."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden")
    content_section = session.get(ContentSection, content_section_id_to_assing)
    if content_section is None:
        raise HTTPException(status_code=404,
                            detail=f"ContentSection mit ID {content_section_id_to_assing} nicht gefunden")
    if content_section.name == METADATA_SECTION_NAME:
        raise HTTPException(status_code=400, detail="Die Plugin-Metadaten-Section wird automatisch verwaltet")

    if any(section.id == content_section_id_to_assing for section in item_type.content_sections):
        raise HTTPException(
            status_code=409,
            detail=f"ContentSection {content_section_id_to_assing} ist bereits dem ItemType {item_type_id} zugeordnet",
        )

    item_type.content_sections.append(content_section)
    try:
        session.add(item_type)
        session.commit()
        session.refresh(item_type)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"ContentSection {content_section_id_to_assing} konnte nicht zugeordnet werden",
        ) from exc

    return build_item_type_detail(item_type, session)
