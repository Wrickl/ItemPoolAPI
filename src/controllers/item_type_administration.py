from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from database.dao_connection import get_session
from models import (
    ContentSectionItemType,
    ContentSection,
    ContentPiece,
    ContentSectionContentPiece,
    DataType,
    ItemType,
    ItemTypePlugin
)
from schemas import (
    ItemTemplateResponse,
    ItemTypeDetailRead,
    ItemTypeCreate,
    ItemTypeRead,
)
from services import PluginSystem
from util.item_type import build_item_type_detail, build_content_piece_read

router = APIRouter(tags=["ItemType"])


@router.post("/createItemType", response_model=ItemTypeRead)
async def create_item_type(item_type_data: ItemTypeCreate, session: Session = Depends(get_session)):
    """Legt einen neuen ItemType an."""
    existing = session.exec(select(ItemType).where(ItemType.name == item_type_data.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"ItemType '{item_type_data.name}' existiert bereits")

    if len(set(item_type_data.content_section_ids)) != len(item_type_data.content_section_ids):
        raise HTTPException(status_code=400, detail="ContentSections dürfen nicht mehrfach zugeordnet werden")
    for section_id in item_type_data.content_section_ids:
        section = session.get(ContentSection, section_id)
        if section is None:
            raise HTTPException(status_code=404, detail=f"ContentSection {section_id} nicht gefunden")
        if section.name == PluginSystem.METADATA_SECTION_NAME:
            raise HTTPException(status_code=400, detail="Die Plugin-Metadaten-Section wird automatisch verwaltet")
    seen_plugins = set()
    for assignment in item_type_data.plugins:
        if assignment.plugin_name in seen_plugins:
            raise HTTPException(status_code=400, detail=f"Plugin {assignment.plugin_name} mehrfach zugeordnet")
        seen_plugins.add(assignment.plugin_name)
        plugin = PluginSystem.plugins.get(assignment.plugin_name)
        if plugin is None:
            raise HTTPException(status_code=400, detail=f"Plugin {assignment.plugin_name} nicht gefunden")
        if assignment.content_section_id not in item_type_data.content_section_ids:
            raise HTTPException(status_code=400, detail="Plugin-ContentSection gehört nicht zum ItemType")
        if session.get(ContentSectionContentPiece,
                       (assignment.content_section_id, assignment.content_piece_id)) is None:
            raise HTTPException(status_code=400, detail="Plugin-ContentPiece gehört nicht zur ContentSection")
        piece = session.get(ContentPiece, assignment.content_piece_id)
        data_type = session.get(DataType, piece.data_type_id) if piece else None
        if data_type is None or data_type.name.upper() not in {
            name.upper() for name in plugin.supported_data_types
        }:
            raise HTTPException(status_code=400, detail=f"Datentyp wird von Plugin {plugin.name} nicht unterstützt")

    item_type = ItemType.model_validate(item_type_data)
    session.add(item_type)
    session.flush()  # Ensure the item_type gets an ID before committing
    session.add_all(
        [
            ContentSectionItemType(content_section_id=content_section, item_type_id=item_type.id)
            for content_section in item_type_data.content_section_ids
        ]
    )
    if item_type_data.plugins:
        metadata_section = session.exec(
            select(ContentSection).where(ContentSection.name == PluginSystem.METADATA_SECTION_NAME)
        ).first()
        if metadata_section is None:
            metadata_section = ContentSection(
                name=PluginSystem.METADATA_SECTION_NAME,
                description="Automatisch erzeugte Plugin-Ergebnisse",
            )
            session.add(metadata_section)
        data_type = session.exec(select(DataType).where(DataType.name == "JSON")).first()
        if data_type is None:
            data_type = DataType(name="JSON", description="Plugin-Ergebnis", source="plugin")
            session.add(data_type)
        session.flush()
        for assignment in item_type_data.plugins:
            output_piece = ContentPiece(
                name=assignment.plugin_name,
                description=PluginSystem.plugins[assignment.plugin_name].return_description,
                data_type_id=data_type.data_type_id,
            )
            session.add(output_piece)
            session.flush()
            session.add(ContentSectionContentPiece(
                content_section_id=metadata_section.id, content_piece_id=output_piece.id
            ))
            session.add(ItemTypePlugin(
                item_type_id=item_type.id,
                plugin_name=assignment.plugin_name,
                content_section_id=assignment.content_section_id,
                content_piece_id=assignment.content_piece_id,
                output_content_piece_id=output_piece.id,
            ))
    session.commit()
    session.refresh(item_type)
    return ItemTypeRead(
        id=item_type.id,
        name=item_type.name,
        description=item_type.description,
        content_section_ids=item_type_data.content_section_ids,
        plugins=item_type_data.plugins,
    )


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
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden")

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
