from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import joinedload
from sqlmodel import Session, col, select

from util.item import (
    _build_export_payload,
    _build_item_content_sections,
    _build_item_response_payload,
    _load_item_type,
    _item_version_info,
    _persist_item,
    _validate_item_create,
    generate_item_export,
)
from database.dao_connection import get_session
from models import ContentSectionItem, Item, ItemContentPieceValue, ItemTag
from schemas.items.item import (
    MAX_ITEM_TAGS,
    ItemCreate,
    ItemUpdate,
    ItemVersionInfo,
    ItemExportResponse,
    ItemResponse,
    ItemTagsResponse,
    ItemTagsUpdate,
    TagName,
)
from schemas import ItemTemplateResponse
from services.item_plugin_service import run_item_plugins

router = APIRouter()

TagFilter = Annotated[
    list[TagName] | None,
    Query(
        max_length=MAX_ITEM_TAGS,
        description="Das Item muss alle angegebenen Tags besitzen.",
    ),
]
SessionDependency = Annotated[Session, Depends(get_session)]
TextFilter = Annotated[str | None, Query(description="Freitextsuche in Item-Inhalten")]
AuthorIdFilter = Annotated[UUID | None, Query(description="UUID des Autors (optional)")]
AuthorNameFilter = Annotated[
    str | None,
    Query(description="Name des Autors (optional, alternative zum author_id)"),
]
SearchLimit = Annotated[int, Query(ge=1, le=1000)]
SearchOffset = Annotated[int, Query(ge=0)]


