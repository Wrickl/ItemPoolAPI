from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from Util.item_type import build_item_type_detail, build_content_piece_read

from database.dao_connection import get_session
from models import ContentSectionItemType, ContentSection, ContentPiece
from models.Tasks.content_types import (
    ItemType,
)
from schemas import ItemTemplateResponse
from schemas.Tasks.ItemType import ItemTypeCreate, ItemTypeRead
from schemas.Tasks.content_types import (
    ItemTypeDetailRead,
)

router = APIRouter(tags=["ItemType"])


@router.post("/createItemType", response_model=ItemTypeRead)
async def create_item_type(item_type_data: ItemTypeCreate, session: Session = Depends(get_session)):
    """Legt einen neuen ItemType an."""
    existing = session.exec(select(ItemType).where(ItemType.name == item_type_data.name)).first()
    if existing:
        raise HTTPException(status_code=409,detail=f"ItemType '{item_type_data.name}' existiert bereits")

    item_type = ItemType.model_validate(item_type_data)
    session.add(item_type)
    session.flush()    # Ensure the item_type gets an ID before committing
    session.add_all(
        [
            ContentSectionItemType(content_section_id=content_section, item_type_id=item_type.id)
            for content_section in item_type_data.content_section_ids
        ]
    )
    session.commit()
    session.refresh(item_type)
    return ItemTypeRead.model_validate(item_type)


@router.get("/getAllItemTypes", response_model=list[ItemTypeDetailRead])
async def get_all_item_types(session: Session = Depends(get_session)):
    """Gibt alle ItemTypes inklusive zugewiesener ContentPieces zurueck."""
    item_types = session.exec(select(ItemType).order_by(ItemType.name)).all()
    return [build_item_type_detail(item_type, session) for item_type in item_types]


@router.get("/getItemTypeById/{item_type_id}", response_model=ItemTypeDetailRead)
async def get_itemtype(item_type_id: UUID, session: Session = Depends(get_session)):
    """Liefert eine leere Item-Vorlage für einen ItemType inklusive aller Sections und ContentPieces."""
    item_type = session.get(ItemType, item_type_id)
    if item_type is None:
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden")
    return build_item_type_detail(item_type, session)

@router.get("/getItemTypeById/{item_type_id}/", response_model=ItemTemplateResponse)
async def get_itemtype_full(item_type_id: UUID, session: Session = Depends(get_session)):
    """Liefert eine leere Item-Vorlage für einen ItemType inklusive aller Sections und ContentPieces."""
    item_type = session.exec(select(ItemType)
        .where(ItemType.id == item_type_id)
        .options(
            selectinload(ItemType.content_sections)
            .selectinload(ContentSection.content_pieces)
            .selectinload(ContentPiece.data_type)
        )).first()

    if item_type is None:
        raise HTTPException(status_code=404,detail=f"ItemType {item_type_id} nicht gefunden")

    content_sections = []
    for section2get in sorted(item_type.content_sections, key=lambda section2get: section2get.name):
        if section2get.id is None:
            continue
        content_pieces = [
            build_content_piece_read(content_piece)
            for content_piece in sorted(section2get.content_pieces, key=lambda piece: piece.name)
            if content_piece.id is not None
        ]
        content_sections.append({
                "id": section2get.id,
                "name": section2get.name,
                "description": section2get.description,
                "content_pieces": content_pieces})
    return {
        "item_type_id": item_type.id,
        "item_type_name": item_type.name,
        "item_type_description": item_type.description,
        "content_sections": content_sections,
    }
