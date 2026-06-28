from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ===== SolutionAttempt =====
class ScorePayload(BaseModel):
    """Bewertungsergebnis eines Loesungsversuchs."""

    value: int | float = Field(..., ge=0)
    maximum: int | float = Field(..., ge=0)
    correct: bool

    @model_validator(mode="after")
    def validate_score_range(self):
        if self.value > self.maximum:
            raise ValueError("score.value darf nicht groesser als score.maximum sein")
        return self


class TimestampsPayload(BaseModel):
    """Zeitinformationen eines Loesungsversuchs."""

    started: datetime
    submitted: datetime
    duration: int = Field(..., ge=0)


class ProcessPayload(BaseModel):
    """Prozessdaten eines Loesungsversuchs."""

    events: list[dict[str, Any]] = Field(default_factory=list)


class SolutionAttemptBase(BaseModel):
    """Schema-freies MongoDB-Dokument fuer Loesungsversuche."""

    attempt_id: UUID
    candidate_id: UUID
    assessment_id: UUID
    item_id: int
    item_version: int = Field(..., ge=0)
    response: dict[str, Any]
    score: ScorePayload
    timestamps: TimestampsPayload
    process: ProcessPayload
    evaluation: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolutionAttempt(SolutionAttemptBase):
    """MongoDB-Dokument fuer Loesungsversuche."""
    model_config = ConfigDict(populate_by_name=True)
    mongo_id: str | None = Field(default=None, alias="_id")
