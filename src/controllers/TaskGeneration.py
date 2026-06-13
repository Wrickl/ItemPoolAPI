import io
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ..database.DAOConnection import get_session
from ..models.Author import Creator
from ..models.Enums.License import License
from ..models.Enums.Questionstypes import Questiontypes
from ..models.Enums.Status import Status
from ..models.Organisation import Organisation
from ..models.Tasks.Tasks import Item
from ..schemas.Author.Author import CreatorCreate, CreatorRead
from ..schemas.Tasks.Item import ItemCreate, ItemResponse, ItemWithAuthorResponse
from ..services.PluginSystem import run_on_item_create

router = APIRouter()


@router.get("/getAllAvailableQuestionTypes", tags=["Data", "Enums"])
async def get_available_question_types():
    return [k.value for k in Questiontypes]


@router.get("/getAllAvailableLicenseTypes", tags=["Data", "Enums"])
async def get_available_license_types():
    return [k.value for k in License]


@router.get("/getAllAvailableStatusTypes", tags=["Data", "Enums"])
async def get_available_status_types():
    return [k.value for k in Status]


@router.get("/getAllCreator", response_model=list[CreatorRead])
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors aus der Datenbank auslesen.
    """
    creators = session.exec(select(Creator)).all()
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
    itmes = session.exec(select(Item)).all()
    return itmes


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
        stmt = stmt.where(Item.author_id == author_id)
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
    stmt = select(Item)
    if q:
        stmt = stmt.where(Item.fragestellung.ilike(f"%{q}%"))  # type: ignore[attr-defined]
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))  # type: ignore[attr-defined]
    if database_id:
        stmt = stmt.where(Item.database_id == database_id)

    items = session.exec(stmt).all()

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
    - question_type: Questiontypes (erforderlich) - Typ der Frage
    - license: License (erforderlich) - Lizenz des Items
    - status: Status (optional, default=Draft) - Status des Items
    - author_id: UUID (erforderlich) - UUID des Autors
    - solution: str (optional) - Musterlösung
    - item_metadata: dict (optional) - Schema-freie Metadaten
    - tags_id: int (optional) - ID der Tags
    - database_id: int (optional) - ID der Datenbank
    """
    # Prüfe, ob der Author existiert
    author = session.exec(select(Creator).where(Creator.author_id == item_data.author_id)).first()
    if not author:
        raise HTTPException(
            status_code=404,
            detail=f"Creator mit author_id '{item_data.author_id}' nicht gefunden"
        )

    # Erstelle neues Item mit aktuellem Timestamp
    new_item = Item(
        fragestellung=item_data.fragestellung,
        question_type=item_data.question_type,
        license=item_data.license,
        status=item_data.status,
        author_id=item_data.author_id,
        solution=item_data.solution,
        item_metadata=item_data.item_metadata,
        tags_id=item_data.tags_id,
        database_id=item_data.database_id,
        created_at=datetime.now(timezone.utc)
    )

    session.add(new_item)
    session.commit()
    session.refresh(new_item)

    # Triggere registrierte Plugins, die auf Item-Erstellung reagieren
    #try:
    run_on_item_create(new_item, session)
    #except Exception:
        # Plugins sollen den Haupt-Flow nicht brechen; Fehler werden geschluckt
    #    pass

    return new_item
