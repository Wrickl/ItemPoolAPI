import json
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import aliased, joinedload, selectinload
from sqlmodel import Session, col, select

from util.searching import has_all_tags, search_for_item
from models import ContentPiece
from models.Enums.License import License
from models.Enums.Status import Status
from models.Enums.Themenbereich import Themenbereich
from models.items.content_section_item import ContentSectionItem
from models.items.content_types import DataType, ItemType
from models.items.content_section import ContentSection
from models.items.item_content_piece_value import ItemContentPieceValue
from models.items.item_tag import ItemTag
from models.items.tasks import Item
from models.complextype import ComplexType
from models.creator import Creator
from schemas.items.item import ItemContentSectionCreate, ItemCreate

FETCH_BATCH_SIZE = 200


def _build_item_content_sections(
        session: Session, item_ids: Sequence[UUID]
) -> dict[UUID, list[dict[str, Any]]]:
    sections_by_item: dict[UUID, list[dict[str, Any]]] = {
        item_id: [] for item_id in item_ids
    }
    for start in range(0, len(item_ids), FETCH_BATCH_SIZE):
        batch = item_ids[start: start + FETCH_BATCH_SIZE]
        pieces_by_section: dict[tuple[UUID, UUID], list[dict[str, Any]]] = {}
        values = session.exec(
            select(ItemContentPieceValue, ContentPiece, DataType, ComplexType)
            .join(ContentPiece, col(ItemContentPieceValue.content_piece_id) == col(ContentPiece.id))
            .outerjoin(DataType, col(ContentPiece.data_type_id) == col(DataType.data_type_id))
            .outerjoin(ComplexType, col(ContentPiece.complex_type_id) == col(ComplexType.id))
            .where(col(ItemContentPieceValue.item_id).in_(batch))
        )
        for value, piece, data_type, complex_type in values:
            pieces_by_section.setdefault((value.item_id, value.content_section_id), []).append(
                {
                    "id": piece.id,
                    "name": piece.name,
                    "description": piece.description,
                    "data_type_id": piece.data_type_id,
                    "data_type_name": data_type.name if data_type else None,
                    "complex_type_id": piece.complex_type_id,
                    "complex_schema": complex_type.json_schema if complex_type else None,
                    "value": value.value,
                }
            )
        assignments = session.exec(
            select(ContentSectionItem, ContentSection)
            .join(ContentSection, col(ContentSectionItem.content_section_id) == col(ContentSection.id))
            .where(col(ContentSectionItem.item_id).in_(batch))
        )
        for assignment, section in assignments:
            sections_by_item[assignment.item_id].append(
                {
                    "id": section.id,
                    "name": section.name,
                    "description": section.description,
                    "content_pieces": sorted(
                        pieces_by_section.get((assignment.item_id, section.id), []),
                        key=lambda piece: piece["name"].lower(),
                    ),
                }
            )
    for sections in sections_by_item.values():
        sections.sort(key=lambda section: section["name"].lower())
    return sections_by_item


def _version_fields(item: Item, current_id: UUID, current_number: int) -> dict[str, Any]:
    return {
        "version_group_id": item.version_group_id,
        "version_number": item.version_number,
        "previous_item_id": item.previous_item_id,
        "change_note": item.change_note,
        "is_current": item.item_id == current_id,
        "current_item_id": current_id,
        "current_version_number": current_number,
    }


def _item_version_info(session: Session, items: Sequence[Item]) -> dict[UUID, dict[str, Any]]:
    groups = list({item.version_group_id for item in items})
    current: dict[UUID, tuple[UUID, int]] = {}
    for start in range(0, len(groups), FETCH_BATCH_SIZE):
        ranked = (
            select(
                Item.item_id,
                Item.version_group_id,
                Item.version_number,
                func.row_number().over(
                    partition_by=Item.version_group_id,
                    order_by=col(Item.version_number).desc(),
                ).label("rank"),
            )
            .where(col(Item.version_group_id).in_(groups[start:start + FETCH_BATCH_SIZE]))
            .subquery()
        )
        for item_id, group_id, version_number in session.exec(
            select(ranked.c.item_id, ranked.c.version_group_id, ranked.c.version_number)
            .where(ranked.c.rank == 1)
        ):
            current[group_id] = (item_id, version_number)
    return {
        item.item_id: _version_fields(item, *current[item.version_group_id])
        for item in items
    }


