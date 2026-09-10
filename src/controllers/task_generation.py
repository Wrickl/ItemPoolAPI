import io
import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ..database.dao_connection import get_session
from ..models.author import Creator
from ..models.Enums.License import License
from ..models.Enums.Status import Status
from ..models.Enums.Themenbereich import Themenbereich
from ..models.organisation import Organisation
from ..models.Tasks.content_types import (
    ContentPiece,
    DataType,
    ItemType,
    ItemTypeContentPiece,
)
from ..models.Tasks.tasks import Item
from ..schemas.Author.Author import CreatorCreate, CreatorRead
from ..schemas.Tasks.Item import (
    ItemCreate,
    ItemExportResponse,
    ItemResponse,
    ItemWithAuthorResponse,
)
from ..schemas.Tasks.License import LicenseCreate, LicenseResponse
from ..schemas.Tasks.Status import StatusCreate, StatusResponse
from ..schemas.Tasks.Themenbereich import ThemenbereichCreate, ThemenbereichResponse
from ..services.PluginSystem import run_on_item_create
from ..Util.searching import search_for_item

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


def _convert_item_to_export_format(
    item: Item, session: Session, author_name: str | None = None
) -> dict:
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
        item_type_id = item.item_type_id
        item_type_piece_map = {}

        if item_type_id is not None:
            assignments = session.exec(
                select(ItemTypeContentPiece).where(
                    ItemTypeContentPiece.item_type_id == item_type_id
                )
            ).all()
            item_type_piece_map = {
                (assignment.content_piece_id, assignment.usage_area): assignment
                for assignment in assignments
            }

        for block in blocks:
            content_piece_id = block.get("content_piece_id")
            value = block.get("value")

            if content_piece_id is None:
                continue

            content_piece = session.get(ContentPiece, content_piece_id)
            assignment = item_type_piece_map.get((content_piece_id, usage_area))

            if content_piece is not None:
                data_type = session.get(DataType, content_piece.data_type_id)
                enriched.append(
                    {
                        "content_piece": {
                            "content_piece_id": content_piece.content_piece_id,
                            "is_required": bool(assignment.is_required)
                            if assignment
                            else False,
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
                            "is_required": bool(assignment.is_required)
                            if assignment
                            else False,
                            "content_piece_name": f"Unknown ContentPiece #{content_piece_id}",
                            "content_piece_description": None,
                            "data_type_id": 0,
                            "data_type_name": "",
                        },
                        "value": value,
                    }
                )
        return enriched

    # Baue Export-Response
    export_data = {
        "item_id": item.item_id,
        "license": license_name,
        "status": status_name,
        "item_type": item_type_name,
        "author_id": item.author_id,
        "author_name": author_name,
        "solution": enrich_content_blocks(item.solution or [], "solution"),
        "interaction_content": enrich_content_blocks(
            item.interaction_content or [], "interaction_content"
        ),
        "stimuli_content": enrich_content_blocks(
            item.stimuli_content or [], "stimuli_content"
        ),
        "item_metadata": item.item_metadata,
        "themenbereich_id": item.themenbereich,
        "themenbereich": themenbereich_name,
        "tags_id": item.tags_id,
        "created_at": item.created_at,
    }

    return export_data


@router.get("/getAllCreator", response_model=list[CreatorRead])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors aus der Datenbank auslesen.
    """
    stmt = select(Creator, Organisation.name.label("organisation_name")).join(
        Organisation,
        Creator.organisation_id == Organisation.id,  # type: ignore[arg-type]
    )
    rows = session.exec(stmt).all()

    creators = []
    for creator, organisation_name in rows:
        creators.append(
            CreatorRead(
                author_id=creator.author_id,
                email=creator.email,
                name=creator.name,
                role=creator.role,
                organisation_name=organisation_name,
            )
        )
    return creators


@router.post("/createCreator", response_model=Creator)
async def create_creator(
    creator_data: CreatorCreate, session: Session = Depends(get_session)
):
    """
    Einen neuen Creator anlegen.
    """
    creator2add = Creator.model_validate(creator_data)

    session.add(creator2add)
    session.commit()
    session.refresh(creator2add)

    return creator2add


@router.post("/createOrganisation")
async def create_organisation(
    organisation: Organisation, session: Session = Depends(get_session)
):
    """
    Eine neue Organisation anlegen.
    """
    session.add(organisation)
    session.commit()
    session.refresh(organisation)
    return organisation


@router.get("/getAllOrganisations")
async def get_all_organisations(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Organisationen
    """
    organisations = session.exec(select(Organisation)).all()
    return organisations


