from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ===== SolutionAttempt =====
class SolutionAttemptBase(BaseModel):
    """
    Lösungsversuch einer Frage.

    - Schema-frei: solution_data ist ein JSON-Feld, das beliebige Strukturen speichern kann
    - Referenziert eine Item (über item_id)
    - Optional: student_id, attempt_number, status für Tracking
    """
    item_id: int
    solution_data: dict[str, Any]
    student_id: Optional[UUID] = None
    attempt_number: int = Field(default=1, ge=1)
    status: str = Field(default="submitted", max_length=50)


class SolutionAttempt(SolutionAttemptBase):
    """MongoDB-Dokument fuer Loesungsversuche.

    `_id` wird von MongoDB vergeben und hier als String abgebildet.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

