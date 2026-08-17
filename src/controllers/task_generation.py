import io
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ..Util.searching import search_for_item
from ..Util.serializer import _serialize_text_payload
from ..database.dao_connection import get_session
from ..models.Enums.License import License
from ..models.Enums.Questiontypes import QuestionTypes
from ..models.Enums.Status import Status
from ..models.Enums.Themenbereich import Themenbereich
from ..models.Tasks.content_types import ContentPiece
from ..models.Tasks.tasks import Item
from ..models.author import Creator
from ..models.organisation import Organisation
from ..schemas.Author.Author import CreatorCreate, CreatorRead
from ..schemas.Tasks.Item import ItemCreate, ItemResponse, ItemWithAuthorResponse
from ..schemas.Tasks.License import LicenseResponse, LicenseCreate
from ..schemas.Tasks.Status import StatusResponse, StatusCreate
from ..schemas.Tasks.Themenbereich import ThemenbereichResponse, ThemenbereichCreate
from ..services.PluginSystem import run_on_item_create

router = APIRouter()


@router.get("/getAllAvailableQuestionsTypes", tags=["Enums"])
async def get_available_questions_types():
    return [k.value for k in QuestionTypes]


@router.get("/getAllCreator", response_model=list[CreatorRead])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors aus der Datenbank auslesen.
    """
    stmt = select(Creator, Organisation.name).join(Organisation,
                                                   Creator.organisation_id == Organisation.id)  # type: ignore[arg-type]
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
async def create_creator(creator_data: CreatorCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Creator in der Datenbank anlegen.
    """
    creator = Creator.model_validate(creator_data)

    session.add(creator)
    session.commit()
    session.refresh(creator)

    return creator


@router.post("/createOrganisation")
async def create_organisation(organisation: Organisation, session: Session = Depends(get_session)):
    """
    Eine neue Organisation in der Datenbank anlegen.
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


@router.get("/getAllItems")
async def get_all_questions(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Items
    """
    items = session.exec(select(Item)).all()
    return items


@router.get("/searchItems", response_model=list[ItemWithAuthorResponse], tags=["Items"])
async def search_items(
        q: Optional[str] = Query(None, description="Freitextsuche in Fragestellung"),
        author_id: Optional[str] = Query(None, description="UUID des Autors (optional)"),
        author_name: Optional[str] = Query(None, description="Name des Autors (optional, alternative zum author_id)"),
        database_id: Optional[int] = Query(None, description="ID der Datenbank"),
        limit: int = Query(100, ge=1, le=1000),
        session: Session = Depends(get_session),
):
    """Suche Items mit optionalen Filtern. Liefert Items inklusive `author_name` (server-side join)."""
    # build a select that returns (Item, author_name)
    stmt = select(Item, Creator.name).join(Creator, Item.author_id == Creator.author_id)
    if q:
        stmt = stmt.where(Item.fragestellung.ilike(f"%{q}%"))  # type: ignore[attr-defined]
    if author_id:
        stmt = stmt.where(Item.author_id == UUID(author_id))
    elif author_name:
        stmt = stmt.where(Creator.name.ilike(f"%{author_name}%"))  # type: ignore[attr-defined]
    if database_id:
        stmt = stmt.where(Item.database_id == database_id)

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
        q: Optional[str] = Query(None, description="Freitextsuche in Fragestellung"),
        author_id: Optional[str] = Query(None, description="UUID des Autors (optional)"),
        author_name: Optional[str] = Query(None, description="Name des Autors (optional, alternative zum author_id)"),
        database_id: Optional[int] = Query(None, description="ID der Datenbank"),
        session: Session = Depends(get_session),
):
    """Exportiere gefundene Items als JSON-Datei. Wenn keine Filter gesetzt sind, werden alle Items exportiert."""
    items = session.exec(search_for_item(author_id, author_name, database_id, q)).all()

    payload = [ItemResponse.model_validate(it).model_dump(mode="json") for it in items]
    output = io.StringIO()
    json.dump(payload, output, ensure_ascii=False, indent=2)
    output.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=items_export.json"
    }
    return StreamingResponse(output, media_type="application/json", headers=headers)


