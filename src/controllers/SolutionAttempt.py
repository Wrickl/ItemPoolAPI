from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError
from sqlmodel import Session

from ..database.DAOConnection import get_engine
from ..database.MongoConnection import get_solution_attempt_collection
from ..models.Tasks.Tasks import Item
from ..schemas.Solutions.SolutionAttempt import SolutionAttemptCreate, SolutionAttemptRead
from ..services.PluginSystem import run_on_solution_attempt_create

router = APIRouter()


def _normalize_solution_attempt_document(document: dict) -> dict:
    """Macht MongoDB-Dokumente Pydantic-kompatibel.

    Insbesondere wird `_id` von ObjectId auf String konvertiert.
    """
    normalized = dict(document)
    if "_id" in normalized and isinstance(normalized["_id"], ObjectId):
        normalized["_id"] = str(normalized["_id"])
    return normalized


def _prepare_solution_attempt_document(solution_attempt_data: SolutionAttemptCreate) -> dict:
    """Bereitet das MongoDB-Dokument vor und berechnet fehlende Dauerwerte."""
    if solution_attempt_data.timestamps.submitted < solution_attempt_data.timestamps.started:
        raise HTTPException(
            status_code=422,
            detail="timestamps.submitted darf nicht vor timestamps.started liegen",
        )

    document = solution_attempt_data.model_dump(mode="json")
    duration = document["timestamps"].get("duration")

    if duration is None:
        started = solution_attempt_data.timestamps.started
        submitted = solution_attempt_data.timestamps.submitted
        document["timestamps"]["duration"] = int((submitted - started).total_seconds())

    return document


def _ensure_item_exists(item_id: int) -> None:
    """Prueft, ob das referenzierte Item in der SQL-Datenbank existiert."""
    try:
        with Session(get_engine()) as session:
            item = session.get(Item, item_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Item-Pruefung fehlgeschlagen: {exc}") from exc

    if item is None:
        raise HTTPException(status_code=404, detail=f"Item mit ID {item_id} wurde nicht gefunden")


@router.post("/createSolutionAttempt", response_model=SolutionAttemptRead, tags=["Solutions"])
def create_solution_attempt(solution_attempt_data: SolutionAttemptCreate):
    """Speichert einen Loesungsversuch in MongoDB."""
    _ensure_item_exists(solution_attempt_data.item_id)

    collection = get_solution_attempt_collection()
    document = _prepare_solution_attempt_document(solution_attempt_data)

    try:
        result = collection.insert_one(document)
        stored_document = collection.find_one({"_id": result.inserted_id})
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"SolutionAttempt konnte nicht gespeichert werden: {exc}") from exc

    if stored_document is None:
        raise HTTPException(status_code=500, detail="SolutionAttempt konnte nach dem Speichern nicht gelesen werden")

    # Triggere Plugins, die auf das Hinzufügen eines SolutionAttempt reagieren.
    # Dafür öffnen wir eine temporäre SQL-Session.
    try:
        with Session(get_engine()) as session:
            run_on_solution_attempt_create(stored_document, session)
    except Exception:
        # Plugin-Fehler dürfen den Speichervorgang nicht rückgängig machen.
        pass

    normalized_document = _normalize_solution_attempt_document(stored_document)
    return SolutionAttemptRead.model_validate(normalized_document)


@router.get("/getAllSolutionAttempts", response_model=list[SolutionAttemptRead], tags=["Solutions"])
def get_all_solution_attempts():
    """Liest alle Loesungsversuche aus MongoDB aus."""
    collection = get_solution_attempt_collection()
    documents = list(collection.find())
    return [SolutionAttemptRead.model_validate(_normalize_solution_attempt_document(doc)) for doc in documents]


@router.get("/getSolutionAttemptsForItem/{item_id}", response_model=list[SolutionAttemptRead], tags=["Solutions"])
def get_solution_attempts_for_item(item_id: int):
    """Liest alle Loesungsversuche fuer eine gegebene Item-ID aus MongoDB aus.

    Pfadparameter:
    - item_id: die ID des Items (int)
    """
    collection = get_solution_attempt_collection()

    try:
        documents = list(collection.find({"item_id": item_id}))
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"Fehler beim Lesen der SolutionAttempts: {exc}") from exc

    return [SolutionAttemptRead.model_validate(_normalize_solution_attempt_document(doc)) for doc in documents]