def _build_item_response_payload(
    item: Item, content_sections: list[dict[str, Any]], version_info: dict[str, Any]
) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        **version_info,
        "license": item.license,
        "status": item.status,
        "status_id": item.status,
        "author_id": item.author_id,
        "themenbereich_id": item.themenbereich,
        "content_sections": content_sections,
        "item_type_id": item.item_type_id,
        "tags": sorted(link.name for link in item.tag_links),
        "created_at": item.created_at,
    }


def _build_export_payload(session: Session, items: Sequence[Item]) -> list[dict[str, Any]]:
    item_ids = [item.item_id for item in items]
    sections = _build_item_content_sections(session, item_ids)
    labels: dict[UUID, tuple[Any, ...]] = {}
    latest = aliased(Item)
    latest_id = (
        select(latest.item_id).where(latest.version_group_id == Item.version_group_id)
        .order_by(col(latest.version_number).desc()).limit(1).correlate(Item).scalar_subquery()
    )
    latest_number = (
        select(latest.version_number).where(latest.version_group_id == Item.version_group_id)
        .order_by(col(latest.version_number).desc()).limit(1).correlate(Item).scalar_subquery()
    )
    for start in range(0, len(item_ids), FETCH_BATCH_SIZE):
        batch = item_ids[start: start + FETCH_BATCH_SIZE]
        rows = session.exec(
            select(Item.item_id, Creator.name, License.name, Status.name, ItemType.name, Themenbereich.name,
                   latest_id, latest_number)
            .outerjoin(Creator, col(Item.author_id) == col(Creator.author_id))
            .outerjoin(License, col(Item.license) == col(License.id))
            .outerjoin(Status, col(Item.status) == col(Status.id))
            .outerjoin(ItemType, col(Item.item_type_id) == col(ItemType.id))
            .outerjoin(Themenbereich, col(Item.themenbereich) == col(Themenbereich.id))
            .where(col(Item.item_id).in_(batch))
        )
        for item_id, author, license_name, status, item_type, topic, current_id, current_number in rows:
            labels[item_id] = (author, license_name, status, item_type, topic, current_id, current_number)
    payload = []
    for item in items:
        author, license_name, status, item_type, topic, current_id, current_number = labels[item.item_id]
        payload.append(
            {
                "item_id": item.item_id,
                **_version_fields(item, current_id, current_number),
                "license": license_name,
                "status": status,
                "item_type": item_type,
                "author_id": item.author_id,
                "author_name": author,
                "content_sections": sections[item.item_id],
                "themenbereich_id": item.themenbereich,
                "themenbereich": topic,
                "tags": sorted(link.name for link in item.tag_links),
                "created_at": item.created_at,
            }
        )
    return payload


def _load_item_type(session: Session, item_type_id: UUID, *, include_piece_metadata: bool = False) -> ItemType:
    content_pieces = selectinload(ItemType.content_sections).selectinload(
        ContentSection.content_pieces
    )
    if include_piece_metadata:
        content_pieces = content_pieces.options(
            selectinload(ContentPiece.data_type),
            selectinload(ContentPiece.complex_type),
        )
    item_type = session.exec(
        select(ItemType).where(ItemType.id == item_type_id).options(content_pieces)
    ).first()

    if item_type is None:
        raise HTTPException(status_code=404, detail=f"ItemType {item_type_id} nicht gefunden", )
    return item_type