@router.get("/getAllItems", response_model=list[ItemExportResponse], tags=["Items"], name="get_all_questions")
def get_all_items(
    session: SessionDependency,
    limit: SearchLimit = 100,
    offset: SearchOffset = 0,
    item_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Liefert eine Seite von Items mit angereicherten ContentPieces."""
    statement = select(Item).order_by(col(Item.item_id)).offset(offset).limit(limit).options(joinedload(Item.tag_links))
    if item_id is not None:
        statement = statement.where(Item.item_id == item_id)
    return _build_export_payload(session, session.exec(statement).unique().all())


# @router.get("/searchItems", response_model=list[ItemWithAuthorResponse], tags=["Items"])
# def search_items(
#         session: SessionDependency,
# #        q: TextFilter = None,
#         author_id: AuthorIdFilter = None,
#         author_name: AuthorNameFilter = None,
#         limit: SearchLimit = 100,
#         offset: SearchOffset = 0,
#         tags: TagFilter = None,
# ) -> list[dict[str, Any]]:
#     """Liefert Items inklusive Autorenname und optionalen Filtern."""
#     statement = select(Item, col(Creator.name)).join(
#         Creator, col(Item.author_id) == col(Creator.author_id)
#     )
#     if author_id:
#         statement = statement.where(Item.author_id == author_id)
#     elif author_name:
#         statement = statement.where(col(Creator.name).ilike(f"%{author_name}%"))
#
#     if tags:
#         statement = statement.where(has_all_tags(tags))
#
#     statement = statement.order_by(col(Item.item_id)).offset(offset).limit(limit).options(joinedload(Item.tag_links))
#     rows = session.exec(statement).unique().all()
#     sections = _build_item_content_sections(session, [item.item_id for item, _ in rows])
#     return [
#         {**_build_item_response_payload(item, sections[item.item_id]), "author_name": name}
#         for item, name in rows
#     ]


@router.get("/exportItems", tags=["Items", "UI"])
def export_items(session: SessionDependency, q: TextFilter = None, author_id: AuthorIdFilter = None,
                 author_name: AuthorNameFilter = None, tags: TagFilter = None, ) -> StreamingResponse:
    """Exportiert alle passenden Items als JSON-Datei."""
    return StreamingResponse(
        generate_item_export(session.get_bind(), author_id, author_name, q, tags),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=items_export.json"},
    )


@router.post("/createItem", response_model=ItemResponse, tags=["Items"])
def create_item(item_data: ItemCreate, session: SessionDependency) -> dict[str, Any]:
    """Erstellt ein Item aus einem vollständig ausgefüllten ItemType-Template."""
    with session.begin():
        _validate_item_create(session, item_data)
        item = _persist_item(session, item_data)
        session.flush()
        run_item_plugins(item, session)

    session.refresh(item)
    sections = _build_item_content_sections(session, [item.item_id])
    return _build_item_response_payload(item, sections[item.item_id], _item_version_info(session, [item])[item.item_id])


def _lock_current_item(session: Session, item_id: UUID) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} nicht gefunden")
    session.exec(
        select(Item.item_id)
        .where(Item.version_group_id == item.version_group_id, Item.version_number == 1)
        .with_for_update()
    ).one()
    current = session.exec(
        select(Item).where(Item.version_group_id == item.version_group_id)
        .order_by(col(Item.version_number).desc()).limit(1)
    ).one()
    if current.item_id != item_id:
        raise HTTPException(
            status_code=409,
            detail=f"Item ist nicht aktuell; aktuelle Item-ID: {current.item_id}",
        )
    return current


@router.get("/getItemVersions/{item_id}", response_model=list[ItemVersionInfo], tags=["Items"])
def get_item_versions(item_id: UUID, session: SessionDependency) -> list[dict[str, Any]]:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} nicht gefunden")
    items = session.exec(
        select(Item).where(Item.version_group_id == item.version_group_id)
        .order_by(col(Item.version_number))
    ).all()
    versions = _item_version_info(session, items)
    return [{"item_id": entry.item_id, **versions[entry.item_id]} for entry in items]


@router.put("/updateItem/{item_id}", response_model=ItemResponse, tags=["Items"])
def update_item(item_id: UUID, item_data: ItemUpdate, session: SessionDependency) -> dict[str, Any]:
    """Erstellt eine neue Item-Version aus den übermittelten Daten."""
    with session.begin():
        previous = _lock_current_item(session, item_id)
        _validate_item_create(session, item_data)
        item = _persist_item(session, item_data, previous=previous, change_note=item_data.change_note)
        session.flush()
        run_item_plugins(item, session)
    session.refresh(item)
    sections = _build_item_content_sections(session, [item.item_id])
    return _build_item_response_payload(item, sections[item.item_id], _item_version_info(session, [item])[item.item_id])


@router.put("/updateItemTags/{item_id}", response_model=ItemTagsResponse, tags=["Items"])
def update_item_tags(item_id: UUID, item_data: ItemTagsUpdate, session: SessionDependency) -> ItemTagsResponse:
    """Erstellt eine neue Version mit den angegebenen Tags."""
    names = sorted(set(item_data.tags))
    with session.begin():
        previous = _lock_current_item(session, item_id)
        item = Item(
            license=previous.license, status=previous.status, themenbereich=previous.themenbereich,
            author_id=previous.author_id, item_type_id=previous.item_type_id,
            version_group_id=previous.version_group_id, version_number=previous.version_number + 1,
            previous_item_id=previous.item_id, change_note=item_data.change_note,
        )
        session.add(item)
        session.flush()
        sections = session.exec(select(ContentSectionItem).where(ContentSectionItem.item_id == item_id)).all()
        values = session.exec(select(ItemContentPieceValue).where(ItemContentPieceValue.item_id == item_id)).all()
        session.add_all(ItemTag(item_id=item.item_id, name=name) for name in names)
        session.add_all(ContentSectionItem(item_id=item.item_id, content_section_id=section.content_section_id)
                        for section in sections)
        session.add_all(
            ItemContentPieceValue(item_id=item.item_id, content_section_id=value.content_section_id,
                                  content_piece_id=value.content_piece_id, value=value.value)
            for value in values
        )
        session.flush()
        run_item_plugins(item, session)
    session.refresh(item)
    return ItemTagsResponse(item_id=item.item_id, tags=names, **_item_version_info(session, [item])[item.item_id])


@router.get("/createItem/template/{item_type_id}", response_model=ItemTemplateResponse, tags=["Items"])
def get_create_item_template(item_type_id: UUID, session: SessionDependency) -> dict[str, Any]:
    """Liefert eine Blanko-Vorlage mit Sections und ContentPieces."""
    item_type = _load_item_type(session, item_type_id, include_piece_metadata=True)
    content_sections: list[dict[str, Any]] = []
    for section in sorted(
            item_type.content_sections, key=lambda entry: entry.name.lower()
    ):
        if section.id is None:
            continue

        content_pieces = []
        for piece in sorted(
                section.content_pieces, key=lambda entry: entry.name.lower()
        ):
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
                    "complex_schema": piece.complex_type.json_schema
                    if piece.complex_type
                    else None,
                    "value": None,
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
        "license": None,
        "author_id": None,
        "status_id": None,
        "themenbereich_id": None,
        "content_sections": content_sections,
    }