@router.post("/createItem", response_model=ItemResponse, tags=["Items"])
async def create_item(item_data: ItemCreate, session: Session = Depends(get_session)):
    """
    Ein neues Item in der Datenbank erstellen.

    - fragestellung: str (erforderlich) - Die Aufgabenstellung
    - question_type: QuestionTypes (erforderlich) - Typ der Frage
    - license: License (erforderlich) - Lizenz des Items
    - status_id: int (erforderlich) - Status-ID des Items
    - author_id: UUID (erforderlich) - UUID des Autors
    - solution: list[object] (optional) - Flexible Loesungsbloecke auf Basis von ContentPiece-IDs
    - interaction_content: list[object] (erforderlich) - Flexible Inhaltsbausteine fuer Interaktion
    - stimuli_content: list[object] (erforderlich) - Flexible Inhaltsbausteine fuer Stimuli/Material
    - item_metadata: dict (erforderlich) - Schema-freie Metadaten mit Pflichtfeld `bloomlevel`
    - tags_id: int (optional) - ID der Tags
    - database_id: int (optional) - ID der Datenbank
    """
    logging.debug(f"Creating item with data: {item_data.model_dump()}")
    # Prüfe, ob der Author existiert
    author = session.exec(select(Creator).where(Creator.author_id == item_data.author_id)).first()
    if not author:
        raise HTTPException(
            status_code=404,
            detail=f"Creator mit author_id '{item_data.author_id}' nicht gefunden"
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
        select(ContentPiece).where(ContentPiece.content_piece_id.in_(referenced_piece_ids))
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
        fragestellung=_serialize_text_payload(item_data.fragestellung) or "",
        question_type=item_data.question_type,
        license=item_data.license,
        status=item_data.status_id,
        fragenart=item_data.themenbereich_id,
        author_id=item_data.author_id,
        solution=[block.model_dump(mode="json") for block in
                  item_data.solution] if item_data.solution is not None else [],
        interaction_content=[block.model_dump(mode="json") for block in item_data.interaction_content],
        stimuli_content=[block.model_dump(mode="json") for block in item_data.stimuli_content],
        item_metadata=item_data.item_metadata,
        tags_id=item_data.tags_id,
        database_id=item_data.database_id,
        created_at=datetime.now(timezone.utc)
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


@router.get("/getThemenbereich", response_model=List[ThemenbereichResponse], tags=["Themenbereich"])
async def get_themenbereich(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Themenbereiche.
    """
    themenbereiche = session.exec(select(Themenbereich)).all()
    return themenbereiche


@router.post("/createThemenbereich", response_model=ThemenbereichResponse, tags=["Themenbereich"])
async def create_themenbereich(themenbereich_data: ThemenbereichCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Themenbereich in der Datenbank anlegen.
    """
    themenbereich = Themenbereich(
        name=themenbereich_data.name,
        description=themenbereich_data.description
    )
    session.add(themenbereich)
    session.commit()
    session.refresh(themenbereich)
    return themenbereich


@router.get("/getStatus", response_model=List[StatusResponse], tags=["Status"])
async def get_status(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Status.
    """
    status_list = session.exec(select(Status)).all()
    return status_list


@router.post("/createStatus", response_model=StatusResponse, tags=["Status"])
async def create_status(status_data: StatusCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Themenbereich in der Datenbank anlegen.
    """
    status = Status(
        name=status_data.name,
        description=status_data.description
    )
    session.add(status)
    session.commit()
    session.refresh(status)
    return status


@router.get("/getLicence", response_model=List[LicenseResponse], tags=["Licence"])
async def get_licence(session: Session = Depends(get_session)):
    """
    Rückgabe aller registrierten Lizenzen.
    """
    licence_list = session.exec(select(License)).all()
    return licence_list


@router.post("/createLicense", response_model=LicenseResponse, tags=["Licence"])
async def create_license(license_data: LicenseCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Lizenz in der Datenbank anlegen.
    """
    license = License(
        name=license_data.name,
        description=license_data.description
    )
    session.add(license)
    session.commit()
    session.refresh(license)
    return license
