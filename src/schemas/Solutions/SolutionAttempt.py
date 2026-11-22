from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourcePayload(BaseModel):
    """Quellinformationen fuer SA, Event und Analyse."""

    system_id: str = Field(..., min_length=1)
    system_version: str | None = None


class SubmissionPayload(BaseModel):
    """Final abgegebene Loesung als formatierter JSON-Wert."""

    format: str = Field(..., min_length=1)
    data: Any


class EventLogPayload(BaseModel):
    """Zusammenfassung ueber die Anzahl referenzierter Events."""

    event_count: int = Field(..., ge=0)


class SolutionAttemptCreate(BaseModel):
    """Schema fuer den Import eines finalen SolutionAttempt."""

    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    item_id: int
    candidate: str = Field(..., min_length=1)
    source: SourcePayload
    submission: SubmissionPayload
    submitted_at: datetime
    stored_at: datetime | None = None
    event_log: EventLogPayload
    events: list[dict[str, Any]] = Field(default_factory=list)
    assessment_context: dict[str, Any] | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class SolutionAttemptRead(SolutionAttemptCreate):
    """Response-Modell fuer einen gespeicherten SolutionAttempt."""

    stored_at: datetime
    events: list[dict[str, Any]] = Field(default_factory=list, exclude=True)


class SolutionAttemptEventCreate(BaseModel):
    """Schema fuer ein einzelnes Rohereignis zu einem SolutionAttempt."""

    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    attempt_id: UUID
    sequence: int = Field(..., ge=0)
    occurred_at: datetime | None = None
    recorded_at: datetime
    event_type: str = Field(..., min_length=1)
    source: SourcePayload
    raw_event: Any
    extensions: dict[str, Any] = Field(default_factory=dict)


class SolutionAttemptEventRead(SolutionAttemptEventCreate):
    """Response-Modell fuer ein gespeichertes SA-Ereignis."""
