from datetime import UTC, datetime
from uuid import UUID, uuid4

from bson import ObjectId
from fastapi import HTTPException
from sqlmodel import Session

from database.dao_connection import get_engine
from models.items.tasks import Item
from schemas.Solutions.SolutionAttempt import SolutionAttemptCreate


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


def _ensure_item_exists(item_id: int, *, session_factory=Session, engine_factory=get_engine) -> None:
    """Prueft, ob das referenzierte Item in der SQL-Datenbank existiert."""
    try:
        with session_factory(engine_factory()) as session:
            item = session.get(Item, item_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Item-Pruefung fehlgeschlagen: {exc}"
        ) from exc

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Item mit ID {item_id} wurde nicht gefunden"
        )
