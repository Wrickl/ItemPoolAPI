from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import ConfigDict
from pydantic import model_validator

from ...models.Enums.License import License
from ...models.Enums.Questiontypes import QuestionTypes
from ...models.Enums.Status import Status


class MultipleChoiceOption(BaseModel):
    option_id: str = Field(..., min_length=1, description="Eindeutige ID der Antwortoption")
    text: str = Field(..., min_length=1, description="Anzeigetext der Antwortoption")


class MultipleChoiceQuestionPayload(BaseModel):
    prompt: str = Field(..., min_length=1, description="Fragetext der Multiple-Choice-Frage")
    options: list[MultipleChoiceOption] = Field(
        ..., min_length=2, description="Alle moeglichen Antwortoptionen"
    )


class MultipleChoiceSolutionPayload(BaseModel):
    options: list[MultipleChoiceOption] = Field(
        ..., min_length=2, description="Alle Antwortoptionen inkl. IDs"
    )
    correct_option_ids: list[str] = Field(
        ..., min_length=1, description="Eine oder mehrere korrekte Option-IDs"
    )

    @model_validator(mode="after")
    def validate_correct_option_ids(self):
        option_ids = {option.option_id for option in self.options}
        if len(option_ids) != len(self.options):
            raise ValueError("`solution.options` enthaelt doppelte `option_id`-Werte")

        invalid_ids = [option_id for option_id in self.correct_option_ids if option_id not in option_ids]
        if invalid_ids:
            raise ValueError(
                f"`solution.correct_option_ids` enthaelt unbekannte IDs: {', '.join(invalid_ids)}"
            )
        return self


class ItemCreate(BaseModel):
    """
    Schema für die Erstellung eines neuen Items über die API.

    - Erforderliche Felder: fragestellung, question_type, license, status, author_id
    - Optionale Felder: solution, item_metadata, tags_id, database_id
    """
    fragestellung: str | MultipleChoiceQuestionPayload = Field(..., description="Die Aufgabenstellung")
    question_type: QuestionTypes = Field(..., description="Typ der Frage (z.B. Freitext, MultipleChoice)")
    license: License = Field(..., description="Lizenz des Items")
    status: Status = Field(default=Status.Draft, description="Status des Items")
    author_id: UUID = Field(..., description="UUID des Autors/Creators")
    solution: str | MultipleChoiceSolutionPayload = Field(
        default=None,
        description="Loesung. Bei MultipleChoice mit Optionen + korrekten IDs",
    )
    item_metadata: Optional[dict] = Field(default=None, description="Schema-freie Metadaten (JSON)")
    tags_id: Optional[int] = Field(default=None, description="ID der Tags (optional)")
    database_id: Optional[int] = Field(default=None, description="ID der zugehörigen Datenbank (optional)")

    @model_validator(mode="after")
    def validate_by_question_type(self):
        if self.question_type == QuestionTypes.MultipleChoice:
            if not isinstance(self.fragestellung, MultipleChoiceQuestionPayload):
                raise ValueError(
                    "Bei `question_type=MultipleChoice` muss `fragestellung` ein Objekt mit `prompt` und `options` sein"
                )
            if not isinstance(self.solution, MultipleChoiceSolutionPayload):
                raise ValueError(
                    "Bei `question_type=MultipleChoice` muss `solution` ein Objekt mit `options` und `correct_option_ids` sein"
                )

            question_option_ids = {option.option_id for option in self.fragestellung.options}
            solution_option_ids = {option.option_id for option in self.solution.options}
            if question_option_ids != solution_option_ids:
                raise ValueError(
                    "Bei `MultipleChoice` muessen `fragestellung.options` und `solution.options` dieselben `option_id` enthalten"
                )
            return self

        if not isinstance(self.fragestellung, str) or not self.fragestellung.strip():
            raise ValueError("Bei nicht-MultipleChoice muss `fragestellung` ein nicht-leerer String sein")
        if self.solution is not None and (not isinstance(self.solution, str) or not self.solution.strip()):
            raise ValueError("Bei nicht-MultipleChoice muss `solution` ein String sein (oder weggelassen werden)")
        return self


class ItemResponse(BaseModel):
    """Response-Modell für ein erstelltes oder abgerufenes Item."""
    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: License
    status: Status
    author_id: UUID
    solution: Optional[str]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ItemWithAuthorResponse(BaseModel):
    """Response-Modell für Items inklusive Author-Name (server-side join).

    Wird von `searchItems` verwendet, damit die UI den Autorennamen direkt
    vom Server bekommt und nicht erst weitere Requests benötigt.
    """
    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: License
    status: Status
    author_id: UUID
    author_name: Optional[str]
    solution: Optional[str]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

