from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

from .Database import Database
from ..Author import Creator
from ..Enums.License import License
from ..Enums.Themenbereich import Themenbereich
from ..Enums.Status import Status
from ..Enums.Questiontypes import QuestionTypes
"""TODO Beachten von verschiedene Fragentypen ( Freitext, Programmierung (SQL), oder Multiple Choice) mit entsprechenden Anpassungen der Datenbank-Modelle, z.B. durch Vererbung oder separate Tabellen für spezifische Fragentypen."""

# ===== Questions =====
class QuestionsBase(SQLModel):
    question_template: str
    description: Optional[str] = Field(default=None, max_length=255)


class Questions(QuestionsBase, table=True):
    __tablename__ = "Questions"

    question_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    placeholders: List["Placeholders"] = Relationship(back_populates="question")


# ===== Placeholders =====
class PlaceholdersBase(SQLModel):
    placeholder_order: int
    name: str = Field(max_length=100)
    data_type: str = Field(max_length=50)
    default_value: Optional[str] = Field(default=None, max_length=255)
    fk_question_id: int = Field(foreign_key="Questions.question_id")


class Placeholders(PlaceholdersBase, table=True):
    __tablename__ = "Placeholders"

    placeholder_id: Optional[int] = Field(default=None, primary_key=True)
    question: Questions = Relationship(back_populates="placeholders")


# ===== Item =====
class ItemBase(SQLModel):
    license: License
    status: Status
    fragestellung: str
    solution: str
    fragenart: Optional[Themenbereich] = None #TODO Ausführung prüfen
    question_type: QuestionTypes
    item_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    tags_id: Optional[int] = None
    created_at: datetime
    author_id: UUID = Field(foreign_key="Author.author_id")
    database_id: Optional[int] = Field(default=None, foreign_key="database.database_id")


class Item(ItemBase, table=True):
    __tablename__ = "Item"

    item_id: Optional[int] = Field(default=None, primary_key=True)
    author: Creator = Relationship(back_populates="items")
    database: Optional[Database] = Relationship(back_populates="items")
