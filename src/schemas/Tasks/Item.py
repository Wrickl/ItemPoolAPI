import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class ProgrammingSolutionPayload(BaseModel):
    text: str = Field(..., min_length=1, description="Eigentlicher Loesungstext")
    output: Optional[str] = Field(default=None, description="Optionaler erwarteter Output")


class ItemCreate(BaseModel):
    """
    Schema fuer die Erstellung eines neuen Items ueber die API.

    - Erforderliche Felder: fragestellung, question_type, license, status, author_id
    - Optionale Felder: solution, tags_id, database_id
    - Pflicht-Metadatum: item_metadata.bloomlevel
    """

    fragestellung: str = Field(..., description="Die Aufgabenstellung")
    question_type: QuestionTypes = Field(..., description="Typ der Frage (z.B. Freitext, MultipleChoice)")
    license: License = Field(..., description="Lizenz des Items")
    status: Status = Field(default=Status.Draft, description="Status des Items")
    author_id: UUID = Field(..., description="UUID des Autors/Creators")
    solution: str | MultipleChoiceSolutionPayload | ProgrammingSolutionPayload = Field(
        default=None,
        description="Loesung. Bei MultipleChoice mit Optionen + korrekten IDs; bei Programmierung optional mit `text` + `output`",
    )
    item_metadata: dict = Field(..., description="Schema-freie Metadaten (JSON), muss `bloomlevel` enthalten")
    tags_id: Optional[int] = Field(default=None, description="ID der Tags (optional)")
    database_id: Optional[int] = Field(default=None, description="ID der zugehoerigen Datenbank (optional)")

    @model_validator(mode="after")
    def validate_by_question_type(self):
        if self.question_type in (QuestionTypes.MultipleChoice, QuestionTypes.SingleChoice):
            if not self.fragestellung.strip():
                raise ValueError("Bei Choice-Fragen muss `fragestellung` ein nicht-leerer String sein")

            if not isinstance(self.solution, MultipleChoiceSolutionPayload):
                raise ValueError(
                    "Bei Choice-Fragen muss `solution` ein Objekt mit `options` und `correct_option_ids` sein"
                )

            if self.question_type == QuestionTypes.SingleChoice and len(self.solution.correct_option_ids) != 1:
                raise ValueError("Bei `question_type=SingleChoice` muss genau eine korrekte Option gesetzt sein")

            bloomlevel = self.item_metadata.get("bloomlevel")
            if bloomlevel is None or (isinstance(bloomlevel, str) and not bloomlevel.strip()):
                raise ValueError("`item_metadata.bloomlevel` muss gesetzt sein")
            return self

        if self.question_type == QuestionTypes.Programmierung:
            if not isinstance(self.fragestellung, str) or not self.fragestellung.strip():
                raise ValueError("Bei `question_type=Programmierung` muss `fragestellung` ein nicht-leerer String sein")
            if self.solution is not None:
                if isinstance(self.solution, str):
                    if not self.solution.strip():
                        raise ValueError("Bei `question_type=Programmierung` muss `solution` ein nicht-leerer String sein")
                elif not isinstance(self.solution, ProgrammingSolutionPayload):
                    raise ValueError(
                        "Bei `question_type=Programmierung` muss `solution` ein String oder Objekt mit `text` und optional `output` sein"
                    )
            bloomlevel = self.item_metadata.get("bloomlevel")
            if bloomlevel is None or (isinstance(bloomlevel, str) and not bloomlevel.strip()):
                raise ValueError("`item_metadata.bloomlevel` muss gesetzt sein")
            return self

        if not isinstance(self.fragestellung, str) or not self.fragestellung.strip():
            raise ValueError("Bei nicht-MultipleChoice muss `fragestellung` ein nicht-leerer String sein")
        if self.solution is not None and (not isinstance(self.solution, str) or not self.solution.strip()):
            raise ValueError("Bei nicht-MultipleChoice muss `solution` ein String sein (oder weggelassen werden)")

        bloomlevel = self.item_metadata.get("bloomlevel")
        if bloomlevel is None or (isinstance(bloomlevel, str) and not bloomlevel.strip()):
            raise ValueError("`item_metadata.bloomlevel` muss gesetzt sein")
        return self


class ItemResponse(BaseModel):
    """Response-Modell fuer ein erstelltes oder abgerufenes Item."""

    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: License
    status: Status
    author_id: UUID
    solution: Optional[dict | str]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    @field_validator("solution", mode="before")
    @classmethod
    def parse_solution_json_if_possible(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return value
            if isinstance(parsed, dict):
                return parsed
        return value

    class Config:
        from_attributes = True


class ItemWithAuthorResponse(BaseModel):
    """Response-Modell fuer Items inklusive Author-Name (server-side join)."""

    item_id: Optional[int]
    fragestellung: str
    question_type: QuestionTypes
    license: License
    status: Status
    author_id: UUID
    author_name: Optional[str]
    solution: Optional[dict | str]
    item_metadata: Optional[dict]
    tags_id: Optional[int]
    database_id: Optional[int]
    created_at: datetime

    @field_validator("solution", mode="before")
    @classmethod
    def parse_solution_json_if_possible(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return value
            if isinstance(parsed, dict):
                return parsed
        return value

    model_config = ConfigDict(from_attributes=True)