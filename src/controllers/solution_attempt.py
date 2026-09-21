from datetime import UTC, datetime
from uuid import UUID, uuid4

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError
from sqlmodel import Session

from database.dao_connection import get_engine
from database.mongo_connection import (
    get_solution_attempt_collection,
    get_solution_attempt_events_collection,
)
from models.Tasks.tasks import Item
from schemas.Solutions.SolutionAttempt import (
    SolutionAttemptCreate,
    SolutionAttemptEventRead,
    SolutionAttemptRead,
)

router = APIRouter()


def run_on_solution_attempt_create(*_args, **_kwargs):
    """No-op: Plugin-Trigger fuer die aktuelle Entwicklungsphase deaktiviert."""


def _normalize_solution_attempt_document(document: dict) -> dict:
    """Macht MongoDB-Dokumente Pydantic-kompatibel.

    Insbesondere wird `_id` von ObjectId auf String konvertiert.
    """
    normalized = dict(document)
    if "_id" in normalized and isinstance(normalized["_id"], ObjectId):
        normalized["_id"] = str(normalized["_id"])
    return normalized


def _prepare_solution_attempt_document(
    solution_attempt_data: SolutionAttemptCreate,
) -> dict:
    """Bereitet das MongoDB-Dokument fuer das neue SA-Kernschema vor."""
    document = solution_attempt_data.model_dump(mode="json", exclude={"events"})
    if document.get("stored_at") is None:
        document["stored_at"] = datetime.now(UTC).isoformat()

    return document


def _prepare_solution_attempt_events(
    attempt_id: UUID,
    source_system_id: str,
    stored_at_iso: str,
    events: list[dict],
) -> list[dict]:
    prepared_events: list[dict] = []
    for index, event in enumerate(events):
        prepared_events.append(
            {
                "event_id": event.get("event_id") or str(uuid4()),
                "attempt_id": str(attempt_id),
                "sequence": event.get("sequence", index),
                "occurred_at": event.get("occurred_at"),
                "recorded_at": event.get("recorded_at", stored_at_iso),
                "event_type": event.get("event_type", "unknown:event"),
                "source": event.get("source", {"system_id": source_system_id}),
                "raw_event": event.get("raw_event", event),
                "extensions": event.get("extensions", {}),
            }
        )
    return prepared_events


def _find_solution_attempt_by_attempt_id(collection, attempt_id: str):
    documents = list(collection.find({"attempt_id": attempt_id}))
    if not documents:
        return None
    return documents[0]


def _ensure_item_exists(item_id: int) -> None:
    """Prueft, ob das referenzierte Item in der SQL-Datenbank existiert."""
    try:
        with Session(get_engine()) as session:
            item = session.get(Item, item_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Item-Pruefung fehlgeschlagen: {exc}"
        ) from exc

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Item mit ID {item_id} wurde nicht gefunden"
        )


@router.post(
    "/createSolutionAttempt", response_model=SolutionAttemptRead, tags=["Solutions"]
)
def create_solution_attempt(solution_attempt_data: SolutionAttemptCreate):
    """Speichert einen Loesungsversuch in MongoDB."""
    _ensure_item_exists(solution_attempt_data.item_id)

    collection = get_solution_attempt_collection()
    events_collection = get_solution_attempt_events_collection()
    document = _prepare_solution_attempt_document(solution_attempt_data)

    expected_event_count = solution_attempt_data.event_log.event_count
    actual_event_count = len(solution_attempt_data.events)
    if expected_event_count != actual_event_count:
        raise HTTPException(
            status_code=422,
            detail="event_log.event_count passt nicht zur Anzahl mitgelieferter Events",
        )

    try:
        result = collection.insert_one(document)
        stored_document = collection.find_one({"_id": result.inserted_id})

        event_documents = _prepare_solution_attempt_events(
            attempt_id=solution_attempt_data.attempt_id,
            source_system_id=solution_attempt_data.source.system_id,
            stored_at_iso=document["stored_at"],
            events=solution_attempt_data.events,
        )
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
    "/getSolutionAttempts", response_model=list[SolutionAttemptRead], tags=["Solutions"]
)
def get_solution_attempts(
    item_id: int | None = None, limit: int = 100, cursor: str | None = None
):
    """Liest SA-Uebersicht aus MongoDB; optional gefiltert nach item_id."""
    _ = cursor  # Cursor wird im naechsten Schritt fuer echte Pagination genutzt.
    collection = get_solution_attempt_collection()

    query: dict = {}
    if item_id is not None:
        query["item_id"] = item_id

    documents = list(collection.find(query))[: max(limit, 0)]
    return [
        SolutionAttemptRead.model_validate(_normalize_solution_attempt_document(doc))
        for doc in documents
    ]


@router.get(
    "/getSolutionAttempt/{attempt_id}",
    response_model=SolutionAttemptRead,
    tags=["Solutions"],
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
    tags=["Solutions"],
)
def get_solution_attempt_events(
    attempt_id: UUID, after_sequence: int | None = None, limit: int = 100
):
    """Liest Eventdaten eines SA aus der Event-Collection."""
    collection = get_solution_attempt_events_collection()
    try:
        events = list(collection.find({"attempt_id": str(attempt_id)}))
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500, detail=f"Fehler beim Lesen der SA-Events: {exc}"
        ) from exc

    if after_sequence is not None:
        events = [
            event for event in events if event.get("sequence", -1) > after_sequence
        ]
    events.sort(key=lambda event: event.get("sequence", -1))
    events = events[: max(limit, 0)]

    return [SolutionAttemptEventRead.model_validate(event) for event in events]
