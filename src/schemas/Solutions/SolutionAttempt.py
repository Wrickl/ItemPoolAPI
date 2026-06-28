from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScorePayload(BaseModel):
    """Bewertungsergebnis eines Loesungsversuchs."""

    value: int | float = Field(..., ge=0, description="Erreichte Punktzahl")
    maximum: int | float = Field(..., ge=0, description="Maximal erreichbare Punktzahl")
    correct: bool = Field(..., description="Ob der Versuch als korrekt bewertet wurde")

    @model_validator(mode="after")
    def validate_score_range(self):
        if self.value > self.maximum:
            raise ValueError("score.value darf nicht groesser als score.maximum sein")
        return self


class TimestampsReadPayload(BaseModel):
    """Zeitinformationen eines gespeicherten Loesungsversuchs."""

    started: datetime = Field(..., description="Startzeitpunkt des Versuchs")
    submitted: datetime = Field(..., description="Abgabezeitpunkt des Versuchs")
    duration: int = Field(..., ge=0, description="Dauer des Versuchs in Sekunden")


class TimestampsCreatePayload(BaseModel):
    """Zeitinformationen fuer das Erstellen eines Loesungsversuchs."""

    started: datetime = Field(..., description="Startzeitpunkt des Versuchs")
    submitted: datetime = Field(..., description="Abgabezeitpunkt des Versuchs")
    duration: int | None = Field(default=None, ge=0, description="Optionale Dauer des Versuchs in Sekunden")


class ProcessPayload(BaseModel):
    """Prozessdaten eines Loesungsversuchs."""

    events: list[dict[str, Any]] = Field(default_factory=list, description="Liste frei strukturierter Ereignisse")


class SolutionAttemptPayload(BaseModel):
    """Gemeinsames Payload-Schema fuer Loesungsversuche in MongoDB."""

    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID = Field(..., description="Fachliche ID des Loesungsversuchs")
    candidate_id: UUID = Field(..., description="ID des Kandidaten")
    assessment_id: UUID = Field(..., description="ID des Assessments")
    item_id: int = Field(..., description="ID des zugehoerigen Items")
    item_version: int = Field(..., ge=0, description="Version des referenzierten Items")
    response: dict[str, Any] = Field(..., description="Schema-freie Antwortdaten")
    score: ScorePayload
    timestamps: TimestampsReadPayload
    process: ProcessPayload
    evaluation: dict[str, Any] = Field(default_factory=dict, description="Schema-freie Evaluationsdaten")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Schema-freie Metadaten")


class SolutionAttemptCreate(BaseModel):
    """Schema fuer das Erstellen eines Loesungsversuchs in MongoDB."""

    model_config = ConfigDict(from_attributes=True)
    attempt_id: UUID = Field(..., description="Fachliche ID des Loesungsversuchs")
    candidate_id: UUID = Field(..., description="ID des Kandidaten")
    assessment_id: UUID = Field(..., description="ID des Assessments")
    item_id: int = Field(..., description="ID des zugehoerigen Items")
    item_version: int = Field(..., ge=0, description="Version des referenzierten Items")
    response: dict[str, Any] = Field(..., description="Schema-freie Antwortdaten")
    score: ScorePayload
    timestamps: TimestampsCreatePayload
    process: ProcessPayload
    evaluation: dict[str, Any] = Field(default_factory=dict, description="Schema-freie Evaluationsdaten")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Schema-freie Metadaten")


class SolutionAttemptRead(SolutionAttemptPayload):
    """Response-Modell fuer einen Loesungsversuch."""