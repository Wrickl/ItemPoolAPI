from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SolutionAttemptCreate(BaseModel):
    """Schema fuer das Erstellen eines Loesungsversuchs in MongoDB."""

    item_id: int = Field(..., description="ID des zugehoerigen Items")
    solution_data: dict[str, Any] = Field(..., description="Schema-freie Loesungsdaten")
    student_id: Optional[UUID] = Field(default=None, description="Optionale Student-ID")
    attempt_number: int = Field(default=1, ge=1, description="Fortlaufende Versuchszahl")
    status: str = Field(default="submitted", max_length=50, description="Status des Versuchs")


class SolutionAttemptRead(BaseModel):
    """Response-Modell fuer einen Loesungsversuch."""

    id: Optional[str]
    item_id: int
    solution_data: dict[str, Any]
    student_id: Optional[UUID]
    attempt_number: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