@router.put("/updateOrganisation/{organisation_id}")
async def update_organisation(
    organisation_id: UUID,
    organisation: Organisation,
    session: Session = Depends(get_session),
):
    """
    Eine bestehende Organisation aktualisieren.
    """
    existing = session.exec(
        select(Organisation).where(Organisation.id == organisation_id)
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")

    existing.name = organisation.name
    existing.contact = organisation.contact
    existing.faculty = organisation.faculty

    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


@router.delete("/deleteOrganisation/{organisation_id}")
async def delete_organisation(
    organisation_id: UUID, session: Session = Depends(get_session)
):
    """
    Eine Organisation aus der Datenbank löschen.
    """
    organisation = session.exec(
        select(Organisation).where(Organisation.id == organisation_id)
    ).first()
    if not organisation:
        raise HTTPException(status_code=404, detail="Organisation nicht gefunden")

    session.delete(organisation)
    session.commit()
    return {"detail": "Organisation gelöscht"}


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

        base = ItemResponse.model_validate(item_obj).model_dump(mode="json")
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
    return StreamingResponse(output, media_type="application/json", headers={"Content-Disposition": "attachment; filename=items_export.json"})


@router.post("/createItem", response_model=ItemResponse, tags=["Items"])
async def create_item(item_data: ItemCreate, session: Session = Depends(get_session)):
    """
    Ein neues Item erstellen.

    - license: int (erforderlich) - ID der Lizenz
    - status_id: int (erforderlich) - Status-ID des Items
    - author_id: UUID (erforderlich) - UUID des Autors
    - solution: list[object] (optional) - Flexible Loesungsbloecke auf Basis von ContentPiece-IDs
    - interaction_content: list[object] (erforderlich) - Flexible Inhaltsbausteine fuer Interaktion
    - stimuli_content: list[object] (erforderlich) - Flexible Inhaltsbausteine fuer Stimuli/Material
    - tags_id: int (optional) - ID der Tags
    - item_type_id: int (optional) - ID des ItemTypes
    """
    logging.debug(f"Creating item with data: {item_data.model_dump()}")
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
        for block in [
            *item_data.interaction_content,
            *item_data.stimuli_content,
            *(item_data.solution or []),
        ]
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

    # Erstelle neues Item mit aktuellem Timestamp
    new_item = Item(
        license=item_data.license,
        status=item_data.status_id,
        themenbereich=item_data.themenbereich_id,
        author_id=item_data.author_id,
        solution=[block.model_dump(mode="json") for block in item_data.solution]
        if item_data.solution is not None
        else [],
        interaction_content=[
            block.model_dump(mode="json") for block in item_data.interaction_content
        ],
        stimuli_content=[
            block.model_dump(mode="json") for block in item_data.stimuli_content
        ],
        item_metadata=item_data.item_metadata,
        tags_id=item_data.tags_id,
        item_type_id=item_data.item_type_id,
        created_at=datetime.now(UTC),
    )

    session.add(new_item)
    session.commit()
    session.refresh(new_item)

    # Triggere registrierte Plugins, die auf Item-Erstellung reagieren
    # try:
    run_on_item_create(new_item, session)
    # except Exception:
    # Plugins sollen den Haupt-Flow nicht brechen; Fehler werden geschluckt
    #    pass

    return new_item


@router.get(
    "/getThemenbereich",
    response_model=list[ThemenbereichResponse],
    tags=["Themenbereich"],
)
async def get_themenbereich(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Themenbereiche.
    """
    return session.exec(select(Themenbereich)).all()


@router.post(
    "/createThemenbereich", response_model=ThemenbereichResponse, tags=["Themenbereich"]
)
async def create_themenbereich(
    themenbereich_data: ThemenbereichCreate, session: Session = Depends(get_session)
):
    """
    Einen neuen Themenbereich anlegen.
    """
    themenbereich2add = Themenbereich(
        name=themenbereich_data.name, description=themenbereich_data.description
    )
    session.add(themenbereich2add)
    session.commit()
    session.refresh(themenbereich2add)
    return themenbereich2add


@router.get("/getStatus", response_model=list[StatusResponse], tags=["Status"])
async def get_status(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Status.
    """
    return session.exec(select(Status)).all()


@router.post("/createStatus", response_model=StatusResponse, tags=["Status"])
async def create_status(
    status_data: StatusCreate, session: Session = Depends(get_session)
):
    """
    Einen neuen Status anlegen.
    """
    status2add = Status(name=status_data.name, description=status_data.description)
    session.add(status2add)
    session.commit()
    session.refresh(status2add)
    return status2add


@router.get("/getLicence", response_model=list[LicenseResponse], tags=["Licence"])
async def get_licence(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Lizenzen.
    """
    return session.exec(select(License)).all()


@router.post("/createLicense", response_model=LicenseResponse, tags=["Licence"])
async def create_license(
    license_data: LicenseCreate, session: Session = Depends(get_session)
):
    """
    Einen neuen Lizenz anlegen.
    """
    license2add = License(name=license_data.name, description=license_data.description)
    session.add(license2add)
    session.commit()
    session.refresh(license2add)
    return license2add
