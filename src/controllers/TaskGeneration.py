from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import Optional
import io
import csv

from ..database.DAOConnection import get_session
from ..models.Author import Creator
from ..models.Enums.License import License
from ..models.Enums.Questionstypes import Questiontypes
from ..models.Organisation import Organisation
from ..models.Tasks.Tasks import Item, Database
from ..schemas.Author.Author import CreatorCreate
from ..schemas.Tasks.Database import DatabaseCreate, DatabaseResponse
from ..schemas.Tasks.Item import ItemCreate, ItemResponse

router = APIRouter()


@router.get("/getAllAvailableQuestionTypes", tags=["Data", "Enums"])
async def get_available_question_types():
    return [k.value for k in Questiontypes]


@router.get("/getAllAvailableLicenseTypes")
async def get_available_license_types():
    return [k.value for k in License]


@router.get("/getAllCreator")
async def get_all_creators(session: Session = Depends(get_session)):
    """
    Alle Creator/Authors aus der Datenbank auslesen.
    """
    creators = session.exec(select(Creator)).all()
    return creators


@router.post("/createCreator", response_model=Creator)
async def create_creator(creator_data: CreatorCreate, session: Session = Depends(get_session)):
    """
    Einen neuen Creator/_Test in der Datenbank anlegen.
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


@router.post("/getAllOrganisations")
async def get_all_organisations(session: Session = Depends(get_session)):
    organisations = session.exec(select(Organisation)).all()
    return organisations


@router.get("/getAllItems")
async def get_all_questions(session: Session = Depends(get_session)):
    """
    Alle Questions aus der Datenbank mit allen Feldern auslesen.
    """
    itmes = session.exec(select(Item)).all()
    return itmes


@router.get("/searchItems", tags=["Items"])
async def search_items(
    q: Optional[str] = Query(None, description="Freitextsuche in Fragestellung"),
    author_id: Optional[str] = Query(None, description="UUID des Autors (optional)"),
    author_name: Optional[str] = Query(None, description="Name des Autors (optional, alternative zum author_id)"),
    database_id: Optional[int] = Query(None, description="ID der Datenbank"),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    """Suche Items mit optionalen Filtern. Gibt eine Liste von Items zurück."""
    stmt = select(Item)
    if q:
        # suche in fragestellung (case-insensitive)
        stmt = stmt.where(Item.fragestellung.ilike(f"%{q}%"))
    # author filter: prefer exact id, fallback to name search
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        # join to Creator and search by name
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))
    if database_id:
        stmt = stmt.where(Item.database_id == database_id)

    stmt = stmt.limit(limit)
    results = session.exec(stmt).all()
    return results


@router.get("/exportItems", tags=["Items"])
async def export_items(
    q: Optional[str] = Query(None, description="Freitextsuche in Fragestellung"),
    author_id: Optional[str] = Query(None, description="UUID des Autors (optional)"),
    author_name: Optional[str] = Query(None, description="Name des Autors (optional, alternative zum author_id)"),
    database_id: Optional[int] = Query(None, description="ID der Datenbank"),
    session: Session = Depends(get_session),
):
    """Exportiere gefundene Items als CSV. Wenn keine Filter gesetzt sind, werden alle Items exportiert."""
    stmt = select(Item)
    if q:
        stmt = stmt.where(Item.fragestellung.ilike(f"%{q}%"))
    if author_id:
        stmt = stmt.where(Item.author_id == author_id)
    elif author_name:
        stmt = stmt.join(Creator).where(Creator.name.ilike(f"%{author_name}%"))
    if database_id:
        stmt = stmt.where(Item.database_id == database_id)

    items = session.exec(stmt).all()

    # Erzeuge CSV im Speicher
    output = io.StringIO()
    writer = csv.writer(output)
    # Header
    writer.writerow(["item_id", "fragestellung", "question_type", "license", "status", "created_at", "author_id", "database_id"])
    for it in items:
        writer.writerow([
            it.item_id,
            it.fragestellung,
            getattr(it.question_type, 'value', it.question_type),
            getattr(it.license, 'value', it.license),
            it.status,
            it.created_at.isoformat() if it.created_at else "",
            it.author_id,
            it.database_id,
        ])

    output.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=items_export.csv"
    }
    return StreamingResponse(output, media_type="text/csv", headers=headers)


@router.get("/getAllDatabases", response_model=list[DatabaseResponse], tags=["Database"])
async def get_all_databases(session: Session = Depends(get_session)):
    """Alle gespeicherten Datenbank-Definitionen auslesen."""
    databases = session.exec(select(Database)).all()
    return databases


@router.post("/createDatabase", response_model=DatabaseResponse, tags=["Database"])
async def create_database(database_data: DatabaseCreate, session: Session = Depends(get_session)):
    """Eine neue Datenbank-Definition in der Datenbank anlegen."""
    database = Database.model_validate(database_data)

    session.add(database)
    session.commit()
    session.refresh(database)

    return database


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

    return new_item
