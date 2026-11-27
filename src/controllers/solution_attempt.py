from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sqlmodel import Session

from util.solution_attempt import (
    _ensure_item_exists,
    _find_solution_attempt_by_attempt_id,
    _normalize_solution_attempt_document,
    _prepare_solution_attempt_document,
    _prepare_solution_attempt_events,
)
from database.dao_connection import get_engine
from database.mongo_connection import (
    get_solution_attempt_collection,
    get_solution_attempt_events_collection,
)
from schemas import (
    SolutionAttemptCreate,
    SolutionAttemptEventRead,
    SolutionAttemptRead,
)

router = APIRouter()


@router.post(
    "/createSolutionAttempt", response_model=SolutionAttemptRead, tags=["solution_attempts"]
)
def create_solution_attempt(solution_attempt_data: SolutionAttemptCreate):
    """Speichert einen Loesungsversuch in MongoDB."""
    _ensure_item_exists(solution_attempt_data.item_id, session_factory=Session, engine_factory=get_engine)

    expected_event_count = solution_attempt_data.event_log.event_count
    actual_event_count = len(solution_attempt_data.events)
    if expected_event_count != actual_event_count:
        raise HTTPException(
            status_code=422,
            detail="event_log.event_count passt nicht zur Anzahl mitgelieferter Events",
        )

    document = _prepare_solution_attempt_document(solution_attempt_data)
    event_documents = _prepare_solution_attempt_events(
        attempt_id=solution_attempt_data.attempt_id,
        source_system_id=solution_attempt_data.source.system_id,
        stored_at_iso=document["stored_at"],
        events=solution_attempt_data.events,
    )
    try:
        event_documents = [
            SolutionAttemptEventRead.model_validate(event).model_dump(mode="json")
            for event in event_documents
        ]
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Ungültiges SolutionAttempt-Event: {exc}") from exc

    collection = get_solution_attempt_collection()
    events_collection = get_solution_attempt_events_collection()
    try:
        result = collection.insert_one(document)
        stored_document = collection.find_one({"_id": result.inserted_id})
        if event_documents:
            events_collection.insert_many(event_documents)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SolutionAttempt konnte nicht gespeichert werden: {exc}",
        ) from exc

    if stored_document is None:
        raise HTTPException(
            status_code=500,
            detail="SolutionAttempt konnte nach dem Speichern nicht gelesen werden",
        )

    normalized_document = _normalize_solution_attempt_document(stored_document)
    return SolutionAttemptRead.model_validate(normalized_document)


@router.get(
    "/getSolutionAttempts", response_model=list[SolutionAttemptRead], tags=["solution_attempts"]
)
def get_solution_attempts(
    item_id: UUID | None = None, limit: int = 100, cursor: str | None = None
):
    """Liest SA-Uebersicht aus MongoDB; optional gefiltert nach item_id."""
    if cursor is not None:
        raise HTTPException(status_code=400, detail="Cursor-Pagination wird noch nicht unterstützt")
    if limit <= 0:
        return []
    collection = get_solution_attempt_collection()

    query: dict = {}
    if item_id is not None:
        query["item_id"] = str(item_id)

    try:
        documents = collection.find(query, limit=limit)
        return [
            SolutionAttemptRead.model_validate(_normalize_solution_attempt_document(doc))
            for doc in documents
        ]
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"Fehler beim Lesen der SolutionAttempts: {exc}") from exc


@router.get(
    "/getSolutionAttempt/{attempt_id}",
    response_model=SolutionAttemptRead,
    tags=["solution_attempts"],
)
def get_solution_attempt(attempt_id: UUID):
    """Liest einen einzelnen SA ueber seine fachliche attempt_id."""
    collection = get_solution_attempt_collection()
    try:
        document = _find_solution_attempt_by_attempt_id(collection, str(attempt_id))
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500, detail=f"Fehler beim Lesen der SolutionAttempts: {exc}"
        ) from exc

    if document is None:
        raise HTTPException(status_code=404, detail="SolutionAttempt nicht gefunden")

    if not isinstance(document, dict):
        raise HTTPException(
            status_code=500,
            detail="Ungueltiges Datenformat beim Lesen des SolutionAttempt",
        )

    normalized_document = _normalize_solution_attempt_document(document)
    return SolutionAttemptRead.model_validate(normalized_document)


@router.get(
    "/getSolutionAttempt/{attempt_id}/events",
    response_model=list[SolutionAttemptEventRead],
    tags=["solution_attempts"],
)
def get_solution_attempt_events(
    attempt_id: UUID, after_sequence: int | None = None, limit: int = 100
):
    """Liest Eventdaten eines SA aus der Event-Collection."""
    if limit <= 0:
        return []
    collection = get_solution_attempt_events_collection()
    query = {"attempt_id": str(attempt_id)}
    if after_sequence is not None:
        query["sequence"] = {"$gt": after_sequence}
    try:
        events = collection.find(query).sort("sequence", 1).limit(limit)
        return [SolutionAttemptEventRead.model_validate(event) for event in events]
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500, detail=f"Fehler beim Lesen der SA-Events: {exc}"
        ) from exc
