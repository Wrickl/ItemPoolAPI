import io
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from Util.searching import search_for_item
from database.dao_connection import get_session
from models import ContentPiece
from models.Enums.License import License
from models.Enums.Status import Status
from models.Enums.Themenbereich import Themenbereich
from models.Tasks.content_section_item import ContentSectionItem
from models.Tasks.content_types import (
    DataType,
    ItemType,
)
from models.Tasks.contentsection import ContentSection
from models.Tasks.tasks import Item
from models.creator import Creator
from schemas.Tasks.Item import (
    ItemCreate,
    ItemExportResponse,
    ItemTemplateResponse,
    ItemResponse,
    ItemWithAuthorResponse,
)
from services.PluginSystem import run_on_item_create

router = APIRouter()


def _validate_content_piece_ids(session: Session, content_piece_ids: list[int]) -> None:
    if not content_piece_ids:
        return

    existing_pieces = session.exec(
        select(ContentPiece).where(ContentPiece.content_piece_id.in_(content_piece_ids))
    ).all()
    existing_piece_ids = {piece.content_piece_id for piece in existing_pieces}
    missing_piece_ids = sorted(set(content_piece_ids) - existing_piece_ids)
    if missing_piece_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannte ContentPiece-IDs: {', '.join(str(piece_id) for piece_id in missing_piece_ids)}",
        )


def _extract_content_section_ids(item: Item) -> list[UUID]:
    return [section.id for section in item.content_sections if section.id is not None]


def _load_section_assignments(session: Session, item_id: UUID) -> list[ContentSectionItem]:
    return session.exec(
        select(ContentSectionItem).where(ContentSectionItem.item_id == item_id)
    ).all()


def _build_item_response_payload(session: Session, item: Item) -> dict[str, Any]:
    assignments = _load_section_assignments(session, item.item_id)
    content_sections = [
        {
            "content_section_id": assignment.content_section_id,
            "usage_area": assignment.usage_area,
            "content_blocks": assignment.content_blocks or [],
            "item_metadata": assignment.item_metadata or {},
        }
        for assignment in assignments
    ]
    return {
        "item_id": item.item_id,
        "license": item.license,
        "status": item.status,
        "author_id": item.author_id,
        "content_sections": content_sections,
        "item_type_id": item.item_type_id,
        "created_at": item.created_at,
    }


def _convert_item_to_export_format(item: Item, session: Session, author_name: str | None = None) -> dict:
    """
    Konvertiert ein Item in das Export-Format mit Namen statt IDs und angereicherten Content-Pieces.

    - Ersetzt license_id durch license_name
    - Ersetzt status_id durch status_name
    - Ersetzt item_type_id durch item_type_name
    - Ersetzt themenbereich_id durch themenbereich_name
    - Konvertiert content_piece_ids in vollständige ContentPiece-Objekte
    """
    # Laden der Namen für die IDs
    license_name = None
    if item.license:
        license_obj = session.get(License, item.license)
        if license_obj:
            license_name = license_obj.name

    status_name = None
    if item.status:
        status_obj = session.get(Status, item.status)
        if status_obj:
            status_name = status_obj.name

    item_type_name = None
    if item.item_type_id:
        item_type = session.get(ItemType, item.item_type_id)
        if item_type:
            item_type_name = item_type.name

    themenbereich_name = None
    if item.themenbereich:
        themenbereich = session.get(Themenbereich, item.themenbereich)
        if themenbereich:
            themenbereich_name = themenbereich.name

    # Hilfsfunktion zum Anreichern von Content-Pieces
    def enrich_content_blocks(blocks: list[dict], usage_area: str) -> list[dict]:
        enriched = []

        for block in blocks:
            content_piece_id = block.get("content_piece_id")
            value = block.get("value")

            if content_piece_id is None:
                continue

            content_piece = session.get(ContentPiece, content_piece_id)

            if content_piece is not None:
                data_type = session.get(DataType, content_piece.data_type_id)
                enriched.append(
                    {
                        "content_piece": {
                            "content_piece_id": content_piece.content_piece_id,
                            "is_required": False,
                            "content_piece_name": content_piece.name,
                            "content_piece_description": content_piece.description,
                            "data_type_id": content_piece.data_type_id,
                            "data_type_name": data_type.name if data_type else "",
                        },
                        "value": value,
                    }
                )
            else:
                # Fallback, falls ContentPiece nicht gefunden
                enriched.append(
                    {
                        "content_piece": {
                            "content_piece_id": content_piece_id,
                            "is_required": False,
                            "content_piece_name": f"Unknown ContentPiece #{content_piece_id}",
                            "content_piece_description": None,
                            "data_type_id": 0,
                            "data_type_name": "",
                        },
                        "value": value,
                    }
                )
        return enriched

    section_assignments = _load_section_assignments(session, item.item_id)
    assignment_by_section_id = {
        assignment.content_section_id: assignment for assignment in section_assignments
    }
    export_sections = []
    for section in item.content_sections:
        if section.id is None:
            continue
        assignment = assignment_by_section_id.get(section.id)
        usage_area = assignment.usage_area if assignment else "stimuli_content"
        content_blocks = assignment.content_blocks if assignment else []
        enriched_blocks = enrich_content_blocks(content_blocks, usage_area)
        export_sections.append(
            {
                "content_section_id": section.id,
                "name": section.name,
                "description": section.description,
                "usage_area": usage_area,
                "content_blocks": enriched_blocks,
                "item_metadata": assignment.item_metadata if assignment else {},
            }
        )

    # Baue Export-Response
    export_data = {
        "item_id": item.item_id,
        "license": license_name,
        "status": status_name,
        "item_type": item_type_name,
        "author_id": item.author_id,
        "author_name": author_name,
        "content_sections": export_sections,
        "themenbereich_id": item.themenbereich,
        "themenbereich": themenbereich_name,
        "created_at": item.created_at,
    }

    return export_data