def _validate_template_content(sections: Sequence[ItemContentSectionCreate], item_type: ItemType) -> None:
    expected_sections = {
        section.id: {piece.id for piece in section.content_pieces}
        for section in item_type.content_sections
        if section.id is not None
    }
    submitted_section_ids = {section.id for section in sections}
    if len(submitted_section_ids) != len(sections):
        raise HTTPException(status_code=400, detail="Eine ContentSection wurde mehrfach übermittelt")
    if submitted_section_ids != expected_sections.keys():
        raise HTTPException(status_code=400,
                            detail="Die ContentSections stimmen nicht mit dem ItemType-Template überein")

    for section in sections:
        submitted_piece_ids = {piece.id for piece in section.content_pieces}
        if len(submitted_piece_ids) != len(section.content_pieces):
            raise HTTPException(status_code=400,
                                detail=f"Ein ContentPiece in Section {section.id} wurde mehrfach übermittelt")
        if submitted_piece_ids != expected_sections[section.id]:
            raise HTTPException(status_code=400,
                                detail=f"Die ContentPieces der Section {section.id} stimmen nicht mit dem ItemType-Template überein")


def _validate_item_create(session: Session, item_data: ItemCreate) -> None:
    if session.get(Creator, item_data.author_id) is None:
        raise HTTPException(status_code=404, detail=f"Creator mit author_id '{item_data.author_id}' nicht gefunden")

    item_type = _load_item_type(session, item_data.item_type_id)
    _validate_template_content(item_data.content_sections, item_type)

    for model, record_id, label in (
            (License, item_data.license, "License"),
            (Status, item_data.status_id, "Status"),
            (Themenbereich, item_data.themenbereich_id, "Themenbereich"),
    ):
        if session.get(model, record_id) is None:
            raise HTTPException(status_code=404, detail=f"{label} {record_id} nicht gefunden")


def _persist_item(
    session: Session, item_data: ItemCreate, *, previous: Item | None = None, change_note: str | None = None
) -> Item:
    item = Item(
        license=item_data.license,
        status=item_data.status_id,
        themenbereich=item_data.themenbereich_id,
        author_id=item_data.author_id,
        item_type_id=item_data.item_type_id,
        created_at=datetime.now(UTC),
        **({
            "version_group_id": previous.version_group_id,
            "version_number": previous.version_number + 1,
            "previous_item_id": previous.item_id,
            "change_note": change_note,
        } if previous is not None else {}),
    )

    session.add(item)
    session.flush()
    session.add_all(
        ItemTag(item_id=item.item_id, name=name) for name in set(item_data.tags)
    )
    for section in item_data.content_sections:
        session.add(
            ContentSectionItem(content_section_id=section.id, item_id=item.item_id)
        )
        session.add_all(
            ItemContentPieceValue(
                item_id=item.item_id,
                content_section_id=section.id,
                content_piece_id=piece.id,
                value=piece.value,
            )
            for piece in section.content_pieces
        )
    return item


def generate_item_export(
        bind: Engine | Connection,
        author_id: UUID | None,
        author_name: str | None,
        query: str | None,
        tags: list[str] | None,
) -> Iterator[str]:
    last_id: UUID | None = None
    separator = ""
    yield "["

    statement = search_for_item(author_id, author_name).options(
        joinedload(Item.tag_links)
    ).order_by(col(Item.item_id)).limit(FETCH_BATCH_SIZE)
    if tags:
        statement = statement.where(has_all_tags(tags))

    while True:
        with Session(bind) as export_session:
            page = statement if last_id is None else statement.where(col(Item.item_id) > last_id)
            items = export_session.exec(page).unique().all()
            if not items:
                break
            last_id = items[-1].item_id
            payload = _build_export_payload(export_session, items)
        for item in payload:
            yield separator + json.dumps(jsonable_encoder(item), ensure_ascii=False)
            separator = ","
    yield "]"
