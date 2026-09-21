from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    """Quellsystem eines SA/Event/Analyse-Dokuments."""

    system_id: str = Field(..., min_length=1)
    system_version: str | None = None


class Submission(BaseModel):
    """Finale Abgabe eines SolutionAttempts."""

    format: str = Field(..., min_length=1)
    data: Any


class EventLog(BaseModel):
    """Zusammenfassung ueber importierte Rohereignisse."""

    event_count: int = Field(..., ge=0)


class SolutionAttemptBase(BaseModel):
    """Kernmodell fuer `solution_attempts` ohne eingebettete Events/Analysen."""

    attempt_id: UUID
    item_id: int
    candidate: str = Field(..., min_length=1)
    source: Source
    submission: Submission
    submitted_at: datetime
    stored_at: datetime
    event_log: EventLog
    assessment_context: dict[str, Any] | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)


class SolutionAttempt(SolutionAttemptBase):
    """Persistiertes SA-Dokument."""

    model_config = ConfigDict(populate_by_name=True)
    mongo_id: str | None = Field(default=None, alias="_id")


class SolutionAttemptEvent(BaseModel):
    """Dokumentmodell fuer `solution_attempt_events`."""

    event_id: UUID
    attempt_id: UUID
    sequence: int = Field(..., ge=0)
    occurred_at: datetime | None = None
    recorded_at: datetime
    event_type: str = Field(..., min_length=1)
    source: Source
    raw_event: Any
    extensions: dict[str, Any] = Field(default_factory=dict)