@router.get("/getAllItems", response_model=list[ItemExportResponse], tags=["Items"])
async def get_all_questions(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Items mit Namen statt IDs und angereicherten Content-Pieces
    """
    items = session.exec(select(Item)).all()

    # Laden Sie Creator-Namen für alle Items
    creator_names = {}
    for item in items:
        if item.author_id not in creator_names:
            creator = session.get(Creator, item.author_id)
            creator_names[item.author_id] = creator.name if creator else None

    # Konvertiere Items in Export-Format
    return [
        _convert_item_to_export_format(item, session, creator_names.get(item.author_id))
        for item in items
    ]


@router.get("/searchItems", response_model=list[ItemWithAuthorResponse], tags=["Items"])
async def search_items(
        q: str | None = Query(None, description="Freitextsuche in Item-Inhalten"),
        author_id: str | None = Query(None, description="UUID des Autors (optional)"),
        author_name: str | None = Query(
            None, description="Name des Autors (optional, alternative zum author_id)"
        ),
        limit: int = Query(100, ge=1, le=1000),
        session: Session = Depends(get_session),
):
    """Suche Items mit optionalen Filtern. Liefert Items inklusive `author_name` (server-side join)."""
    # build a select that returns (Item, author_name)
    stmt = select(Item, Creator.name.label("author_name")).join(
        Creator,
        Item.author_id == Creator.author_id,  # type: ignore[arg-type]
    )
    if author_id:
        stmt = stmt.where(Item.author_id == UUID(author_id))  # type: ignore[arg-type]
    elif author_name:
        stmt = stmt.where(Creator.name.ilike(f"%{author_name}%"))  # type: ignore[attr-defined]

    stmt = stmt.limit(limit)
    rows = session.exec(stmt).all()

    results = []
    for row in rows:
        # row is typically a tuple (Item, author_name)
        try:
            item_obj, author_name = row
        except Exception:
            # fallback handling
            item_obj = row[0]
            author_name = None

        base = _build_item_response_payload(session, item_obj)
        base["author_name"] = author_name
        results.append(base)

    return results


@router.get("/exportItems", tags=["Items", "UI"])
async def export_items(
        q: str | None = Query(None, description="Freitextsuche in Item-Inhalten"),
        author_id: str | None = Query(None, description="UUID des Autors (optional)"),
        author_name: str | None = Query(
            None, description="Name des Autors (optional, alternative zum author_id)"
        ),
        session: Session = Depends(get_session),
):
    """Exportiere gefundene Items als JSON-Datei mit Namen statt IDs. Wenn keine Filter gesetzt sind, werden alle Items exportiert."""
    items = session.exec(search_for_item(author_id, author_name, q)).all()

    # Laden Sie Creator-Namen für alle Items
    creator_names = {}
    for item in items:
        if item.author_id not in creator_names:
            creator = session.get(Creator, item.author_id)
            creator_names[item.author_id] = creator.name if creator else None

    # Konvertiere Items in Export-Format
    payload = [
        _convert_item_to_export_format(item, session, creator_names.get(item.author_id))
        for item in items
    ]

    output = io.StringIO()
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.seek(0)
    return StreamingResponse(output, media_type="application/json",
                             headers={"Content-Disposition": "attachment; filename=items_export.json"})


@router.post("/createItem", response_model=ItemResponse, tags=["Items"])
async def create_item(item_data: ItemCreate, session: Session = Depends(get_session)):
    """
    Ein neues Item erstellen.

    - license: int (erforderlich) - ID der Lizenz
    - status_id: int (erforderlich) - Status-ID des Items
    - author_id: UUID (erforderlich) - UUID des Autors
    - content_sections: list[object] (erforderlich) - Zugeordnete ContentSections inkl. usage_area/payload
    - tags_id: int (optional) - ID der Tags
    - item_type_id: int (optional) - ID des ItemTypes
    """
    # Prüfe, ob der Author existiert
    author = session.exec(
        select(Creator).where(Creator.author_id == item_data.author_id)
    ).first()
    if not author:
        raise HTTPException(
            status_code=404,
            detail=f"Creator mit author_id '{item_data.author_id}' nicht gefunden",
        )

    # Validiere, dass alle referenzierten ContentPiece-IDs existieren (inkl. Solution-Bloecke).
    referenced_piece_ids = {
        block.content_piece_id
        for assignment in item_data.content_sections
        for block in assignment.content_blocks
    }
    existing_pieces = session.exec(
        select(ContentPiece).where(
            ContentPiece.content_piece_id.in_(referenced_piece_ids)
        )
    ).all()
    existing_piece_ids = {piece.content_piece_id for piece in existing_pieces}
    missing_piece_ids = sorted(referenced_piece_ids - existing_piece_ids)
    if missing_piece_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannte ContentPiece-IDs: {', '.join(str(piece_id) for piece_id in missing_piece_ids)}",
        )

    section_ids = [assignment.content_section_id for assignment in item_data.content_sections]
    existing_sections = session.exec(
        select(ContentSection).where(ContentSection.id.in_(section_ids))
    ).all()
    existing_section_ids = {section.id for section in existing_sections}
    missing_section_ids = sorted(
        set(section_ids) - {section_id for section_id in existing_section_ids if section_id is not None}
    )
    if missing_section_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannte ContentSection-IDs: {', '.join(str(section_id) for section_id in missing_section_ids)}",
        )

    # Erstelle neues Item mit aktuellem Timestamp
    new_item = Item(
        license=item_data.license,
        status=item_data.status_id,
        themenbereich=item_data.themenbereich_id,
        author_id=item_data.author_id,
        item_type_id=item_data.item_type_id,
        created_at=datetime.now(UTC),
    )

    session.add(new_item)
    session.commit()
    session.refresh(new_item)

    for assignment in item_data.content_sections:
        session.add(
            ContentSectionItem(
                content_section_id=assignment.content_section_id,
                item_id=new_item.item_id,
                usage_area=assignment.usage_area,
                content_blocks=[
                    block.model_dump(mode="json") for block in assignment.content_blocks
                ],
                item_metadata=assignment.item_metadata,
            )
        )

    session.commit()
    session.refresh(new_item)

    # Triggere registrierte Plugins, die auf Item-Erstellung reagieren
    # try:
    run_on_item_create(new_item, session)
    # except Exception:
    # Plugins sollen den Haupt-Flow nicht brechen; Fehler werden geschluckt
    #    pass

    response_payload = _build_item_response_payload(session, new_item)
    return response_payload


@router.get("/createItem/template/{item_type_id}", response_model=ItemTemplateResponse, tags=["Items"])
async def get_create_item_template(item_type_id: UUID, session: Session = Depends(get_session)):
    """Liefert eine Blanko-Vorlage für Items eines ItemTypes inklusive Sections und ContentPieces."""
    item_type = session.exec(
        select(ItemType)
        .where(ItemType.id == item_type_id)
        .options(
            selectinload(ItemType.content_sections)
            .selectinload(ContentSection.content_pieces)
            .selectinload(ContentPiece.data_type),
            selectinload(ItemType.content_sections)
            .selectinload(ContentSection.content_pieces)
            .selectinload(ContentPiece.complex_type),
        )
    ).first()

    if item_type is None:
        raise HTTPException(
            status_code=404,
            detail=f"ItemType {item_type_id} nicht gefunden",
        )

    content_sections: list[dict[str, Any]] = []
    for section in sorted(item_type.content_sections, key=lambda entry: entry.name.lower()):
        if section.id is None:
            continue

        content_pieces = []
        for piece in sorted(section.content_pieces, key=lambda entry: entry.name.lower()):
            if piece.id is None:
                continue
            content_pieces.append(
                {
                    "id": piece.id,
                    "name": piece.name,
                    "description": piece.description,
                    "data_type_id": piece.data_type_id,
                    "data_type_name": piece.data_type.name if piece.data_type else None,
                    "complex_type_id": piece.complex_type_id,
                    "complex_schema": piece.complex_type.json_schema if piece.complex_type else None,
                }
            )

        content_sections.append(
            {
                "id": section.id,
                "name": section.name,
                "description": section.description,
                "content_pieces": content_pieces,
            }
        )

    return {
        "item_type_id": item_type.id,
        "item_type_name": item_type.name,
        "item_type_description": item_type.description,
        "license_id": "Hier bitte Id der Licences eintragen",
        "status_id": "Hier bitte Id der Status eintragen",
        "themenbereich_id": "Hier bitte Id des Themenbereichs eintragen",
        "content_sections": content_sections,
    }

